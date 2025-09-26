from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import uuid
from datetime import datetime
import threading
import time
import numpy as np
from main import (
    fetch_research_papers, AVLTree, RBTree, 
    fetch_semantic_scholar_papers, fetch_crossref_papers, fetch_arxiv_papers
)
from advanced_search import AdvancedSearchEngine, suggest_domain_queries
from analytics import PaperAnalytics
from paper_manager import PaperManager
from realtime import RealTimeManager
from recommendations import RecommendationEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'research_paper_explorer_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for user sessions and data
user_sessions = {}
cached_searches = {}
search_engine = AdvancedSearchEngine()
analytics_engine = PaperAnalytics()
paper_manager = PaperManager()
realtime_manager = None  # Will be initialized after socketio is created
recommendation_engine = RecommendationEngine(paper_manager)

@app.route('/')
def index():
    """Main page with search interface"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_papers():
    """API endpoint for searching papers"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        sources = data.get('sources', ['semantic_scholar', 'crossref', 'arxiv'])
        year_range = data.get('year_range', {'min': 1900, 'max': 2024})
        min_citations = data.get('min_citations', 0)
        
        # Check cache first
        cache_key = f"{query}_{'-'.join(sources)}_{year_range['min']}_{year_range['max']}_{min_citations}"
        if cache_key in cached_searches:
            return jsonify(cached_searches[cache_key])
        
        papers = []
        
        # Fetch from selected sources
        if 'semantic_scholar' in sources:
            papers.extend(fetch_semantic_scholar_papers(query))
        if 'crossref' in sources:
            papers.extend(fetch_crossref_papers(query))
        if 'arxiv' in sources:
            papers.extend(fetch_arxiv_papers(query))
        
        # Apply filters
        filtered_papers = []
        for paper in papers:
            year = paper.get('year')
            citations = paper.get('citation_count')
            
            # Filter by year
            if year != 'Year Not Available':
                try:
                    year_int = int(year)
                    if year_int < year_range['min'] or year_int > year_range['max']:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Filter by citations
            if citations != 'Citation Count Not Available':
                try:
                    citations_int = int(citations)
                    if citations_int < min_citations:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Add unique ID for frontend
            paper['id'] = str(uuid.uuid4())
            filtered_papers.append(paper)
        
        # Build trees for analysis
        avl_tree = AVLTree()
        rb_tree = RBTree()
        avl_root = None
        
        for paper in filtered_papers:
            title = paper['title']
            authors = paper['authors'].split(', ') if paper['authors'] != 'Authors Not Available' else []
            
            # Insert into AVL tree
            avl_root = avl_tree.insert(avl_root, title)
            
            # Insert into RB tree
            for author in authors:
                if author.strip():
                    rb_tree.insert(title, author.strip())
        
        # Get unique authors
        unique_authors = rb_tree.list_unique_authors()
        
        # Analyze data
        analysis = analyze_papers(filtered_papers)
        
        result = {
            'papers': filtered_papers,
            'total_count': len(filtered_papers),
            'unique_authors': unique_authors,
            'analysis': analysis,
            'search_query': query
        }
        
        # Cache result
        cached_searches[cache_key] = result
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/autocomplete', methods=['POST'])
def autocomplete():
    """API endpoint for title autocomplete"""
    try:
        data = request.get_json()
        prefix = data.get('prefix', '')
        
        # Get recent searches to build autocomplete tree
        all_titles = []
        search_history = [record['query'] for record in search_engine.search_history]
        
        for cached_result in cached_searches.values():
            for paper in cached_result.get('papers', []):
                all_titles.append(paper['title'])
        
        # Use advanced search engine for smart autocomplete
        suggestions = search_engine.smart_autocomplete(prefix, all_titles, search_history)
        
        return jsonify({'suggestions': suggestions[:10]})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/advanced', methods=['POST'])
def advanced_search():
    """API endpoint for advanced search with filters"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # Analyze query for intent and keywords
        query_analysis = search_engine.analyze_query(query)
        
        # Get basic search parameters
        sources = data.get('sources', ['semantic_scholar', 'crossref', 'arxiv'])
        year_range = data.get('year_range', {'min': 1900, 'max': 2024})
        min_citations = data.get('min_citations', 0)
        
        # Get advanced filters
        advanced_filters = data.get('advanced_filters', {})
        
        # Perform basic search first
        papers = []
        
        if 'semantic_scholar' in sources:
            papers.extend(fetch_semantic_scholar_papers(query))
        if 'crossref' in sources:
            papers.extend(fetch_crossref_papers(query))
        if 'arxiv' in sources:
            papers.extend(fetch_arxiv_papers(query))
        
        # Apply basic filters (year, citations)
        filtered_papers = []
        for paper in papers:
            year = paper.get('year')
            citations = paper.get('citation_count')
            
            # Filter by year
            if year != 'Year Not Available':
                try:
                    year_int = int(year)
                    if year_int < year_range['min'] or year_int > year_range['max']:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Filter by citations
            if citations != 'Citation Count Not Available':
                try:
                    citations_int = int(citations)
                    if citations_int < min_citations:
                        continue
                except (ValueError, TypeError):
                    pass
            
            paper['id'] = str(uuid.uuid4())
            filtered_papers.append(paper)
        
        # Apply advanced filters
        if advanced_filters:
            filtered_papers = search_engine.filter_papers_advanced(filtered_papers, advanced_filters)
        
        # Generate suggestions and insights
        related_queries = search_engine.suggest_related_queries(query, filtered_papers)
        insights = search_engine.generate_search_insights(filtered_papers)
        
        # Record search for analytics
        search_engine.record_search(query, len(filtered_papers))
        
        # Build trees for analysis
        avl_tree = AVLTree()
        rb_tree = RBTree()
        avl_root = None
        
        for paper in filtered_papers:
            title = paper['title']
            authors = paper['authors'].split(', ') if paper['authors'] != 'Authors Not Available' else []
            
            avl_root = avl_tree.insert(avl_root, title)
            for author in authors:
                if author.strip():
                    rb_tree.insert(title, author.strip())
        
        unique_authors = rb_tree.list_unique_authors()
        analysis = analyze_papers(filtered_papers)
        
        result = {
            'papers': filtered_papers,
            'total_count': len(filtered_papers),
            'unique_authors': unique_authors,
            'analysis': analysis,
            'search_query': query,
            'query_analysis': query_analysis,
            'related_queries': related_queries,
            'insights': insights
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/suggestions', methods=['POST'])
def search_suggestions():
    """Get search suggestions based on domain and topic"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        domain = data.get('domain', 'general')
        
        suggestions = suggest_domain_queries(topic, domain)
        trends = search_engine.get_search_trends()
        
        return jsonify({
            'suggestions': suggestions,
            'trends': trends,
            'popular_queries': list(trends['popular_queries'].keys())[:5]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/trends')
def search_trends():
    """Get current search trends and analytics"""
    try:
        trends = search_engine.get_search_trends()
        return jsonify(trends)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/comprehensive', methods=['POST'])
def comprehensive_analytics():
    """Get comprehensive analytics for a set of papers"""
    try:
        data = request.get_json()
        paper_ids = data.get('paper_ids', [])
        
        # Get papers from cache
        papers = []
        for cached_result in cached_searches.values():
            for paper in cached_result.get('papers', []):
                if not paper_ids or paper.get('id') in paper_ids:
                    papers.append(paper)
        
        if not papers:
            return jsonify({'error': 'No papers found'}), 404
        
        # Generate comprehensive insights
        insights = analytics_engine.generate_research_insights(papers)
        
        return jsonify({
            'insights': insights,
            'total_papers_analyzed': len(papers)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/collaboration')
def collaboration_network():
    """Get collaboration network data"""
    try:
        # Get all cached papers
        all_papers = []
        for cached_result in cached_searches.values():
            all_papers.extend(cached_result.get('papers', []))
        
        if not all_papers:
            return jsonify({'error': 'No papers available for analysis'}), 404
        
        # Build collaboration network
        analytics_engine.build_collaboration_network(all_papers)
        network_data = analytics_engine.export_network_data()
        metrics = analytics_engine.get_collaboration_metrics()
        
        return jsonify({
            'network': network_data,
            'metrics': metrics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/temporal')
def temporal_analysis():
    """Get temporal trend analysis"""
    try:
        # Get all cached papers
        all_papers = []
        for cached_result in cached_searches.values():
            all_papers.extend(cached_result.get('papers', []))
        
        if not all_papers:
            return jsonify({'error': 'No papers available for analysis'}), 404
        
        timeline = analytics_engine.analyze_temporal_trends(all_papers)
        
        return jsonify({
            'timeline': timeline,
            'total_papers': len(all_papers)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/topics')
def topic_analysis():
    """Get topic clustering analysis"""
    try:
        # Get all cached papers
        all_papers = []
        for cached_result in cached_searches.values():
            all_papers.extend(cached_result.get('papers', []))
        
        if not all_papers:
            return jsonify({'error': 'No papers available for analysis'}), 404
        
        clusters = analytics_engine.analyze_topic_clusters(all_papers)
        
        return jsonify({
            'clusters': clusters,
            'total_topics': len(clusters)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/impact')
def impact_analysis():
    """Get citation impact analysis"""
    try:
        # Get all cached papers
        all_papers = []
        for cached_result in cached_searches.values():
            all_papers.extend(cached_result.get('papers', []))
        
        if not all_papers:
            return jsonify({'error': 'No papers available for analysis'}), 404
        
        impact_metrics = analytics_engine.analyze_impact_metrics(all_papers)
        
        return jsonify(impact_metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes', methods=['GET', 'POST'])
def manage_notes():
    """Manage notes for papers"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            user_id = paper_manager.create_user()
            session['user_id'] = user_id
        
        if request.method == 'GET':
            paper_id = request.args.get('paper_id')
            notes = paper_manager.get_notes(user_id, paper_id)
            return jsonify({'notes': notes})
        
        else:  # POST
            data = request.get_json()
            paper_id = data.get('paper_id')
            content = data.get('content')
            tags = data.get('tags', [])
            
            note_id = paper_manager.add_note(user_id, paper_id, content, tags)
            return jsonify({'success': True, 'note_id': note_id})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<note_id>', methods=['PUT', 'DELETE'])
def update_note(note_id):
    """Update or delete a note"""
    try:
        if request.method == 'PUT':
            data = request.get_json()
            content = data.get('content')
            tags = data.get('tags', [])
            
            paper_manager.update_note(note_id, content, tags)
            return jsonify({'success': True})
        
        else:  # DELETE
            paper_manager.delete_note(note_id)
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections', methods=['GET', 'POST'])
def manage_collections():
    """Manage paper collections"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            user_id = paper_manager.create_user()
            session['user_id'] = user_id
        
        if request.method == 'GET':
            collections = paper_manager.get_user_collections(user_id)
            return jsonify({'collections': collections})
        
        else:  # POST
            data = request.get_json()
            name = data.get('name')
            description = data.get('description', '')
            is_public = data.get('is_public', False)
            
            collection_id = paper_manager.create_collection(user_id, name, description, is_public)
            return jsonify({'success': True, 'collection_id': collection_id})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections/<collection_id>/papers', methods=['POST', 'DELETE'])
def manage_collection_papers(collection_id):
    """Add or remove papers from collection"""
    try:
        data = request.get_json()
        paper_id = data.get('paper_id')
        
        if request.method == 'POST':
            paper_manager.add_paper_to_collection(collection_id, paper_id)
            return jsonify({'success': True})
        
        else:  # DELETE - would need implementation in PaperManager
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reading-progress', methods=['POST'])
def update_reading_progress():
    """Update reading progress for a paper"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            user_id = paper_manager.create_user()
            session['user_id'] = user_id
        
        data = request.get_json()
        paper_id = data.get('paper_id')
        status = data.get('status')  # 'unread', 'reading', 'read', 'reviewed'
        progress = data.get('progress', 0)
        reading_time = data.get('reading_time', 0)
        
        paper_manager.update_reading_progress(user_id, paper_id, status, progress, reading_time)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reading-stats')
def get_reading_stats():
    """Get reading statistics for user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        stats = paper_manager.get_reading_stats(user_id)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_user_data():
    """Export user data in various formats"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        format_type = data.get('format', 'json')  # 'json', 'bibtex'
        
        exported_data = paper_manager.export_user_data(user_id, format_type)
        
        return jsonify({
            'success': True,
            'data': exported_data,
            'format': format_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications')
def get_notifications():
    """Get user notifications"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        if realtime_manager:
            notifications = realtime_manager.get_user_notifications(user_id, unread_only)
            return jsonify({'notifications': notifications})
        
        return jsonify({'notifications': []})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/realtime/stats')
def get_realtime_stats():
    """Get real-time application statistics"""
    try:
        if realtime_manager:
            stats = {
                'active_users': len(realtime_manager.active_users),
                'active_searches': len(realtime_manager.search_rooms),
                'trending_topics': realtime_manager.trending_topics,
                'timestamp': datetime.now().isoformat()
            }
            return jsonify(stats)
        
        return jsonify({'error': 'Real-time features not available'}), 503
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations')
def get_recommendations():
    """Get personalized paper recommendations"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all cached papers for recommendations
        all_papers = []
        for cached_result in cached_searches.values():
            all_papers.extend(cached_result.get('papers', []))
        
        if not all_papers:
            return jsonify({'recommendations': []})
        
        # Get personalized recommendations
        recommendations = recommendation_engine.get_diversified_recommendations(
            user_id, all_papers, 10
        )
        
        return jsonify({'recommendations': recommendations})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/trending')
def get_trending_recommendations():
    """Get trending papers"""
    try:
        # Get all cached papers
        all_papers = []
        for cached_result in cached_searches.values():
            all_papers.extend(cached_result.get('papers', []))
        
        if not all_papers:
            return jsonify({'trending': []})
        
        trending = recommendation_engine.get_trending_papers(all_papers)
        
        return jsonify({'trending': trending})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/similar/<paper_id>')
def get_similar_papers(paper_id):
    """Get papers similar to a specific paper"""
    try:
        # Find the target paper
        target_paper = None
        all_papers = []
        
        for cached_result in cached_searches.values():
            for paper in cached_result.get('papers', []):
                all_papers.append(paper)
                if paper.get('id') == paper_id:
                    target_paper = paper
        
        if not target_paper:
            return jsonify({'error': 'Paper not found'}), 404
        
        # Build features if not already done
        if not recommendation_engine.paper_vectors:
            recommendation_engine.build_paper_features(all_papers)
        
        # Find similar papers using content similarity
        similar_papers = []
        
        if paper_id in recommendation_engine.paper_features:
            target_idx = recommendation_engine.paper_features[paper_id]['vector_index']
            similarities = recommendation_engine.similarity_matrix[target_idx]
            
            # Get top similar papers (excluding the target paper itself)
            similar_indices = np.argsort(similarities)[::-1][1:11]  # Top 10, excluding self
            
            for idx in similar_indices:
                # Find paper by vector index
                for pid, features in recommendation_engine.paper_features.items():
                    if features['vector_index'] == idx:
                        similar_papers.append({
                            'paper': features['paper_data'],
                            'similarity_score': similarities[idx],
                            'reason': f'Similar content (similarity: {similarities[idx]:.2f})'
                        })
                        break
        
        return jsonify({'similar_papers': similar_papers})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/update', methods=['POST'])
def update_recommendations():
    """Update recommendation models with new data"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all papers for model update
        all_papers = []
        for cached_result in cached_searches.values():
            all_papers.extend(cached_result.get('papers', []))
        
        if all_papers:
            # Update recommendation cache
            recommendations = recommendation_engine.update_recommendations_cache(user_id, all_papers)
            return jsonify({
                'success': True,
                'updated_recommendations': len(recommendations)
            })
        
        return jsonify({'success': True, 'updated_recommendations': 0})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper/<paper_id>')
def get_paper_details(paper_id):
    """Get detailed information about a specific paper"""
    try:
        # Search through cached results
        for cached_result in cached_searches.values():
            for paper in cached_result.get('papers', []):
                if paper.get('id') == paper_id:
                    return jsonify(paper)
        
        return jsonify({'error': 'Paper not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookmark', methods=['POST'])
def bookmark_paper():
    """Bookmark a paper for later reading"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            user_id = paper_manager.create_user()
            session['user_id'] = user_id
        
        paper_id = data.get('paper_id')
        action = data.get('action', 'add')
        
        # Find and save the paper first
        paper = None
        for cached_result in cached_searches.values():
            for p in cached_result.get('papers', []):
                if p.get('id') == paper_id:
                    paper = p
                    break
            if paper:
                break
        
        if paper:
            paper_manager.save_paper(paper)
            
            if action == 'add':
                paper_manager.add_to_bookmark(user_id, paper_id)
            else:
                paper_manager.remove_from_bookmark(user_id, paper_id)
        
        # Get updated bookmarks
        bookmarks = paper_manager.get_user_papers(user_id, 'bookmark')
        bookmark_ids = [b['id'] for b in bookmarks]
        
        return jsonify({'success': True, 'bookmarks': bookmark_ids})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reading-list', methods=['GET', 'POST'])
def manage_reading_list():
    """Manage user's reading list"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            user_id = paper_manager.create_user()
            session['user_id'] = user_id
        
        if request.method == 'GET':
            reading_list = paper_manager.get_user_papers(user_id, 'reading_list')
            return jsonify({'reading_list': reading_list})
        
        else:  # POST
            data = request.get_json()
            paper_id = data.get('paper_id')
            action = data.get('action', 'add')
            
            # Find and save the paper first
            paper = None
            for cached_result in cached_searches.values():
                for p in cached_result.get('papers', []):
                    if p.get('id') == paper_id:
                        paper = p
                        break
                if paper:
                    break
            
            if paper:
                paper_manager.save_paper(paper)
                
                if action == 'add':
                    paper_manager.add_to_reading_list(user_id, paper_id)
                else:
                    paper_manager.remove_from_reading_list(user_id, paper_id)
            
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_papers(papers):
    """Analyze papers for trends and insights"""
    analysis = {
        'year_distribution': {},
        'source_distribution': {},
        'top_authors': {},
        'citation_stats': {
            'total': 0,
            'average': 0,
            'max': 0,
            'min': float('inf')
        }
    }
    
    total_citations = 0
    citation_count = 0
    
    for paper in papers:
        # Year distribution
        year = paper.get('year')
        if year != 'Year Not Available':
            try:
                year_int = int(year)
                analysis['year_distribution'][year_int] = analysis['year_distribution'].get(year_int, 0) + 1
            except (ValueError, TypeError):
                pass
        
        # Source distribution
        source = paper.get('source', 'Unknown')
        analysis['source_distribution'][source] = analysis['source_distribution'].get(source, 0) + 1
        
        # Author frequency
        authors = paper.get('authors', '').split(', ')
        for author in authors:
            if author and author != 'Authors Not Available':
                analysis['top_authors'][author] = analysis['top_authors'].get(author, 0) + 1
        
        # Citation statistics
        citations = paper.get('citation_count')
        if citations != 'Citation Count Not Available':
            try:
                citations_int = int(citations)
                total_citations += citations_int
                citation_count += 1
                analysis['citation_stats']['max'] = max(analysis['citation_stats']['max'], citations_int)
                analysis['citation_stats']['min'] = min(analysis['citation_stats']['min'], citations_int)
            except (ValueError, TypeError):
                pass
    
    # Calculate averages
    if citation_count > 0:
        analysis['citation_stats']['total'] = total_citations
        analysis['citation_stats']['average'] = total_citations / citation_count
    else:
        analysis['citation_stats']['min'] = 0
    
    # Sort top authors
    analysis['top_authors'] = dict(sorted(analysis['top_authors'].items(), 
                                        key=lambda x: x[1], reverse=True)[:10])
    
    return analysis

# WebSocket events for real-time features
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = paper_manager.create_user()
        session['user_id'] = user_id
    
    # Handle connection with real-time manager
    if realtime_manager:
        realtime_manager.handle_user_connect(user_id, request.sid)
    
    emit('connected', {
        'user_id': user_id,
        'session_id': request.sid
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = session.get('user_id')
    if user_id and realtime_manager:
        realtime_manager.handle_user_disconnect(user_id)

@socketio.on('join_search')
def handle_join_search(data):
    """Join a search room for collaborative features"""
    user_id = session.get('user_id')
    query = data.get('search_query', 'general')
    
    if realtime_manager:
        room_name = realtime_manager.join_search_room(user_id, query, request.sid)
        join_room(room_name)
        emit('joined_search', {'room': room_name, 'query': query})

@socketio.on('leave_search')
def handle_leave_search(data):
    """Leave a search room"""
    user_id = session.get('user_id')
    room_name = data.get('room_name')
    
    if realtime_manager and room_name:
        realtime_manager.leave_search_room(user_id, room_name)
        leave_room(room_name)

@socketio.on('mark_notification_read')
def handle_mark_notification_read(data):
    """Mark notification as read"""
    user_id = session.get('user_id')
    notification_id = data.get('notification_id')
    
    if realtime_manager and user_id and notification_id:
        realtime_manager.mark_notification_read(user_id, notification_id)
        emit('notification_marked_read', {'notification_id': notification_id})

@socketio.on('request_recommendations')
def handle_request_recommendations():
    """Request personalized recommendations"""
    user_id = session.get('user_id')
    
    if realtime_manager and user_id:
        recommendations = realtime_manager.get_user_recommendations(user_id)
        emit('recommendations', {'recommendations': recommendations})

@socketio.on('share_paper')
def handle_share_paper(data):
    """Share a paper with other users in the same search room"""
    user_id = session.get('user_id')
    paper_id = data.get('paper_id')
    room_name = data.get('room_name')
    message = data.get('message', '')
    
    if room_name:
        emit('paper_shared', {
            'user_id': user_id,
            'paper_id': paper_id,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }, room=room_name)

@socketio.on('typing_search')
def handle_typing_search(data):
    """Handle real-time search typing for collaboration"""
    user_id = session.get('user_id')
    room_name = data.get('room_name')
    query = data.get('query')
    
    if room_name:
        emit('user_typing', {
            'user_id': user_id,
            'query': query
        }, room=room_name, include_self=False)

if __name__ == '__main__':
    # Initialize real-time manager
    realtime_manager = RealTimeManager(socketio, search_engine, paper_manager)
    
    # Run the application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
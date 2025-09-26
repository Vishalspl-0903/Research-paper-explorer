# Data Visualization and Analytics Module
import json
import networkx as nx
from collections import defaultdict, Counter
import numpy as np
from datetime import datetime, timedelta

class PaperAnalytics:
    def __init__(self):
        self.collaboration_graph = nx.Graph()
        self.citation_network = nx.DiGraph()
        self.topic_clusters = {}
    
    def build_collaboration_network(self, papers):
        """Build author collaboration network"""
        self.collaboration_graph.clear()
        
        for paper in papers:
            authors = paper.get('authors', '').split(', ')
            authors = [a.strip() for a in authors if a.strip() and a != 'Authors Not Available']
            
            # Add authors as nodes
            for author in authors:
                if not self.collaboration_graph.has_node(author):
                    self.collaboration_graph.add_node(author, papers=0, total_citations=0)
                
                # Update author metrics
                self.collaboration_graph.nodes[author]['papers'] += 1
                citations = self._safe_int(paper.get('citation_count', 0))
                self.collaboration_graph.nodes[author]['total_citations'] += citations
            
            # Add collaboration edges
            for i, author1 in enumerate(authors):
                for author2 in authors[i+1:]:
                    if self.collaboration_graph.has_edge(author1, author2):
                        self.collaboration_graph[author1][author2]['weight'] += 1
                        self.collaboration_graph[author1][author2]['papers'].append(paper['title'])
                    else:
                        self.collaboration_graph.add_edge(
                            author1, author2, 
                            weight=1, 
                            papers=[paper['title']]
                        )
        
        return self.collaboration_graph
    
    def get_collaboration_metrics(self):
        """Calculate collaboration network metrics"""
        if not self.collaboration_graph.nodes():
            return {}
        
        metrics = {
            'total_authors': self.collaboration_graph.number_of_nodes(),
            'total_collaborations': self.collaboration_graph.number_of_edges(),
            'density': nx.density(self.collaboration_graph),
            'average_collaborators': sum(dict(self.collaboration_graph.degree()).values()) / self.collaboration_graph.number_of_nodes(),
            'most_prolific_authors': [],
            'strongest_collaborations': [],
            'isolated_authors': [],
            'collaboration_clusters': []
        }
        
        # Most prolific authors
        author_papers = [(author, data['papers']) for author, data in self.collaboration_graph.nodes(data=True)]
        metrics['most_prolific_authors'] = sorted(author_papers, key=lambda x: x[1], reverse=True)[:10]
        
        # Strongest collaborations
        collaborations = [(u, v, data['weight']) for u, v, data in self.collaboration_graph.edges(data=True)]
        metrics['strongest_collaborations'] = sorted(collaborations, key=lambda x: x[2], reverse=True)[:10]
        
        # Isolated authors (no collaborations)
        metrics['isolated_authors'] = [author for author, degree in self.collaboration_graph.degree() if degree == 0]
        
        # Find collaboration clusters
        try:
            components = list(nx.connected_components(self.collaboration_graph))
            metrics['collaboration_clusters'] = [
                {'size': len(component), 'authors': list(component)[:5]}  # Show first 5 authors
                for component in sorted(components, key=len, reverse=True)[:5]
            ]
        except:
            metrics['collaboration_clusters'] = []
        
        return metrics
    
    def analyze_temporal_trends(self, papers):
        """Analyze publication and citation trends over time"""
        year_data = defaultdict(lambda: {'papers': 0, 'citations': 0, 'authors': set()})
        
        for paper in papers:
            year = paper.get('year')
            if year != 'Year Not Available':
                try:
                    year_int = int(year)
                    year_data[year_int]['papers'] += 1
                    year_data[year_int]['citations'] += self._safe_int(paper.get('citation_count', 0))
                    
                    authors = paper.get('authors', '').split(', ')
                    for author in authors:
                        if author.strip() and author != 'Authors Not Available':
                            year_data[year_int]['authors'].add(author.strip())
                except (ValueError, TypeError):
                    continue
        
        # Convert to timeline format
        timeline = []
        for year in sorted(year_data.keys()):
            data = year_data[year]
            timeline.append({
                'year': year,
                'papers': data['papers'],
                'citations': data['citations'],
                'authors': len(data['authors']),
                'avg_citations': data['citations'] / data['papers'] if data['papers'] > 0 else 0
            })
        
        return timeline
    
    def analyze_topic_clusters(self, papers):
        """Cluster papers by topic using keyword analysis"""
        from collections import Counter
        import re
        
        # Extract keywords from titles
        all_keywords = []
        paper_keywords = {}
        
        for paper in papers:
            title = paper.get('title', '').lower()
            # Simple keyword extraction (can be enhanced with NLP)
            keywords = re.findall(r'\b\w{4,}\b', title)
            keywords = [k for k in keywords if k not in ['paper', 'study', 'analysis', 'research', 'using', 'based']]
            
            paper_keywords[paper['id']] = keywords
            all_keywords.extend(keywords)
        
        # Find most common keywords
        keyword_freq = Counter(all_keywords)
        top_keywords = [kw for kw, freq in keyword_freq.most_common(20) if freq > 1]
        
        # Cluster papers by shared keywords
        clusters = defaultdict(list)
        for paper in papers:
            paper_kws = paper_keywords.get(paper['id'], [])
            
            # Find the most frequent keyword in this paper
            main_topic = None
            max_freq = 0
            for kw in paper_kws:
                if kw in top_keywords and keyword_freq[kw] > max_freq:
                    max_freq = keyword_freq[kw]
                    main_topic = kw
            
            if main_topic:
                clusters[main_topic].append({
                    'id': paper['id'],
                    'title': paper['title'],
                    'citations': self._safe_int(paper.get('citation_count', 0)),
                    'year': paper.get('year')
                })
            else:
                clusters['other'].append({
                    'id': paper['id'],
                    'title': paper['title'],
                    'citations': self._safe_int(paper.get('citation_count', 0)),
                    'year': paper.get('year')
                })
        
        # Sort clusters by size and papers by citations
        sorted_clusters = {}
        for topic, papers_list in clusters.items():
            sorted_papers = sorted(papers_list, key=lambda x: x['citations'], reverse=True)
            sorted_clusters[topic] = {
                'papers': sorted_papers,
                'count': len(sorted_papers),
                'total_citations': sum(p['citations'] for p in sorted_papers)
            }
        
        return dict(sorted(sorted_clusters.items(), key=lambda x: x[1]['count'], reverse=True))
    
    def analyze_impact_metrics(self, papers):
        """Calculate various impact metrics"""
        citations = [self._safe_int(paper.get('citation_count', 0)) for paper in papers]
        citations = [c for c in citations if c > 0]  # Remove zero citations
        
        if not citations:
            return {}
        
        citations_np = np.array(citations)
        
        metrics = {
            'total_papers': len(papers),
            'total_citations': sum(citations),
            'average_citations': np.mean(citations_np),
            'median_citations': np.median(citations_np),
            'std_citations': np.std(citations_np),
            'max_citations': np.max(citations_np),
            'min_citations': np.min(citations_np),
            'h_index': self._calculate_h_index(citations),
            'citation_percentiles': {
                '90th': np.percentile(citations_np, 90),
                '75th': np.percentile(citations_np, 75),
                '50th': np.percentile(citations_np, 50),
                '25th': np.percentile(citations_np, 25)
            },
            'highly_cited_papers': [],
            'impact_distribution': {}
        }
        
        # Highly cited papers (top 10% by citations)
        citation_threshold = np.percentile(citations_np, 90)
        highly_cited = [
            paper for paper in papers 
            if self._safe_int(paper.get('citation_count', 0)) >= citation_threshold
        ]
        metrics['highly_cited_papers'] = sorted(
            highly_cited, 
            key=lambda x: self._safe_int(x.get('citation_count', 0)), 
            reverse=True
        )[:10]
        
        # Impact distribution
        impact_ranges = [
            (0, 10, 'Low Impact'),
            (10, 50, 'Medium Impact'),
            (50, 100, 'High Impact'),
            (100, float('inf'), 'Very High Impact')
        ]
        
        for min_cit, max_cit, category in impact_ranges:
            count = sum(1 for c in citations if min_cit <= c < max_cit)
            metrics['impact_distribution'][category] = count
        
        return metrics
    
    def generate_research_insights(self, papers):
        """Generate comprehensive research insights"""
        insights = {
            'collaboration_analysis': {},
            'temporal_trends': [],
            'topic_clusters': {},
            'impact_metrics': {},
            'research_gaps': [],
            'emerging_trends': []
        }
        
        try:
            # Build collaboration network
            self.build_collaboration_network(papers)
            insights['collaboration_analysis'] = self.get_collaboration_metrics()
            
            # Temporal analysis
            insights['temporal_trends'] = self.analyze_temporal_trends(papers)
            
            # Topic clustering
            insights['topic_clusters'] = self.analyze_topic_clusters(papers)
            
            # Impact analysis
            insights['impact_metrics'] = self.analyze_impact_metrics(papers)
            
            # Identify research gaps (topics with few recent papers)
            insights['research_gaps'] = self._identify_research_gaps(papers)
            
            # Emerging trends (topics gaining momentum)
            insights['emerging_trends'] = self._identify_emerging_trends(papers)
            
        except Exception as e:
            print(f"Error generating insights: {e}")
        
        return insights
    
    def _identify_research_gaps(self, papers):
        """Identify potential research gaps"""
        # Simple implementation: topics with few papers in recent years
        recent_year = datetime.now().year - 2
        recent_papers = [p for p in papers if self._safe_int(p.get('year', 0)) >= recent_year]
        
        if len(recent_papers) < len(papers) * 0.3:  # Less than 30% are recent
            return ["Limited recent research in this area - potential gap"]
        
        return []
    
    def _identify_emerging_trends(self, papers):
        """Identify emerging research trends"""
        # Simple implementation: compare recent vs older papers
        current_year = datetime.now().year
        recent_papers = [p for p in papers if self._safe_int(p.get('year', 0)) >= current_year - 3]
        older_papers = [p for p in papers if self._safe_int(p.get('year', 0)) < current_year - 3]
        
        if len(recent_papers) > len(older_papers):
            return ["Increasing research activity in recent years"]
        
        return []
    
    def _calculate_h_index(self, citations):
        """Calculate h-index for the paper set"""
        citations_sorted = sorted(citations, reverse=True)
        h_index = 0
        
        for i, citation_count in enumerate(citations_sorted):
            if citation_count >= i + 1:
                h_index = i + 1
            else:
                break
        
        return h_index
    
    def _safe_int(self, value):
        """Safely convert value to integer"""
        if value == 'Citation Count Not Available' or value == 'Year Not Available':
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    def export_network_data(self, format='json'):
        """Export collaboration network for visualization"""
        if format == 'json':
            nodes = []
            edges = []
            
            for node, data in self.collaboration_graph.nodes(data=True):
                nodes.append({
                    'id': node,
                    'label': node,
                    'papers': data.get('papers', 0),
                    'citations': data.get('total_citations', 0),
                    'size': min(data.get('papers', 0) * 3 + 10, 50)  # Scale node size
                })
            
            for u, v, data in self.collaboration_graph.edges(data=True):
                edges.append({
                    'source': u,
                    'target': v,
                    'weight': data.get('weight', 1),
                    'papers': data.get('papers', [])
                })
            
            return {'nodes': nodes, 'edges': edges}
        
        return None
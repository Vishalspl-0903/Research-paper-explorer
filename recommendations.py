# Machine Learning Recommendation System
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
import networkx as nx
from collections import defaultdict, Counter
import re
import json
from datetime import datetime, timedelta

class RecommendationEngine:
    def __init__(self, paper_manager):
        self.paper_manager = paper_manager
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8
        )
        self.paper_vectors = None
        self.paper_features = {}
        self.user_profiles = {}
        self.similarity_matrix = None
        self.trending_papers = []
        
    def build_paper_features(self, papers):
        """Build feature vectors for papers using TF-IDF"""
        # Combine title, authors, and keywords for feature extraction
        documents = []
        paper_ids = []
        
        for paper in papers:
            text_features = []
            
            # Add title
            if paper.get('title'):
                text_features.append(paper['title'])
            
            # Add authors
            if paper.get('authors') and paper['authors'] != 'Authors Not Available':
                authors = paper['authors'].replace(',', ' ')
                text_features.append(authors)
            
            # Add keywords (if available)
            if paper.get('keywords'):
                text_features.append(paper['keywords'])
            
            # Add year as context
            if paper.get('year') and paper['year'] != 'Year Not Available':
                text_features.append(f"year_{paper['year']}")
            
            # Add source
            if paper.get('source'):
                text_features.append(f"source_{paper['source'].lower()}")
            
            combined_text = ' '.join(text_features)
            documents.append(combined_text)
            paper_ids.append(paper['id'])
        
        if documents:
            # Fit TF-IDF vectorizer
            self.paper_vectors = self.tfidf_vectorizer.fit_transform(documents)
            
            # Store paper features
            for i, paper_id in enumerate(paper_ids):
                self.paper_features[paper_id] = {
                    'vector_index': i,
                    'paper_data': papers[i]
                }
            
            # Compute similarity matrix
            self.similarity_matrix = cosine_similarity(self.paper_vectors)
            
        return self.paper_vectors
    
    def build_user_profile(self, user_id):
        """Build user profile based on their interactions"""
        profile = {
            'preferred_topics': Counter(),
            'preferred_authors': Counter(),
            'preferred_years': Counter(),
            'preferred_sources': Counter(),
            'avg_citations': 0,
            'reading_patterns': {},
            'interaction_weights': {
                'bookmark': 1.0,
                'reading_list': 0.8,
                'read': 1.2,
                'favorite': 1.5
            }
        }
        
        # Get user interactions
        all_interactions = []
        for interaction_type in ['bookmark', 'reading_list']:
            papers = self.paper_manager.get_user_papers(user_id, interaction_type)
            for paper in papers:
                paper['interaction_type'] = interaction_type
                all_interactions.append(paper)
        
        if not all_interactions:
            return profile
        
        # Extract preferences
        citation_counts = []
        
        for paper in all_interactions:
            weight = profile['interaction_weights'].get(paper['interaction_type'], 1.0)
            
            # Topic preferences (from title keywords)
            if paper.get('title'):
                keywords = self._extract_keywords(paper['title'])
                for keyword in keywords:
                    profile['preferred_topics'][keyword] += weight
            
            # Author preferences
            if paper.get('authors') and paper['authors'] != 'Authors Not Available':
                authors = [a.strip() for a in paper['authors'].split(',')]
                for author in authors:
                    profile['preferred_authors'][author] += weight
            
            # Year preferences
            if paper.get('year') and paper['year'] != 'Year Not Available':
                try:
                    year_int = int(paper['year'])
                    profile['preferred_years'][year_int] += weight
                except (ValueError, TypeError):
                    pass
            
            # Source preferences
            if paper.get('source'):
                profile['preferred_sources'][paper['source']] += weight
            
            # Citation preferences
            if paper.get('citation_count') and paper['citation_count'] != 'Citation Count Not Available':
                try:
                    citations = int(paper['citation_count'])
                    citation_counts.append(citations * weight)
                except (ValueError, TypeError):
                    pass
        
        # Calculate average citation preference
        if citation_counts:
            profile['avg_citations'] = sum(citation_counts) / len(citation_counts)
        
        # Get reading stats
        profile['reading_patterns'] = self.paper_manager.get_reading_stats(user_id)
        
        self.user_profiles[user_id] = profile
        return profile
    
    def get_content_based_recommendations(self, user_id, candidate_papers, num_recommendations=10):
        """Get recommendations based on content similarity"""
        if not self.paper_vectors or not candidate_papers:
            return []
        
        user_profile = self.user_profiles.get(user_id)
        if not user_profile:
            user_profile = self.build_user_profile(user_id)
        
        # Get user's interacted papers
        user_papers = []
        for interaction_type in ['bookmark', 'reading_list']:
            papers = self.paper_manager.get_user_papers(user_id, interaction_type)
            user_papers.extend([p['id'] for p in papers])
        
        if not user_papers:
            return self._get_trending_recommendations(candidate_papers, num_recommendations)
        
        # Calculate recommendations
        recommendations = []
        
        for candidate in candidate_papers:
            if candidate['id'] in user_papers:
                continue  # Skip already interacted papers
            
            # Content similarity score
            content_score = self._calculate_content_similarity(candidate, user_profile)
            
            # Popularity score (based on citations)
            popularity_score = self._calculate_popularity_score(candidate)
            
            # Recency score
            recency_score = self._calculate_recency_score(candidate)
            
            # Combined score
            total_score = (
                content_score * 0.6 +
                popularity_score * 0.3 +
                recency_score * 0.1
            )
            
            recommendations.append({
                'paper': candidate,
                'score': total_score,
                'content_score': content_score,
                'popularity_score': popularity_score,
                'recency_score': recency_score,
                'reason': self._generate_recommendation_reason(candidate, user_profile)
            })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def get_collaborative_recommendations(self, user_id, all_users_data, num_recommendations=10):
        """Get recommendations based on collaborative filtering"""
        # Find similar users
        similar_users = self._find_similar_users(user_id, all_users_data)
        
        if not similar_users:
            return []
        
        # Get papers liked by similar users
        recommended_papers = defaultdict(float)
        user_papers = set()
        
        # Get current user's papers
        for interaction_type in ['bookmark', 'reading_list']:
            papers = self.paper_manager.get_user_papers(user_id, interaction_type)
            user_papers.update([p['id'] for p in papers])
        
        # Aggregate recommendations from similar users
        for similar_user_id, similarity_score in similar_users:
            for interaction_type in ['bookmark', 'reading_list']:
                papers = self.paper_manager.get_user_papers(similar_user_id, interaction_type)
                
                for paper in papers:
                    if paper['id'] not in user_papers:
                        weight = similarity_score
                        if interaction_type == 'reading_list':
                            weight *= 0.8  # Reading list has lower weight than bookmarks
                        
                        recommended_papers[paper['id']] += weight
        
        # Sort and format recommendations
        recommendations = []
        for paper_id, score in sorted(recommended_papers.items(), key=lambda x: x[1], reverse=True):
            # Get paper data (this would need to be retrieved from storage)
            recommendations.append({
                'paper_id': paper_id,
                'score': score,
                'reason': 'Recommended based on users with similar interests'
            })
        
        return recommendations[:num_recommendations]
    
    def get_trending_papers(self, papers, time_window_days=30):
        """Identify trending papers based on recent activity"""
        trending_papers = []
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        
        for paper in papers:
            # Simple trending calculation based on citations and recency
            year = paper.get('year')
            citations = self._safe_int(paper.get('citation_count', 0))
            
            trending_score = 0
            
            # Recent papers get bonus
            if year and year != 'Year Not Available':
                try:
                    paper_year = int(year)
                    if paper_year >= cutoff_date.year:
                        trending_score += 10
                    elif paper_year >= cutoff_date.year - 1:
                        trending_score += 5
                except (ValueError, TypeError):
                    pass
            
            # High citation papers get bonus
            if citations > 0:
                if citations > 100:
                    trending_score += 15
                elif citations > 50:
                    trending_score += 10
                elif citations > 20:
                    trending_score += 5
            
            # Source diversity bonus
            source = paper.get('source', '')
            if source in ['arXiv', 'Semantic Scholar']:
                trending_score += 2
            
            if trending_score > 5:  # Threshold for trending
                trending_papers.append({
                    'paper': paper,
                    'trending_score': trending_score
                })
        
        # Sort by trending score
        trending_papers.sort(key=lambda x: x['trending_score'], reverse=True)
        self.trending_papers = trending_papers[:20]  # Keep top 20
        
        return self.trending_papers
    
    def get_diversified_recommendations(self, user_id, candidate_papers, num_recommendations=10):
        """Get diverse recommendations to avoid filter bubbles"""
        content_recs = self.get_content_based_recommendations(
            user_id, candidate_papers, num_recommendations * 2
        )
        
        if not content_recs:
            return []
        
        # Diversify by topic/author/year
        diversified = []
        used_authors = set()
        used_topics = set()
        used_years = set()
        
        for rec in content_recs:
            paper = rec['paper']
            
            # Extract diversity features
            authors = set()
            if paper.get('authors') and paper['authors'] != 'Authors Not Available':
                authors = set(a.strip() for a in paper['authors'].split(','))
            
            topics = set(self._extract_keywords(paper.get('title', '')))
            year = paper.get('year')
            
            # Check diversity
            author_overlap = len(authors & used_authors) / max(len(authors), 1)
            topic_overlap = len(topics & used_topics) / max(len(topics), 1)
            
            # Accept if sufficiently diverse or high scoring
            if (author_overlap < 0.5 and topic_overlap < 0.5) or rec['score'] > 0.8:
                diversified.append(rec)
                used_authors.update(authors)
                used_topics.update(topics)
                if year:
                    used_years.add(year)
                
                if len(diversified) >= num_recommendations:
                    break
        
        return diversified
    
    def _calculate_content_similarity(self, paper, user_profile):
        """Calculate content similarity score"""
        score = 0.0
        
        # Topic similarity
        if paper.get('title'):
            paper_topics = self._extract_keywords(paper['title'])
            for topic in paper_topics:
                if topic in user_profile['preferred_topics']:
                    score += user_profile['preferred_topics'][topic] * 0.1
        
        # Author similarity
        if paper.get('authors') and paper['authors'] != 'Authors Not Available':
            paper_authors = [a.strip() for a in paper['authors'].split(',')]
            for author in paper_authors:
                if author in user_profile['preferred_authors']:
                    score += user_profile['preferred_authors'][author] * 0.15
        
        # Year similarity
        if paper.get('year') and paper['year'] != 'Year Not Available':
            try:
                paper_year = int(paper['year'])
                year_scores = []
                for pref_year, count in user_profile['preferred_years'].items():
                    year_diff = abs(paper_year - pref_year)
                    if year_diff <= 2:
                        year_scores.append(count * (3 - year_diff) * 0.05)
                if year_scores:
                    score += max(year_scores)
            except (ValueError, TypeError):
                pass
        
        # Source similarity
        if paper.get('source'):
            if paper['source'] in user_profile['preferred_sources']:
                score += user_profile['preferred_sources'][paper['source']] * 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_popularity_score(self, paper):
        """Calculate popularity score based on citations"""
        citations = self._safe_int(paper.get('citation_count', 0))
        
        if citations == 0:
            return 0.1
        elif citations < 10:
            return 0.3
        elif citations < 50:
            return 0.5
        elif citations < 100:
            return 0.7
        elif citations < 500:
            return 0.9
        else:
            return 1.0
    
    def _calculate_recency_score(self, paper):
        """Calculate recency score"""
        year = paper.get('year')
        if not year or year == 'Year Not Available':
            return 0.3
        
        try:
            paper_year = int(year)
            current_year = datetime.now().year
            year_diff = current_year - paper_year
            
            if year_diff <= 1:
                return 1.0
            elif year_diff <= 3:
                return 0.8
            elif year_diff <= 5:
                return 0.6
            elif year_diff <= 10:
                return 0.4
            else:
                return 0.2
        except (ValueError, TypeError):
            return 0.3
    
    def _generate_recommendation_reason(self, paper, user_profile):
        """Generate human-readable reason for recommendation"""
        reasons = []
        
        # Check topic match
        if paper.get('title'):
            paper_topics = self._extract_keywords(paper['title'])
            matching_topics = [t for t in paper_topics if t in user_profile['preferred_topics']]
            if matching_topics:
                reasons.append(f"Similar topics: {', '.join(matching_topics[:2])}")
        
        # Check author match
        if paper.get('authors') and paper['authors'] != 'Authors Not Available':
            paper_authors = [a.strip() for a in paper['authors'].split(',')]
            matching_authors = [a for a in paper_authors if a in user_profile['preferred_authors']]
            if matching_authors:
                reasons.append(f"Authors you follow: {', '.join(matching_authors[:2])}")
        
        # Check citation level
        citations = self._safe_int(paper.get('citation_count', 0))
        if citations > 100:
            reasons.append("Highly cited paper")
        elif citations > 50:
            reasons.append("Well-cited paper")
        
        # Check recency
        year = paper.get('year')
        if year and year != 'Year Not Available':
            try:
                paper_year = int(year)
                if datetime.now().year - paper_year <= 2:
                    reasons.append("Recent publication")
            except (ValueError, TypeError):
                pass
        
        return "; ".join(reasons) if reasons else "Matches your research interests"
    
    def _find_similar_users(self, user_id, all_users_data):
        """Find users with similar interests"""
        # This would implement user-based collaborative filtering
        # For now, return empty list as we'd need access to all user data
        return []
    
    def _get_trending_recommendations(self, papers, num_recommendations):
        """Get trending papers when no user profile exists"""
        trending = self.get_trending_papers(papers)
        return [{
            'paper': trend['paper'],
            'score': trend['trending_score'] / 20.0,  # Normalize
            'reason': 'Trending in your field'
        } for trend in trending[:num_recommendations]]
    
    def _extract_keywords(self, text):
        """Extract keywords from text"""
        if not text:
            return []
        
        # Simple keyword extraction
        words = re.findall(r'\b\w{4,}\b', text.lower())
        # Filter out common words
        stop_words = {'with', 'using', 'from', 'this', 'that', 'they', 'them', 'their', 'such', 'been', 'have'}
        keywords = [w for w in words if w not in stop_words]
        return keywords[:10]  # Return top 10 keywords
    
    def _safe_int(self, value):
        """Safely convert value to integer"""
        if value in ['Year Not Available', 'Citation Count Not Available', None]:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    def update_recommendations_cache(self, user_id, papers):
        """Update cached recommendations for a user"""
        # Build features if not already done
        if not self.paper_vectors:
            self.build_paper_features(papers)
        
        # Build user profile
        self.build_user_profile(user_id)
        
        # Generate recommendations
        recommendations = self.get_diversified_recommendations(user_id, papers)
        
        return recommendations
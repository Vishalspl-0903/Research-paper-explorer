# Background Worker for Research Paper Explorer
import os
import time
import redis
import json
from datetime import datetime, timedelta
from main import fetch_semantic_scholar_papers, fetch_crossref_papers, fetch_arxiv_papers
from paper_manager import PaperManager
from recommendations import RecommendationEngine

class BackgroundWorker:
    def __init__(self):
        self.redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        )
        self.paper_manager = PaperManager()
        self.recommendation_engine = RecommendationEngine(self.paper_manager)
        
    def run(self):
        """Main worker loop"""
        print("Starting background worker...")
        
        while True:
            try:
                # Process pending search requests
                self.process_search_queue()
                
                # Update recommendations
                self.update_recommendations()
                
                # Clean up old data
                self.cleanup_old_data()
                
                # Update trending topics
                self.update_trending_topics()
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                print(f"Worker error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def process_search_queue(self):
        """Process queued search requests"""
        try:
            # Get search requests from Redis queue
            while True:
                request = self.redis_client.blpop(['search_queue'], timeout=1)
                if not request:
                    break
                
                _, request_data = request
                search_data = json.loads(request_data)
                
                # Perform background search
                self.perform_background_search(search_data)
                
        except Exception as e:
            print(f"Error processing search queue: {e}")
    
    def perform_background_search(self, search_data):
        """Perform search in background"""
        try:
            query = search_data.get('query')
            sources = search_data.get('sources', ['semantic_scholar', 'crossref', 'arxiv'])
            user_id = search_data.get('user_id')
            
            papers = []
            
            # Fetch from different sources
            if 'semantic_scholar' in sources:
                papers.extend(fetch_semantic_scholar_papers(query))
            if 'crossref' in sources:
                papers.extend(fetch_crossref_papers(query))
            if 'arxiv' in sources:
                papers.extend(fetch_arxiv_papers(query))
            
            # Save papers to database
            for paper in papers:
                paper['id'] = f"{paper['source']}_{hash(paper['title'])}"
                self.paper_manager.save_paper(paper)
            
            # Cache results in Redis
            cache_key = f"search_results:{query}:{'-'.join(sources)}"
            self.redis_client.setex(
                cache_key, 
                3600,  # 1 hour TTL
                json.dumps({
                    'papers': papers,
                    'timestamp': datetime.now().isoformat(),
                    'query': query
                })
            )
            
            # Update user's search history
            if user_id:
                history_key = f"user_search_history:{user_id}"
                self.redis_client.lpush(history_key, json.dumps({
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'result_count': len(papers)
                }))
                self.redis_client.ltrim(history_key, 0, 99)  # Keep last 100 searches
            
            print(f"Background search completed for '{query}': {len(papers)} papers found")
            
        except Exception as e:
            print(f"Error in background search: {e}")
    
    def update_recommendations(self):
        """Update recommendation models"""
        try:
            # Get all active users (users who searched in last 24 hours)
            active_users = []
            
            # This would get users from database in a real implementation
            # For now, skip if no users
            
            for user_id in active_users:
                try:
                    # Get user's papers
                    user_papers = []
                    for interaction_type in ['bookmark', 'reading_list']:
                        papers = self.paper_manager.get_user_papers(user_id, interaction_type)
                        user_papers.extend(papers)
                    
                    if user_papers:
                        # Update recommendations
                        recommendations = self.recommendation_engine.update_recommendations_cache(
                            user_id, user_papers
                        )
                        
                        # Cache recommendations
                        rec_key = f"user_recommendations:{user_id}"
                        self.redis_client.setex(
                            rec_key,
                            3600,  # 1 hour TTL
                            json.dumps(recommendations)
                        )
                        
                except Exception as e:
                    print(f"Error updating recommendations for user {user_id}: {e}")
            
        except Exception as e:
            print(f"Error updating recommendations: {e}")
    
    def cleanup_old_data(self):
        """Clean up old cached data"""
        try:
            # Clean up old search results (older than 24 hours)
            cutoff = datetime.now() - timedelta(hours=24)
            
            # This would clean up database records in a real implementation
            # For now, just clean up Redis keys
            
            # Get all search result keys
            search_keys = self.redis_client.keys('search_results:*')
            
            for key in search_keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        result = json.loads(data)
                        timestamp = datetime.fromisoformat(result.get('timestamp', ''))
                        
                        if timestamp < cutoff:
                            self.redis_client.delete(key)
                            
                except Exception as e:
                    print(f"Error cleaning up key {key}: {e}")
            
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
    
    def update_trending_topics(self):
        """Update trending topics based on search patterns"""
        try:
            # Get search patterns from last 24 hours
            search_patterns = {}
            
            # Analyze user search history
            history_keys = self.redis_client.keys('user_search_history:*')
            
            for key in history_keys:
                try:
                    searches = self.redis_client.lrange(key, 0, -1)
                    
                    for search_data in searches:
                        search = json.loads(search_data)
                        timestamp = datetime.fromisoformat(search['timestamp'])
                        
                        # Only consider searches from last 24 hours
                        if datetime.now() - timestamp < timedelta(hours=24):
                            query = search['query'].lower()
                            search_patterns[query] = search_patterns.get(query, 0) + 1
                            
                except Exception as e:
                    print(f"Error analyzing search history {key}: {e}")
            
            # Sort by frequency and get top trending topics
            trending = sorted(search_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Cache trending topics
            self.redis_client.setex(
                'trending_topics',
                1800,  # 30 minutes TTL
                json.dumps({
                    'topics': [{'query': query, 'count': count} for query, count in trending],
                    'updated_at': datetime.now().isoformat()
                })
            )
            
            print(f"Updated trending topics: {len(trending)} topics")
            
        except Exception as e:
            print(f"Error updating trending topics: {e}")

if __name__ == '__main__':
    worker = BackgroundWorker()
    worker.run()
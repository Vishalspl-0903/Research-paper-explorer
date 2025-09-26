# Real-time Features Module
import asyncio
import json
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time

class RealTimeManager:
    def __init__(self, socketio, search_engine, paper_manager):
        self.socketio = socketio
        self.search_engine = search_engine
        self.paper_manager = paper_manager
        self.active_users = {}
        self.search_rooms = defaultdict(set)
        self.notifications = defaultdict(list)
        self.trending_topics = []
        self.alert_thresholds = {
            'new_papers': 5,  # Alert when 5+ new papers found
            'citation_spike': 50,  # Alert when paper gets 50+ new citations
            'collaboration': 3  # Alert when 3+ authors collaborate
        }
        
        # Start background tasks
        self.start_background_tasks()
    
    def start_background_tasks(self):
        """Start background tasks for real-time features"""
        # Monitor trending topics
        trending_thread = threading.Thread(target=self.monitor_trending_topics, daemon=True)
        trending_thread.start()
        
        # Send periodic updates
        update_thread = threading.Thread(target=self.send_periodic_updates, daemon=True)
        update_thread.start()
    
    def monitor_trending_topics(self):
        """Monitor and update trending topics"""
        while True:
            try:
                trends = self.search_engine.get_search_trends()
                popular_queries = list(trends['popular_queries'].keys())[:5]
                
                if popular_queries != self.trending_topics:
                    self.trending_topics = popular_queries
                    self.broadcast_trending_update()
                
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Error monitoring trends: {e}")
                time.sleep(60)
    
    def send_periodic_updates(self):
        """Send periodic updates to connected users"""
        while True:
            try:
                # Send daily reading stats reminder
                if datetime.now().hour == 9 and datetime.now().minute == 0:
                    self.send_daily_reminders()
                
                # Send weekly trend summary
                if datetime.now().weekday() == 0 and datetime.now().hour == 10:
                    self.send_weekly_summary()
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error sending updates: {e}")
                time.sleep(300)
    
    def broadcast_trending_update(self):
        """Broadcast trending topics update to all users"""
        self.socketio.emit('trending_update', {
            'trends': self.trending_topics,
            'timestamp': datetime.now().isoformat()
        })
    
    def send_daily_reminders(self):
        """Send daily reading reminders to users"""
        for user_id in self.active_users:
            try:
                stats = self.paper_manager.get_reading_stats(user_id)
                if stats.get('total_papers', 0) > 0:
                    unread_count = stats['total_papers'] - stats.get('papers_read', 0)
                    if unread_count > 0:
                        self.send_notification(user_id, {
                            'type': 'reminder',
                            'title': 'Daily Reading Reminder',
                            'message': f"You have {unread_count} unread papers in your reading list.",
                            'action_url': '/reading-list'
                        })
            except Exception as e:
                print(f"Error sending reminder to user {user_id}: {e}")
    
    def send_weekly_summary(self):
        """Send weekly summary to users"""
        for user_id in self.active_users:
            try:
                # Get user's reading activity for the week
                stats = self.paper_manager.get_reading_stats(user_id)
                
                summary = {
                    'type': 'weekly_summary',
                    'title': 'Your Weekly Research Summary',
                    'stats': stats,
                    'trending_topics': self.trending_topics,
                    'recommendations': self.get_user_recommendations(user_id)[:3]
                }
                
                self.send_notification(user_id, summary)
            except Exception as e:
                print(f"Error sending summary to user {user_id}: {e}")
    
    def send_notification(self, user_id, notification):
        """Send notification to specific user"""
        notification['id'] = f"notif_{int(time.time())}"
        notification['timestamp'] = datetime.now().isoformat()
        notification['read'] = False
        
        # Store notification
        self.notifications[user_id].append(notification)
        
        # Keep only last 50 notifications
        if len(self.notifications[user_id]) > 50:
            self.notifications[user_id] = self.notifications[user_id][-50:]
        
        # Send via WebSocket if user is connected
        if user_id in self.active_users:
            self.socketio.emit('notification', notification, room=self.active_users[user_id])
    
    def get_user_recommendations(self, user_id):
        """Get personalized recommendations for user"""
        try:
            # Get user's bookmarked papers
            bookmarks = self.paper_manager.get_user_papers(user_id, 'bookmark')
            
            if not bookmarks:
                return []
            
            # Simple recommendation based on similar papers
            # In a real system, this would use ML algorithms
            recommendations = []
            
            # Extract keywords from bookmarked papers
            user_keywords = set()
            for paper in bookmarks:
                title_words = paper['title'].lower().split()
                user_keywords.update([w for w in title_words if len(w) > 4])
            
            # Find papers with similar keywords (from cached searches)
            # This is a simplified approach
            similar_papers = []
            # Implementation would go here...
            
            return recommendations[:5]
        except Exception as e:
            print(f"Error getting recommendations for user {user_id}: {e}")
            return []
    
    def handle_user_connect(self, user_id, session_id):
        """Handle user connection"""
        self.active_users[user_id] = session_id
        
        # Send unread notifications
        unread_notifications = [n for n in self.notifications[user_id] if not n.get('read', False)]
        if unread_notifications:
            self.socketio.emit('notifications_batch', {
                'notifications': unread_notifications
            }, room=session_id)
        
        # Send current trending topics
        self.socketio.emit('trending_update', {
            'trends': self.trending_topics,
            'timestamp': datetime.now().isoformat()
        }, room=session_id)
    
    def handle_user_disconnect(self, user_id):
        """Handle user disconnection"""
        if user_id in self.active_users:
            del self.active_users[user_id]
    
    def join_search_room(self, user_id, query, session_id):
        """Handle user joining a search room"""
        room_name = f"search_{query.lower().replace(' ', '_')}"
        self.search_rooms[room_name].add(user_id)
        
        # Notify other users in the room
        self.socketio.emit('user_joined_search', {
            'user_count': len(self.search_rooms[room_name]),
            'query': query
        }, room=room_name)
        
        return room_name
    
    def leave_search_room(self, user_id, room_name):
        """Handle user leaving a search room"""
        if room_name in self.search_rooms:
            self.search_rooms[room_name].discard(user_id)
            
            # Clean up empty rooms
            if not self.search_rooms[room_name]:
                del self.search_rooms[room_name]
            else:
                # Notify remaining users
                self.socketio.emit('user_left_search', {
                    'user_count': len(self.search_rooms[room_name])
                }, room=room_name)
    
    def broadcast_new_papers(self, query, papers):
        """Broadcast new papers found for a query"""
        room_name = f"search_{query.lower().replace(' ', '_')}"
        
        if room_name in self.search_rooms and len(papers) >= self.alert_thresholds['new_papers']:
            self.socketio.emit('new_papers_found', {
                'query': query,
                'count': len(papers),
                'papers': papers[:5],  # Send first 5 papers
                'timestamp': datetime.now().isoformat()
            }, room=room_name)
    
    def notify_paper_bookmarked(self, user_id, paper_id, paper_title):
        """Notify when a paper is bookmarked"""
        notification = {
            'type': 'bookmark',
            'title': 'Paper Bookmarked',
            'message': f'You bookmarked: {paper_title[:100]}...',
            'paper_id': paper_id
        }
        self.send_notification(user_id, notification)
    
    def suggest_collaboration(self, user_id, potential_collaborators):
        """Suggest potential collaborations"""
        if len(potential_collaborators) >= self.alert_thresholds['collaboration']:
            notification = {
                'type': 'collaboration',
                'title': 'Potential Collaboration',
                'message': f'Found {len(potential_collaborators)} researchers working on similar topics.',
                'collaborators': potential_collaborators[:5]
            }
            self.send_notification(user_id, notification)
    
    def mark_notification_read(self, user_id, notification_id):
        """Mark notification as read"""
        for notification in self.notifications[user_id]:
            if notification.get('id') == notification_id:
                notification['read'] = True
                break
    
    def get_user_notifications(self, user_id, unread_only=False):
        """Get notifications for a user"""
        notifications = self.notifications[user_id]
        
        if unread_only:
            notifications = [n for n in notifications if not n.get('read', False)]
        
        return sorted(notifications, key=lambda x: x['timestamp'], reverse=True)
    
    def create_shared_session(self, user_id, session_name, query):
        """Create a shared research session"""
        session_id = f"shared_{int(time.time())}"
        
        session_data = {
            'id': session_id,
            'name': session_name,
            'creator': user_id,
            'query': query,
            'participants': [user_id],
            'created_at': datetime.now().isoformat(),
            'messages': [],
            'shared_papers': []
        }
        
        # Store session (in production, use persistent storage)
        # For now, using in-memory storage
        
        return session_data
    
    def send_realtime_stats(self):
        """Send real-time statistics to all connected users"""
        stats = {
            'active_users': len(self.active_users),
            'active_searches': len(self.search_rooms),
            'trending_topics': self.trending_topics,
            'timestamp': datetime.now().isoformat()
        }
        
        self.socketio.emit('realtime_stats', stats)
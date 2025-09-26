# Paper Management System
import json
import uuid
from datetime import datetime
import sqlite3
import os

class PaperManager:
    def __init__(self, db_path='paper_manager.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferences TEXT
            )
        ''')
        
        # Papers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                citation_count INTEGER,
                doi TEXT,
                url TEXT,
                source TEXT,
                abstract TEXT,
                keywords TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User paper interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_papers (
                user_id TEXT,
                paper_id TEXT,
                interaction_type TEXT, -- 'bookmark', 'reading_list', 'read', 'favorite'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, paper_id, interaction_type),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')
        
        # Notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                paper_id TEXT,
                content TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')
        
        # Collections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                is_public BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Collection papers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_papers (
                collection_id TEXT,
                paper_id TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (collection_id, paper_id),
                FOREIGN KEY (collection_id) REFERENCES collections(id),
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')
        
        # Reading progress
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_progress (
                user_id TEXT,
                paper_id TEXT,
                status TEXT, -- 'unread', 'reading', 'read', 'reviewed'
                progress_percentage INTEGER DEFAULT 0,
                reading_time_minutes INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, paper_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, user_id=None):
        """Create a new user"""
        if not user_id:
            user_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (id, preferences) VALUES (?, ?)',
                (user_id, json.dumps({}))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # User already exists
        finally:
            conn.close()
        
        return user_id
    
    def save_paper(self, paper_data):
        """Save paper to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO papers 
            (id, title, authors, year, citation_count, doi, url, source, abstract, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            paper_data.get('id'),
            paper_data.get('title'),
            paper_data.get('authors'),
            self._safe_int(paper_data.get('year')),
            self._safe_int(paper_data.get('citation_count')),
            paper_data.get('doi'),
            paper_data.get('url'),
            paper_data.get('source'),
            paper_data.get('abstract', ''),
            paper_data.get('keywords', '')
        ))
        
        conn.commit()
        conn.close()
    
    def add_to_bookmark(self, user_id, paper_id):
        """Add paper to user's bookmarks"""
        return self._add_user_paper_interaction(user_id, paper_id, 'bookmark')
    
    def remove_from_bookmark(self, user_id, paper_id):
        """Remove paper from user's bookmarks"""
        return self._remove_user_paper_interaction(user_id, paper_id, 'bookmark')
    
    def add_to_reading_list(self, user_id, paper_id):
        """Add paper to user's reading list"""
        return self._add_user_paper_interaction(user_id, paper_id, 'reading_list')
    
    def remove_from_reading_list(self, user_id, paper_id):
        """Remove paper from user's reading list"""
        return self._remove_user_paper_interaction(user_id, paper_id, 'reading_list')
    
    def _add_user_paper_interaction(self, user_id, paper_id, interaction_type):
        """Generic method to add user-paper interaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_papers 
            (user_id, paper_id, interaction_type, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, paper_id, interaction_type, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    
    def _remove_user_paper_interaction(self, user_id, paper_id, interaction_type):
        """Generic method to remove user-paper interaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_papers 
            WHERE user_id = ? AND paper_id = ? AND interaction_type = ?
        ''', (user_id, paper_id, interaction_type))
        
        conn.commit()
        conn.close()
        return True
    
    def get_user_papers(self, user_id, interaction_type=None):
        """Get papers for a user by interaction type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT p.*, up.interaction_type, up.created_at as interaction_date
            FROM papers p
            JOIN user_papers up ON p.id = up.paper_id
            WHERE up.user_id = ?
        '''
        params = [user_id]
        
        if interaction_type:
            query += ' AND up.interaction_type = ?'
            params.append(interaction_type)
        
        query += ' ORDER BY up.updated_at DESC'
        
        cursor.execute(query, params)
        papers = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, paper)) for paper in papers]
    
    def add_note(self, user_id, paper_id, content, tags=None):
        """Add a note to a paper"""
        note_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notes (id, user_id, paper_id, content, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (note_id, user_id, paper_id, content, json.dumps(tags or [])))
        
        conn.commit()
        conn.close()
        
        return note_id
    
    def get_notes(self, user_id, paper_id=None):
        """Get notes for a user or specific paper"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM notes WHERE user_id = ?'
        params = [user_id]
        
        if paper_id:
            query += ' AND paper_id = ?'
            params.append(paper_id)
        
        query += ' ORDER BY updated_at DESC'
        
        cursor.execute(query, params)
        notes = cursor.fetchall()
        conn.close()
        
        columns = [desc[0] for desc in cursor.description]
        result = []
        for note in notes:
            note_dict = dict(zip(columns, note))
            note_dict['tags'] = json.loads(note_dict['tags'] or '[]')
            result.append(note_dict)
        
        return result
    
    def update_note(self, note_id, content, tags=None):
        """Update an existing note"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notes 
            SET content = ?, tags = ?, updated_at = ?
            WHERE id = ?
        ''', (content, json.dumps(tags or []), datetime.now().isoformat(), note_id))
        
        conn.commit()
        conn.close()
    
    def delete_note(self, note_id):
        """Delete a note"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        
        conn.commit()
        conn.close()
    
    def create_collection(self, user_id, name, description='', is_public=False):
        """Create a new collection"""
        collection_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO collections (id, user_id, name, description, is_public)
            VALUES (?, ?, ?, ?, ?)
        ''', (collection_id, user_id, name, description, is_public))
        
        conn.commit()
        conn.close()
        
        return collection_id
    
    def add_paper_to_collection(self, collection_id, paper_id):
        """Add paper to collection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO collection_papers (collection_id, paper_id)
            VALUES (?, ?)
        ''', (collection_id, paper_id))
        
        conn.commit()
        conn.close()
    
    def get_user_collections(self, user_id):
        """Get all collections for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, COUNT(cp.paper_id) as paper_count
            FROM collections c
            LEFT JOIN collection_papers cp ON c.id = cp.collection_id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''', (user_id,))
        
        collections = cursor.fetchall()
        conn.close()
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, collection)) for collection in collections]
    
    def update_reading_progress(self, user_id, paper_id, status, progress=0, reading_time=0):
        """Update reading progress for a paper"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO reading_progress 
            (user_id, paper_id, status, progress_percentage, reading_time_minutes, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, paper_id, status, progress, reading_time, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_reading_stats(self, user_id):
        """Get reading statistics for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_papers,
                SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as papers_read,
                SUM(reading_time_minutes) as total_reading_time,
                AVG(reading_time_minutes) as avg_reading_time
            FROM reading_progress 
            WHERE user_id = ?
        ''', (user_id,))
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats:
            return {
                'total_papers': stats[0],
                'papers_read': stats[1],
                'total_reading_time': stats[2] or 0,
                'avg_reading_time': stats[3] or 0,
                'reading_completion_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
            }
        
        return {}
    
    def export_user_data(self, user_id, format='json'):
        """Export all user data"""
        data = {
            'bookmarks': self.get_user_papers(user_id, 'bookmark'),
            'reading_list': self.get_user_papers(user_id, 'reading_list'),
            'notes': self.get_notes(user_id),
            'collections': self.get_user_collections(user_id),
            'reading_stats': self.get_reading_stats(user_id),
            'exported_at': datetime.now().isoformat()
        }
        
        if format == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format == 'bibtex':
            return self._export_bibtex(data['bookmarks'])
        
        return data
    
    def _export_bibtex(self, papers):
        """Export papers in BibTeX format"""
        bibtex_entries = []
        
        for paper in papers:
            # Generate BibTeX key
            first_author = paper.get('authors', '').split(',')[0].strip().replace(' ', '')
            year = paper.get('year', 'unknown')
            title_words = paper.get('title', '').split()[:3]
            key = f"{first_author}{year}{''.join(title_words)}"
            
            entry = f"@article{{{key},\n"
            entry += f"  title={{{paper.get('title', '')}}},\n"
            entry += f"  author={{{paper.get('authors', '')}}},\n"
            entry += f"  year={{{paper.get('year', '')}}},\n"
            
            if paper.get('doi'):
                entry += f"  doi={{{paper.get('doi')}}},\n"
            if paper.get('url'):
                entry += f"  url={{{paper.get('url')}}},\n"
            
            entry += "}\n"
            bibtex_entries.append(entry)
        
        return '\n'.join(bibtex_entries)
    
    def _safe_int(self, value):
        """Safely convert value to integer"""
        if value in ['Year Not Available', 'Citation Count Not Available', None]:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
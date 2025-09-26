# Advanced Search Features Module
import re
from collections import defaultdict
import difflib
from datetime import datetime, timedelta

class AdvancedSearchEngine:
    def __init__(self):
        self.search_history = []
        self.popular_queries = defaultdict(int)
        self.trending_topics = []
    
    def analyze_query(self, query):
        """Analyze search query for intent and extract keywords"""
        analysis = {
            'keywords': [],
            'quoted_phrases': [],
            'boolean_operators': [],
            'field_queries': {},
            'intent': 'general'
        }
        
        # Extract quoted phrases
        quoted_pattern = r'"([^"]*)"'
        quotes = re.findall(quoted_pattern, query)
        analysis['quoted_phrases'] = quotes
        
        # Remove quoted phrases for further processing
        clean_query = re.sub(quoted_pattern, '', query)
        
        # Extract field-specific queries (author:name, year:2020, etc.)
        field_pattern = r'(\w+):([^\s]+)'
        field_matches = re.findall(field_pattern, clean_query)
        for field, value in field_matches:
            analysis['field_queries'][field.lower()] = value
        
        # Remove field queries for keyword extraction
        clean_query = re.sub(field_pattern, '', clean_query)
        
        # Extract boolean operators
        boolean_ops = re.findall(r'\b(AND|OR|NOT)\b', clean_query, re.IGNORECASE)
        analysis['boolean_operators'] = boolean_ops
        
        # Extract remaining keywords
        keywords = re.findall(r'\b\w+\b', clean_query.lower())
        keywords = [k for k in keywords if k not in ['and', 'or', 'not']]
        analysis['keywords'] = keywords
        
        # Determine search intent
        if any(word in keywords for word in ['survey', 'review', 'overview']):
            analysis['intent'] = 'survey'
        elif any(word in keywords for word in ['method', 'algorithm', 'technique']):
            analysis['intent'] = 'methodology'
        elif any(word in keywords for word in ['dataset', 'data', 'benchmark']):
            analysis['intent'] = 'dataset'
        
        return analysis
    
    def suggest_related_queries(self, query, papers):
        """Suggest related search queries based on current results"""
        suggestions = []
        
        # Extract common terms from paper titles and abstracts
        all_text = ' '.join([paper['title'] for paper in papers])
        words = re.findall(r'\b\w+\b', all_text.lower())
        word_freq = defaultdict(int)
        
        for word in words:
            if len(word) > 3 and word not in ['paper', 'study', 'research', 'analysis']:
                word_freq[word] += 1
        
        # Get top words not in original query
        query_words = set(query.lower().split())
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for word, freq in top_words:
            if word not in query_words and freq > 1:
                suggestions.append(f"{query} {word}")
        
        return suggestions[:5]
    
    def smart_autocomplete(self, prefix, paper_titles, search_history):
        """Enhanced autocomplete with learning from search history"""
        suggestions = []
        
        # Direct title matches
        title_matches = [title for title in paper_titles if title.lower().startswith(prefix.lower())]
        suggestions.extend(title_matches[:3])
        
        # Fuzzy matches for typos
        fuzzy_matches = difflib.get_close_matches(prefix, paper_titles, n=3, cutoff=0.6)
        suggestions.extend(fuzzy_matches)
        
        # Historical query matches
        history_matches = [query for query in search_history if prefix.lower() in query.lower()]
        suggestions.extend(history_matches[:2])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:8]
    
    def filter_papers_advanced(self, papers, filters):
        """Apply advanced filtering with multiple criteria"""
        filtered_papers = papers.copy()
        
        # Author filter with fuzzy matching
        if 'author_name' in filters and filters['author_name']:
            author_query = filters['author_name'].lower()
            filtered_papers = [
                paper for paper in filtered_papers
                if any(difflib.SequenceMatcher(None, author_query, author.lower()).ratio() > 0.7
                      for author in paper.get('authors', '').split(', '))
            ]
        
        # Keyword in title filter
        if 'title_keywords' in filters and filters['title_keywords']:
            keywords = [kw.strip().lower() for kw in filters['title_keywords'].split(',')]
            filtered_papers = [
                paper for paper in filtered_papers
                if any(keyword in paper.get('title', '').lower() for keyword in keywords)
            ]
        
        # Citation range filter
        if 'citation_range' in filters:
            min_cit = filters['citation_range'].get('min', 0)
            max_cit = filters['citation_range'].get('max', float('inf'))
            
            filtered_papers = [
                paper for paper in filtered_papers
                if self._get_citation_count(paper) >= min_cit and 
                   self._get_citation_count(paper) <= max_cit
            ]
        
        # Venue/Journal filter
        if 'venue' in filters and filters['venue']:
            venue_query = filters['venue'].lower()
            filtered_papers = [
                paper for paper in filtered_papers
                if venue_query in paper.get('venue', '').lower()
            ]
        
        # Recency filter (papers from last N days)
        if 'recency_days' in filters and filters['recency_days']:
            cutoff_date = datetime.now() - timedelta(days=filters['recency_days'])
            filtered_papers = [
                paper for paper in filtered_papers
                if self._is_recent_paper(paper, cutoff_date)
            ]
        
        return filtered_papers
    
    def _get_citation_count(self, paper):
        """Safely extract citation count from paper"""
        citations = paper.get('citation_count', 0)
        if citations == 'Citation Count Not Available':
            return 0
        try:
            return int(citations)
        except (ValueError, TypeError):
            return 0
    
    def _is_recent_paper(self, paper, cutoff_date):
        """Check if paper is recent based on publication date"""
        year = paper.get('year')
        if year == 'Year Not Available':
            return False
        try:
            paper_date = datetime(int(year), 1, 1)
            return paper_date >= cutoff_date
        except (ValueError, TypeError):
            return False
    
    def get_search_trends(self):
        """Analyze search trends and popular topics"""
        trends = {
            'popular_queries': dict(sorted(self.popular_queries.items(), 
                                         key=lambda x: x[1], reverse=True)[:10]),
            'trending_topics': self.trending_topics,
            'search_volume': len(self.search_history)
        }
        return trends
    
    def record_search(self, query, result_count):
        """Record search for analytics and trend analysis"""
        search_record = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'result_count': result_count
        }
        
        self.search_history.append(search_record)
        self.popular_queries[query] += 1
        
        # Keep only recent history (last 1000 searches)
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-1000:]
    
    def generate_search_insights(self, papers):
        """Generate insights about search results"""
        insights = {}
        
        # Publication trend analysis
        year_counts = defaultdict(int)
        for paper in papers:
            year = paper.get('year')
            if year != 'Year Not Available':
                try:
                    year_counts[int(year)] += 1
                except (ValueError, TypeError):
                    pass
        
        if year_counts:
            peak_year = max(year_counts.items(), key=lambda x: x[1])
            insights['peak_year'] = f"Peak publication year: {peak_year[0]} ({peak_year[1]} papers)"
        
        # Author collaboration analysis
        all_authors = []
        for paper in papers:
            authors = paper.get('authors', '').split(', ')
            all_authors.extend([a.strip() for a in authors if a.strip()])
        
        author_counts = defaultdict(int)
        for author in all_authors:
            author_counts[author] += 1
        
        prolific_authors = [author for author, count in author_counts.items() if count > 1]
        if prolific_authors:
            insights['prolific_authors'] = f"Found {len(prolific_authors)} authors with multiple papers"
        
        # Citation impact analysis
        citations = [self._get_citation_count(paper) for paper in papers]
        if citations:
            avg_citations = sum(citations) / len(citations)
            high_impact = [c for c in citations if c > avg_citations * 2]
            insights['impact_analysis'] = f"Average citations: {avg_citations:.1f}, High-impact papers: {len(high_impact)}"
        
        # Research area diversity
        title_words = []
        for paper in papers:
            words = re.findall(r'\b\w+\b', paper.get('title', '').lower())
            title_words.extend([w for w in words if len(w) > 4])
        
        word_diversity = len(set(title_words)) / len(title_words) if title_words else 0
        insights['diversity'] = f"Topic diversity score: {word_diversity:.2f}"
        
        return insights

# Search query templates for different research domains
DOMAIN_TEMPLATES = {
    'machine_learning': [
        'neural networks {topic}',
        'deep learning {topic}',
        'machine learning {topic}',
        '{topic} classification',
        '{topic} prediction'
    ],
    'computer_vision': [
        'image {topic}',
        'computer vision {topic}',
        'object detection {topic}',
        'image classification {topic}',
        'visual {topic}'
    ],
    'natural_language': [
        'natural language processing {topic}',
        'text {topic}',
        'language model {topic}',
        'NLP {topic}',
        'text mining {topic}'
    ],
    'data_science': [
        'data analysis {topic}',
        'big data {topic}',
        'data mining {topic}',
        'statistical {topic}',
        'analytics {topic}'
    ]
}

def suggest_domain_queries(topic, domain='general'):
    """Suggest domain-specific search queries"""
    if domain in DOMAIN_TEMPLATES:
        return [template.format(topic=topic) for template in DOMAIN_TEMPLATES[domain]]
    return [topic]
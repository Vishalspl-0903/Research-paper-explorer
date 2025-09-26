# � Research Paper Explorer
### Advanced Interactive Research Platform

A comprehensive web-based research platform that transforms academic paper discovery through real-time search, AI-powered recommendations, and collaborative research tools.

## ✨ Features

### 🎯 Smart Search & Discovery
- **Multi-source Integration**: Semantic Scholar, arXiv, CrossRef APIs
- **Intelligent Autocomplete**: Real-time suggestions with fuzzy matching
- **Advanced Filtering**: Domain-specific search templates and filters
- **Related Query Suggestions**: AI-powered query expansion

### 🤖 AI-Powered Recommendations
- **Content-Based Filtering**: TF-IDF similarity analysis
- **Collaborative Filtering**: User behavior patterns
- **Personalized Profiles**: Adaptive user interest modeling
- **Diversity Algorithms**: Balanced recommendation sets

### 📊 Interactive Analytics
- **Research Trends**: Temporal publication patterns
- **Collaboration Networks**: Author relationship mapping
- **Topic Clustering**: Semantic paper grouping
- **Impact Metrics**: Citation and influence analysis
- **Visual Dashboards**: Interactive charts and graphs

### 🔄 Real-time Collaboration
- **Live Updates**: WebSocket-powered notifications
- **Shared Collections**: Collaborative paper management
- **Research Sessions**: Team synchronization
- **Trending Topics**: Community activity monitoring

### 📚 Comprehensive Paper Management
- **Personal Library**: Bookmarks and reading lists
- **Note-Taking**: Rich text annotations
- **Reading Progress**: Track paper completion
- **BibTeX Export**: Citation management
- **Collection Organization**: Custom paper groupings

### 🏗️ Advanced Architecture
- **Data Structures**: AVL Trees and Red-Black Trees for efficient operations
- **Caching Layer**: Redis for performance optimization
- **Background Processing**: Asynchronous search and analysis
- **RESTful API**: 20+ endpoints for all functionality
- **WebSocket Integration**: Real-time bidirectional communication

## 🚀 Quick Start

### Simple Setup
```bash
# Clone the repository
git clone <repository-url>
cd research-paper-explorer

# Run the startup script
python run.py
```

The startup script will:
- ✅ Check and install all dependencies
- ✅ Initialize the database
- ✅ Start background workers
- ✅ Launch the web application
- 🌐 Open at `http://localhost:5000`

### Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python app.py
```

### Docker Deployment
```bash
# Build and run with Docker Compose (Production Ready)
docker-compose up --build

# Run in background
docker-compose up -d --build

# Access at http://localhost (with Nginx proxy)
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask with Flask-SocketIO
- **Database**: SQLite with full schema design
- **Caching**: Redis for performance
- **ML/AI**: scikit-learn, NetworkX
- **APIs**: Multiple academic data sources

### Frontend
- **UI Framework**: Bootstrap 5 responsive design
- **Visualizations**: Chart.js for interactive charts
- **Real-time**: WebSocket client integration
- **UX**: Modern animations and transitions

### Infrastructure
- **Containerization**: Docker with multi-service architecture
- **Reverse Proxy**: Nginx with rate limiting
- **Security**: HTTPS, CORS, input validation
- **Monitoring**: Health checks and logging

## 📁 Project Structure

```
research-paper-explorer/
├── app.py                   # Main Flask application
├── main.py                  # Original CLI tool (preserved)  
├── run.py                   # Startup script
├── worker.py                # Background processing
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation
├── Dockerfile              # Docker container config
├── docker-compose.yml      # Multi-service Docker setup
├── nginx.conf              # Nginx reverse proxy config
├── advanced_search.py      # Enhanced search engine
├── analytics.py            # Research analytics
├── paper_manager.py        # Data persistence layer
├── realtime.py             # WebSocket real-time features
├── recommendations.py      # ML recommendation system
├── templates/
│   └── index.html          # Main web interface
└── static/
    ├── css/
    │   └── style.css       # Advanced styling
    └── js/
        └── app.js          # Frontend JavaScript
```

## 📦 **Files Tracked in Git**

### ✅ **Core Application Files (Included):**
- **Python Source**: `*.py` - All application logic
- **Web Assets**: `templates/`, `static/` - Frontend files
- **Configuration**: `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `nginx.conf`
- **Documentation**: `README.md`, `.gitignore`

### 🚫 **Runtime Data (Excluded):**
- **Databases**: `*.db`, `*.sqlite` - Generated at runtime
- **Logs**: `*.log` - Application logs
- **Cache**: `__pycache__/`, Redis dumps
- **User Data**: Uploads, bookmarks, collections
- **Secrets**: API keys, credentials

## � Configuration

### Environment Variables
```bash
# Optional Redis configuration
REDIS_URL=redis://localhost:6379/0

# API Keys (optional, for enhanced features)
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

### Features Toggles
- Redis: Enables caching and background processing
- API Keys: Increases rate limits and access to premium features

## 🎮 Usage Guide

### 1. **Search & Discover**
- Enter research queries in the search bar
- Use advanced filters for precise results
- Browse autocomplete suggestions
- Explore related topics

### 2. **Analyze & Visualize**
- View interactive analytics dashboard
- Explore collaboration networks
- Track research trends
- Analyze topic clusters

### 3. **Manage & Organize**
- Bookmark interesting papers
- Create custom collections
- Take notes and track reading progress
- Export citations in BibTeX format

### 4. **Collaborate & Share**
- Join real-time research sessions
- Share collections with colleagues
- Monitor trending research topics
- Receive personalized recommendations

## �️ Data Structures & Algorithms

### AVL Tree Implementation
- **Purpose**: Citation-based paper ranking
- **Operations**: O(log n) search, insert, delete
- **Use Case**: Maintaining sorted paper collections

### Red-Black Tree Implementation
- **Purpose**: Author-based organization
- **Operations**: Guaranteed O(log n) with color balancing
- **Use Case**: Author collaboration analysis

### Machine Learning
- **TF-IDF Vectorization**: Content similarity analysis
- **Collaborative Filtering**: User behavior patterns
- **Network Analysis**: Collaboration graph algorithms

## 🔒 Security Features

- **Input Validation**: XSS and injection protection
- **Rate Limiting**: API abuse prevention
- **CORS Configuration**: Cross-origin security
- **Security Headers**: HTTPS and security best practices

## 📈 Performance Optimizations

- **Redis Caching**: Search results and recommendations
- **Background Processing**: Asynchronous heavy operations
- **Database Indexing**: Optimized query performance
- **CDN Ready**: Static asset optimization

## 🧪 API Documentation

### Core Endpoints
- `GET /api/search` - Paper search with filters
- `GET /api/analytics/comprehensive` - Research analytics
- `POST /api/papers/bookmark` - Paper management
- `GET /api/recommendations` - AI recommendations
- `WebSocket /` - Real-time features

### Health & Status
- `GET /api/health` - Application health check
- `GET /api/stats` - Usage statistics

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black . && flake8 .
```

## � Roadmap

- [ ] **Mobile App**: React Native companion app
- [ ] **Advanced ML**: Deep learning recommendation models
- [ ] **Integration**: Mendeley, Zotero, and other tools
- [ ] **Multi-language**: Internationalization support
- [ ] **Enterprise**: SSO and advanced admin features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Academic APIs**: Semantic Scholar, arXiv, CrossRef
- **Open Source**: Flask, scikit-learn, NetworkX communities
- **Design**: Bootstrap and Chart.js teams

## 📞 Support

- **Issues**: Create issues for bugs or feature requests
- **Discussions**: Share ideas and get help from the community
- **Documentation**: Comprehensive guides in this README

## 🔄 Version History

- **v2.0**: Full web platform with AI recommendations and real-time features
- **v1.0**: Original CLI tool with AVL and Red-Black tree implementations

## 🏗️ **Repository Management**

### **What's Included in Git:**
- All core application files (`*.py`)
- Web assets (`templates/`, `static/`)
- Docker configuration (`Dockerfile`, `docker-compose.yml`, `nginx.conf`)  
- Documentation and dependencies (`README.md`, `requirements.txt`, `.gitignore`)

### **What's Excluded:**
- Runtime databases (`*.db`, `*.sqlite`)
- User-generated content (uploads, bookmarks)
- Log files and cache data
- Sensitive information (API keys, credentials)
- Virtual environments (`venv/`, `env/`)

This ensures a clean, secure, and lightweight repository! 🧹

---

**Transform your research workflow with intelligent paper discovery and collaborative analytics!** 🚀

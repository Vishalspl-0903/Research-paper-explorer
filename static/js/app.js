// Research Paper Explorer - Main JavaScript Application

class ResearchPaperExplorer {
    constructor() {
        this.papers = [];
        this.currentAnalysis = null;
        this.bookmarks = new Set();
        this.readingList = new Set();
        this.socket = null;
        this.charts = {};
        this.currentSort = 'relevance';
        this.currentView = 'grid';
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSocketConnection();
        this.loadUserData();
        this.setupAutocomplete();
    }

    setupEventListeners() {
        // Search form
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });

        // Real-time search input
        const searchInput = document.getElementById('searchQuery');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (e.target.value.length > 2) {
                    this.getAutocomplete(e.target.value);
                } else {
                    this.hideAutocomplete();
                }
            }, 300);
        });

        // Sort and view controls
        document.getElementById('sortBy').addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.sortAndDisplayPapers();
        });

        document.getElementById('viewToggle').addEventListener('click', () => {
            this.toggleView();
        });

        // Export functions
        document.getElementById('exportBookmarks').addEventListener('click', () => {
            this.exportData('bookmarks');
        });

        document.getElementById('exportReadingList').addEventListener('click', () => {
            this.exportData('readingList');
        });

        // Load more papers
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMorePapers();
        });

        // Close autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideAutocomplete();
            }
        });
    }

    setupSocketConnection() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
            });

            this.socket.on('connected', (data) => {
                console.log('User ID:', data.user_id);
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
            });
        } catch (error) {
            console.log('Socket.IO not available, continuing without real-time features');
        }
    }

    async performSearch() {
        const query = document.getElementById('searchQuery').value.trim();
        if (!query) return;

        this.showLoading();
        this.hideAutocomplete();

        try {
            const searchData = this.getSearchParameters();
            
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    ...searchData
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.papers = data.papers;
            this.currentAnalysis = data.analysis;
            
            this.hideLoading();
            this.displayResults(data);
            this.displayAnalytics(data.analysis);
            this.createFilterTags(searchData);
            
            // Join search room for collaborative features
            if (this.socket) {
                this.socket.emit('join_search', { search_query: query });
            }

        } catch (error) {
            console.error('Search error:', error);
            this.hideLoading();
            this.showError('Failed to search papers. Please try again.');
        }
    }

    getSearchParameters() {
        const sources = [];
        if (document.getElementById('semanticScholar').checked) sources.push('semantic_scholar');
        if (document.getElementById('crossref').checked) sources.push('crossref');
        if (document.getElementById('arxiv').checked) sources.push('arxiv');

        return {
            sources: sources,
            year_range: {
                min: parseInt(document.getElementById('yearMin').value) || 1900,
                max: parseInt(document.getElementById('yearMax').value) || 2024
            },
            min_citations: parseInt(document.getElementById('minCitations').value) || 0
        };
    }

    displayResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsInfo = document.getElementById('resultsInfo');
        
        resultsInfo.textContent = `Found ${data.total_count} papers for "${data.search_query}"`;
        
        this.sortAndDisplayPapers();
        
        resultsSection.classList.remove('d-none');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    sortAndDisplayPapers() {
        let sortedPapers = [...this.papers];

        switch (this.currentSort) {
            case 'year':
                sortedPapers.sort((a, b) => {
                    const yearA = parseInt(a.year) || 0;
                    const yearB = parseInt(b.year) || 0;
                    return yearB - yearA;
                });
                break;
            case 'citations':
                sortedPapers.sort((a, b) => {
                    const citA = parseInt(a.citation_count) || 0;
                    const citB = parseInt(b.citation_count) || 0;
                    return citB - citA;
                });
                break;
            case 'title':
                sortedPapers.sort((a, b) => a.title.localeCompare(b.title));
                break;
            default: // relevance
                break;
        }

        this.renderPapers(sortedPapers);
    }

    renderPapers(papers) {
        const container = document.getElementById('papersContainer');
        container.innerHTML = '';

        papers.forEach((paper, index) => {
            const paperCard = this.createPaperCard(paper, index);
            container.appendChild(paperCard);
        });

        // Add animation
        container.querySelectorAll('.paper-card').forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in');
            }, index * 100);
        });
    }

    createPaperCard(paper, index) {
        const col = document.createElement('div');
        col.className = 'col-lg-6 col-xl-4 mb-4';

        const isBookmarked = this.bookmarks.has(paper.id);
        const isInReadingList = this.readingList.has(paper.id);

        col.innerHTML = `
            <div class="paper-card">
                <div class="card-header">
                    <span class="source-badge source-${paper.source.toLowerCase().replace(' ', '-')}">
                        ${paper.source}
                    </span>
                    <div class="float-end">
                        <button class="btn btn-sm btn-outline-light bookmark-btn ${isBookmarked ? 'active' : ''}" 
                                data-paper-id="${paper.id}" title="Bookmark">
                            <i class="fas fa-bookmark"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <h3 class="paper-title">${this.truncateText(paper.title, 120)}</h3>
                    <p class="paper-authors">
                        <i class="fas fa-users me-1"></i>
                        ${this.truncateText(paper.authors, 100)}
                    </p>
                    <div class="paper-meta">
                        <span class="meta-item">
                            <i class="fas fa-calendar-alt"></i>
                            ${paper.year}
                        </span>
                        <span class="meta-item">
                            <i class="fas fa-quote-right"></i>
                            ${paper.citation_count} citations
                        </span>
                        ${paper.doi !== 'DOI Not Available' ? `
                            <span class="meta-item">
                                <i class="fas fa-link"></i>
                                DOI
                            </span>
                        ` : ''}
                    </div>
                    <div class="paper-actions">
                        <button class="btn btn-action view-details-btn" data-paper-id="${paper.id}">
                            <i class="fas fa-eye me-1"></i>Details
                        </button>
                        <button class="btn btn-action reading-list-btn ${isInReadingList ? 'active' : ''}" 
                                data-paper-id="${paper.id}">
                            <i class="fas fa-list me-1"></i>Reading List
                        </button>
                        ${paper.url !== 'URL Not Available' ? `
                            <a href="${paper.url}" target="_blank" class="btn btn-action">
                                <i class="fas fa-external-link-alt me-1"></i>Open
                            </a>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        // Add event listeners
        this.setupPaperCardListeners(col);

        return col;
    }

    setupPaperCardListeners(cardElement) {
        // Bookmark button
        const bookmarkBtn = cardElement.querySelector('.bookmark-btn');
        bookmarkBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleBookmark(bookmarkBtn.dataset.paperId);
        });

        // Reading list button
        const readingListBtn = cardElement.querySelector('.reading-list-btn');
        readingListBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleReadingList(readingListBtn.dataset.paperId);
        });

        // View details button
        const viewDetailsBtn = cardElement.querySelector('.view-details-btn');
        viewDetailsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showPaperDetails(viewDetailsBtn.dataset.paperId);
        });
    }

    async toggleBookmark(paperId) {
        try {
            const action = this.bookmarks.has(paperId) ? 'remove' : 'add';
            
            const response = await fetch('/api/bookmark', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    paper_id: paperId,
                    action: action
                })
            });

            if (response.ok) {
                if (action === 'add') {
                    this.bookmarks.add(paperId);
                } else {
                    this.bookmarks.delete(paperId);
                }
                
                this.updateBookmarkUI(paperId);
                this.updateBookmarkCount();
            }
        } catch (error) {
            console.error('Bookmark error:', error);
            this.showError('Failed to update bookmark');
        }
    }

    async toggleReadingList(paperId) {
        try {
            const action = this.readingList.has(paperId) ? 'remove' : 'add';
            
            const response = await fetch('/api/reading-list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    paper_id: paperId,
                    action: action
                })
            });

            if (response.ok) {
                if (action === 'add') {
                    this.readingList.add(paperId);
                } else {
                    this.readingList.delete(paperId);
                }
                
                this.updateReadingListUI(paperId);
                this.updateReadingListCount();
            }
        } catch (error) {
            console.error('Reading list error:', error);
            this.showError('Failed to update reading list');
        }
    }

    async showPaperDetails(paperId) {
        try {
            const response = await fetch(`/api/paper/${paperId}`);
            const paper = await response.json();

            if (paper.error) {
                throw new Error(paper.error);
            }

            const modal = new bootstrap.Modal(document.getElementById('paperDetailModal'));
            const content = document.getElementById('paperDetailContent');

            content.innerHTML = `
                <div class="row">
                    <div class="col-lg-8">
                        <h2 class="h4 mb-3">${paper.title}</h2>
                        <p class="text-muted mb-3">
                            <strong>Authors:</strong> ${paper.authors}
                        </p>
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Year:</strong> ${paper.year}
                            </div>
                            <div class="col-md-4">
                                <strong>Citations:</strong> ${paper.citation_count}
                            </div>
                            <div class="col-md-4">
                                <strong>Source:</strong> ${paper.source}
                            </div>
                        </div>
                        ${paper.doi !== 'DOI Not Available' ? `
                            <p><strong>DOI:</strong> ${paper.doi}</p>
                        ` : ''}
                        ${paper.url !== 'URL Not Available' ? `
                            <p><strong>URL:</strong> <a href="${paper.url}" target="_blank">${paper.url}</a></p>
                        ` : ''}
                    </div>
                    <div class="col-lg-4">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Quick Actions</h6>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <button class="btn btn-primary bookmark-detail-btn" data-paper-id="${paper.id}">
                                        <i class="fas fa-bookmark me-2"></i>
                                        ${this.bookmarks.has(paper.id) ? 'Remove Bookmark' : 'Add Bookmark'}
                                    </button>
                                    <button class="btn btn-outline-primary reading-detail-btn" data-paper-id="${paper.id}">
                                        <i class="fas fa-list me-2"></i>
                                        ${this.readingList.has(paper.id) ? 'Remove from Reading List' : 'Add to Reading List'}
                                    </button>
                                    ${paper.url !== 'URL Not Available' ? `
                                        <a href="${paper.url}" target="_blank" class="btn btn-success">
                                            <i class="fas fa-external-link-alt me-2"></i>Open Paper
                                        </a>
                                    ` : ''}
                                    <button class="btn btn-outline-secondary export-citation-btn" data-paper-id="${paper.id}">
                                        <i class="fas fa-quote-right me-2"></i>Export Citation
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Setup modal event listeners
            content.querySelector('.bookmark-detail-btn').addEventListener('click', (e) => {
                this.toggleBookmark(e.target.dataset.paperId);
                modal.hide();
            });

            content.querySelector('.reading-detail-btn').addEventListener('click', (e) => {
                this.toggleReadingList(e.target.dataset.paperId);
                modal.hide();
            });

            const exportBtn = content.querySelector('.export-citation-btn');
            if (exportBtn) {
                exportBtn.addEventListener('click', () => {
                    this.exportCitation(paper);
                });
            }

            modal.show();

        } catch (error) {
            console.error('Paper details error:', error);
            this.showError('Failed to load paper details');
        }
    }

    async getAutocomplete(prefix) {
        try {
            const response = await fetch('/api/autocomplete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prefix: prefix })
            });

            const data = await response.json();
            this.showAutocomplete(data.suggestions);

        } catch (error) {
            console.error('Autocomplete error:', error);
        }
    }

    showAutocomplete(suggestions) {
        const dropdown = document.getElementById('autocompleteDropdown');
        
        if (suggestions.length === 0) {
            this.hideAutocomplete();
            return;
        }

        dropdown.innerHTML = suggestions.map(suggestion => `
            <div class="autocomplete-item" data-suggestion="${suggestion}">
                ${this.highlightMatch(suggestion, document.getElementById('searchQuery').value)}
            </div>
        `).join('');

        dropdown.style.display = 'block';

        // Add click listeners
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                document.getElementById('searchQuery').value = item.dataset.suggestion;
                this.hideAutocomplete();
                this.performSearch();
            });
        });
    }

    hideAutocomplete() {
        document.getElementById('autocompleteDropdown').style.display = 'none';
    }

    setupAutocomplete() {
        const searchInput = document.getElementById('searchQuery');
        
        searchInput.addEventListener('keydown', (e) => {
            const dropdown = document.getElementById('autocompleteDropdown');
            const items = dropdown.querySelectorAll('.autocomplete-item');
            const active = dropdown.querySelector('.autocomplete-item.active');

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (active) {
                    active.classList.remove('active');
                    const next = active.nextElementSibling || items[0];
                    next.classList.add('active');
                } else if (items.length > 0) {
                    items[0].classList.add('active');
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (active) {
                    active.classList.remove('active');
                    const prev = active.previousElementSibling || items[items.length - 1];
                    prev.classList.add('active');
                } else if (items.length > 0) {
                    items[items.length - 1].classList.add('active');
                }
            } else if (e.key === 'Enter') {
                if (active) {
                    e.preventDefault();
                    searchInput.value = active.dataset.suggestion;
                    this.hideAutocomplete();
                    this.performSearch();
                }
            } else if (e.key === 'Escape') {
                this.hideAutocomplete();
            }
        });
    }

    displayAnalytics(analysis) {
        if (!analysis) return;

        document.getElementById('analytics').classList.remove('d-none');

        this.createYearChart(analysis.year_distribution);
        this.createSourceChart(analysis.source_distribution);
        this.displayTopAuthors(analysis.top_authors);
        this.displayCitationStats(analysis.citation_stats);
    }

    createYearChart(yearData) {
        const ctx = document.getElementById('yearChart').getContext('2d');
        
        if (this.charts.yearChart) {
            this.charts.yearChart.destroy();
        }

        const years = Object.keys(yearData).sort();
        const counts = years.map(year => yearData[year]);

        this.charts.yearChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: [{
                    label: 'Publications',
                    data: counts,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    createSourceChart(sourceData) {
        const ctx = document.getElementById('sourceChart').getContext('2d');
        
        if (this.charts.sourceChart) {
            this.charts.sourceChart.destroy();
        }

        const labels = Object.keys(sourceData);
        const data = Object.values(sourceData);
        const colors = ['#2563eb', '#10b981', '#f59e0b'];

        this.charts.sourceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    displayTopAuthors(authorsData) {
        const container = document.getElementById('authorsChart');
        const authors = Object.entries(authorsData).slice(0, 10);

        container.innerHTML = authors.map(([author, count]) => `
            <div class="author-item">
                <span class="author-name">${author}</span>
                <span class="author-count">${count}</span>
            </div>
        `).join('');
    }

    displayCitationStats(stats) {
        const container = document.getElementById('citationStats');
        
        container.innerHTML = `
            <div class="citation-stat">
                <span class="citation-stat-value">${stats.total}</span>
                <span class="citation-stat-label">Total Citations</span>
            </div>
            <div class="citation-stat">
                <span class="citation-stat-value">${Math.round(stats.average)}</span>
                <span class="citation-stat-label">Average Citations</span>
            </div>
            <div class="citation-stat">
                <span class="citation-stat-value">${stats.max}</span>
                <span class="citation-stat-label">Max Citations</span>
            </div>
        `;
    }

    createFilterTags(searchData) {
        const container = document.getElementById('filterTags');
        const tags = [];

        if (searchData.sources.length < 3) {
            tags.push(`Sources: ${searchData.sources.join(', ')}`);
        }

        if (searchData.year_range.min > 1900 || searchData.year_range.max < 2024) {
            tags.push(`Years: ${searchData.year_range.min}-${searchData.year_range.max}`);
        }

        if (searchData.min_citations > 0) {
            tags.push(`Min Citations: ${searchData.min_citations}`);
        }

        container.innerHTML = tags.map(tag => `
            <span class="filter-tag">
                ${tag}
                <button class="remove-filter" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </span>
        `).join('');
    }

    toggleView() {
        const container = document.getElementById('papersContainer');
        const button = document.getElementById('viewToggle');
        
        if (this.currentView === 'grid') {
            this.currentView = 'list';
            container.className = 'row';
            button.innerHTML = '<i class="fas fa-th"></i>';
            // Add list view styling
        } else {
            this.currentView = 'grid';
            container.className = 'row';
            button.innerHTML = '<i class="fas fa-th-large"></i>';
        }
    }

    updateBookmarkUI(paperId) {
        const button = document.querySelector(`[data-paper-id="${paperId}"].bookmark-btn`);
        if (button) {
            button.classList.toggle('active', this.bookmarks.has(paperId));
        }
    }

    updateReadingListUI(paperId) {
        const button = document.querySelector(`[data-paper-id="${paperId}"].reading-list-btn`);
        if (button) {
            button.classList.toggle('active', this.readingList.has(paperId));
        }
    }

    updateBookmarkCount() {
        document.getElementById('bookmarkCount').textContent = this.bookmarks.size;
    }

    updateReadingListCount() {
        document.getElementById('readingListCount').textContent = this.readingList.size;
    }

    exportCitation(paper) {
        const citation = this.generateCitation(paper, 'apa');
        this.downloadText(citation, `${paper.title.substring(0, 50)}_citation.txt`);
    }

    generateCitation(paper, style = 'apa') {
        // Simple APA style citation
        const authors = paper.authors !== 'Authors Not Available' ? paper.authors : 'Unknown';
        const year = paper.year !== 'Year Not Available' ? paper.year : 'n.d.';
        const title = paper.title;
        
        return `${authors} (${year}). ${title}. Retrieved from ${paper.url}`;
    }

    exportData(type) {
        const data = type === 'bookmarks' ? this.getBookmarkedPapers() : this.getReadingListPapers();
        const filename = `${type}_${new Date().toISOString().split('T')[0]}.json`;
        
        this.downloadJSON(data, filename);
    }

    getBookmarkedPapers() {
        return this.papers.filter(paper => this.bookmarks.has(paper.id));
    }

    getReadingListPapers() {
        return this.papers.filter(paper => this.readingList.has(paper.id));
    }

    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        this.downloadBlob(blob, filename);
    }

    downloadText(text, filename) {
        const blob = new Blob([text], { type: 'text/plain' });
        this.downloadBlob(blob, filename);
    }

    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    loadUserData() {
        // Load from localStorage
        const saved = localStorage.getItem('researchPaperExplorer');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.bookmarks = new Set(data.bookmarks || []);
                this.readingList = new Set(data.readingList || []);
                this.updateBookmarkCount();
                this.updateReadingListCount();
            } catch (error) {
                console.error('Failed to load user data:', error);
            }
        }
    }

    saveUserData() {
        const data = {
            bookmarks: Array.from(this.bookmarks),
            readingList: Array.from(this.readingList)
        };
        localStorage.setItem('researchPaperExplorer', JSON.stringify(data));
    }

    showLoading() {
        document.getElementById('loadingIndicator').classList.remove('d-none');
        document.getElementById('resultsSection').classList.add('d-none');
        document.getElementById('analytics').classList.add('d-none');
    }

    hideLoading() {
        document.getElementById('loadingIndicator').classList.add('d-none');
    }

    showError(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast-notification error';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    highlightMatch(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    loadMorePapers() {
        // Implementation for pagination
        console.log('Load more papers functionality');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.paperExplorer = new ResearchPaperExplorer();
    
    // Save user data periodically
    setInterval(() => {
        window.paperExplorer.saveUserData();
    }, 30000); // Every 30 seconds
    
    // Save on page unload
    window.addEventListener('beforeunload', () => {
        window.paperExplorer.saveUserData();
    });
});
# 📚 Research Paper Fetcher with Tree-Based Analysis
This Python application allows users to fetch the latest research papers from Semantic Scholar, CrossRef, and arXiv using a keyword or title. It then organizes and analyzes the data using two classic data structures:

✅ AVL Tree for storing and autocompleting paper titles.

🔴 Red-Black Tree for tracking and listing unique authors efficiently.

🚀 Features
🔍 Fetch Research Papers: Query and retrieve metadata for top 5 papers from each source.

🌳 AVL Tree:

Stores paper titles.

Provides autocomplete suggestions based on a prefix.

🎨 Red-Black Tree:

Stores paper-author relationships.

Extracts a unique list of authors efficiently.

📊 Source Attribution: Every paper entry includes its source (Semantic Scholar, CrossRef, or arXiv), title, authors, citation count, DOI, and URL.

## Setup
```bash
pip install -r requirements.txt

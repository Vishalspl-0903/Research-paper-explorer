import requests

class AVLNode:
    def __init__(self, title):
        self.title = title
        self.height = 1
        self.left = None
        self.right = None

class AVLTree:
    def insert(self, root, title):
        if not root:
            return AVLNode(title)
        elif title < root.title:
            root.left = self.insert(root.left, title)
        else:
            root.right = self.insert(root.right, title)

        # Update height and rebalance the tree
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        return self.balance_tree(root)

    def get_height(self, node):
        return node.height if node else 0

    def get_balance(self, node):
        return self.get_height(node.left) - self.get_height(node.right) if node else 0

    def balance_tree(self, node):
        balance = self.get_balance(node)

        # Left Left Case
        if balance > 1 and node.left and node.left.title > node.title:
            return self.rotate_right(node)

        # Right Right Case
        if balance < -1 and node.right and node.right.title < node.title:
            return self.rotate_left(node)

        # Left Right Case
        if balance > 1 and node.left and node.left.title < node.title:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)

        # Right Left Case
        if balance < -1 and node.right and node.right.title > node.title:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)

        return node

    def rotate_left(self, z):
        y = z.right
        if not y:  # Ensure y is not None
            return z
        T2 = y.left
        y.left = z
        z.right = T2
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y

    def rotate_right(self, z):
        y = z.left
        if not y:  # Ensure y is not None
            return z
        T3 = y.right
        y.right = z
        z.left = T3
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y

    def autocomplete(self, node, prefix):
        results = []
        if node is not None:
            if node.title.startswith(prefix):
                results.append(node.title)
            results.extend(self.autocomplete(node.left, prefix))
            results.extend(self.autocomplete(node.right, prefix))
        return results

class RBNode:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.color = 'red'
        self.left = None
        self.right = None
        self.parent = None

class RBTree:
    def __init__(self):
        self.NIL = RBNode("", "")
        self.NIL.color = 'black'
        self.root = self.NIL

    def insert(self, title, author):
        new_node = RBNode(title, author)
        new_node.left = new_node.right = self.NIL
        self._insert_node(new_node)

    def _insert_node(self, new_node):
        parent = None
        current = self.root

        while current != self.NIL:
            parent = current
            if new_node.author < current.author:
                current = current.left
            else:
                current = current.right

        new_node.parent = parent
        if parent is None:
            self.root = new_node
        elif new_node.author < parent.author:
            parent.left = new_node
        else:
            parent.right = new_node

        new_node.color = 'red'
        self.fix_insertion(new_node)

    def fix_insertion(self, new_node):
        while new_node != self.root and new_node.parent.color == 'red':
            if new_node.parent == new_node.parent.parent.left:
                uncle = new_node.parent.parent.right
                if uncle.color == 'red':
                    new_node.parent.color = 'black'
                    uncle.color = 'black'
                    new_node.parent.parent.color = 'red'
                    new_node = new_node.parent.parent
                else:
                    if new_node == new_node.parent.right:
                        new_node = new_node.parent
                        self.rotate_left(new_node)
                    new_node.parent.color = 'black'
                    new_node.parent.parent.color = 'red'
                    self.rotate_right(new_node.parent.parent)
            else:
                uncle = new_node.parent.parent.left
                if uncle.color == 'red':
                    new_node.parent.color = 'black'
                    uncle.color = 'black'
                    new_node.parent.parent.color = 'red'
                    new_node = new_node.parent.parent
                else:
                    if new_node == new_node.parent.left:
                        new_node = new_node.parent
                        self.rotate_right(new_node)
                    new_node.parent.color = 'black'
                    new_node.parent.parent.color = 'red'
                    self.rotate_left(new_node.parent.parent)
        self.root.color = 'black'

    def rotate_left(self, x):
        y = x.right
        if y == self.NIL:  # Ensure y is not the NIL node
            return
        x.right = y.left
        if y.left != self.NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def rotate_right(self, x):
        y = x.left
        if y == self.NIL:  # Ensure y is not the NIL node
            return
        x.left = y.right
        if y.right != self.NIL:
            y.right.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x == x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y

    def list_unique_authors(self):
        """List unique authors from the Red-Black Tree."""
        authors = self._inorder_authors(self.root)
        return sorted(set(authors))

    def _inorder_authors(self, node):
        if node != self.NIL:
            return (self._inorder_authors(node.left) + [node.author] + self._inorder_authors(node.right))
        return []

def fetch_semantic_scholar_papers(query):
    """Fetch research papers from the Semantic Scholar API."""
    try:
        api_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=5&fields=title,authors,year,citationCount,doi"
        response = requests.get(api_url)

        if response.status_code == 200:
            papers = response.json().get('data', [])
            return [{
                'source': 'Semantic Scholar',
                'title': paper.get('title', 'Title Not Available'),
                'authors': ", ".join([author['name'] for author in paper.get('authors', [])]) or "Authors Not Available",
                'year': paper.get('year', 'Year Not Available'),
                'citation_count': paper.get('citationCount', 'Citation Count Not Available'),
                'doi': paper.get('doi'),
                'url': f"https://doi.org/{paper.get('doi')}" if paper.get('doi') else "URL Not Available"
            } for paper in papers]
        elif response.status_code == 429:  # Too Many Requests
            print("Rate limit exceeded. Please try again later.")
            return []
        else:
            print(f"Failed to fetch papers from Semantic Scholar: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching papers from Semantic Scholar: {e}")
        return []

def fetch_crossref_papers(query):
    """Fetch research papers from the CrossRef API."""
    try:
        api_url = f"https://api.crossref.org/works?query={query}&rows=5"
        response = requests.get(api_url)

        if response.status_code == 200:
            papers = response.json().get('message', {}).get('items', [])
            return [{
                'source': 'CrossRef',
                'title': paper.get('title', ['Title Not Available'])[0],
                'authors': ", ".join([f"{author['given']} {author['family']}" for author in paper.get('author', [])]) or "Authors Not Available",
                'year': paper.get('published-print', {}).get('date-parts', [[None]])[0][0] or 'Year Not Available',
                'citation_count': paper.get('is-referenced-by-count', 'Citation Count Not Available'),
                'doi': paper.get('DOI'),
                'url': f"https://doi.org/{paper.get('DOI')}" if paper.get('DOI') else "URL Not Available"
            } for paper in papers]
        else:
            print(f"Failed to fetch papers from CrossRef: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching papers from CrossRef: {e}")
        return []

def fetch_arxiv_papers(query):
    """Fetch research papers from the arXiv API."""
    try:
        api_url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=5"
        response = requests.get(api_url)

        if response.status_code == 200:
            entries = response.text.split('<entry>')
            results = []
            for entry in entries[1:]:
                title = entry.split('<title>')[1].split('</title>')[0] if '<title>' in entry else 'Title Not Available'
                author_str = entry.split('<author>')[1:]  # Skip first split for title
                authors = ', '.join([a.split('<name>')[1].split('</name>')[0] for a in author_str]) or "Authors Not Available"
                year = entry.split('<published>')[1].split('-')[0] if '<published>' in entry else 'Year Not Available'
                doi = entry.split('<id>')[1].split('</id>')[0].replace('http://arxiv.org/abs/', '') if '<id>' in entry else 'DOI Not Available'
                results.append({
                    'source': 'arXiv',
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'citation_count': 'Citation Count Not Available',
                    'doi': doi,
                    'url': f"http://arxiv.org/abs/{doi}" if doi != 'DOI Not Available' else "URL Not Available"
                })
            return results
        else:
            print(f"Failed to fetch papers from arXiv: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching papers from arXiv: {e}")
        return []

def fetch_research_papers(bname):
    """Fetch research papers from various sources and build trees."""
    papers = []

    # Fetch papers from different sources
    papers.extend(fetch_semantic_scholar_papers(bname))
    papers.extend(fetch_crossref_papers(bname))
    papers.extend(fetch_arxiv_papers(bname))

    # Initialize trees
    avl_tree_root = None
    rb_tree = RBTree()

    for paper in papers:
        title = paper['title']
        authors = paper['authors'].split(', ')
        for author in authors:
            # Insert into AVL Tree
            avl_tree_root = AVLTree().insert(avl_tree_root, title)
            # Insert into Red-Black Tree (ensuring unique authors)
            rb_tree.insert(title, author)

    return papers, avl_tree_root, rb_tree

def display_papers(papers):
    """Display the fetched research papers."""
    for i, paper in enumerate(papers):
        print(f"Paper {i + 1}:")
        print(f" Source: {paper['source']}")
        print(f" Title: {paper['title']}")
        print(f" Authors: {paper['authors']}")
        print(f" Year: {paper['year']}")
        print(f" Citation Count: {paper['citation_count']}")
        print(f" DOI: {paper['doi']}")
        print(f" URL: {paper['url']}\n")

def main():
    bname = input("Enter the title or keyword for research papers: ")
    research_papers, avl_tree_root, rb_tree = fetch_research_papers(bname)

    if research_papers:
        print("Research Papers Retrieved:")
        display_papers(research_papers)
        print("\n")

        # List unique authors using the Red-Black Tree
        unique_authors = rb_tree.list_unique_authors()
        print("Unique Authors:")
        for author in unique_authors:
            print(author)

        # Example usage of autocomplete with AVL Tree
        prefix = input("Enter prefix for autocomplete: ")
        results = AVLTree().autocomplete(avl_tree_root, prefix)

        if results:
            print("Autocomplete Results:")
            for result in results:
                print(result)
        else:
            print("No titles found with that prefix.")
    else:
        print("No papers found for the keyword.")

if __name__ == "__main__":
    main()

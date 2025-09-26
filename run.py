# Startup script for the Research Paper Explorer

import os
import sys
import subprocess
import time
import requests
from threading import Thread

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import flask_socketio
        import requests
        import numpy
        import scikit_learn
        import networkx
        import redis
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def setup_database():
    """Initialize the database"""
    try:
        from paper_manager import PaperManager
        pm = PaperManager()
        pm.init_db()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

def check_redis():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.ping()
        print("✓ Redis connection successful")
        return True
    except Exception as e:
        print(f"⚠ Redis not available: {e}")
        print("Note: Some features will be limited without Redis")
        return False

def start_worker():
    """Start the background worker"""
    try:
        subprocess.Popen([sys.executable, "worker.py"])
        print("✓ Background worker started")
        return True
    except Exception as e:
        print(f"⚠ Could not start background worker: {e}")
        return False

def start_flask_app():
    """Start the Flask application"""
    try:
        from app import app
        print("🚀 Starting Flask application...")
        print("📱 Open your browser to: http://localhost:5000")
        print("🛑 Press Ctrl+C to stop the server")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"✗ Failed to start Flask app: {e}")
        return False

def health_check():
    """Check if the application is running properly"""
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=5)
            if response.status_code == 200:
                print("✓ Application health check passed")
                return True
        except:
            time.sleep(1)
    
    print("⚠ Health check failed")
    return False

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🔬 RESEARCH PAPER EXPLORER")
    print("   Advanced Interactive Research Platform")
    print("=" * 60)
    print("📊 Features:")
    print("  • Real-time paper search across multiple sources")
    print("  • AI-powered recommendations")
    print("  • Interactive analytics dashboard")
    print("  • Collaborative research tools")
    print("  • Paper management and note-taking")
    print("=" * 60)

def main():
    """Main startup sequence"""
    print_banner()
    
    print("\n🔧 Checking system requirements...")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        return
    
    # Check Redis (optional)
    redis_available = check_redis()
    
    # Start background worker (if Redis is available)
    if redis_available:
        start_worker()
    
    print("\n✅ All systems ready!")
    print("🚀 Starting application...\n")
    
    # Start Flask app
    start_flask_app()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        print("Thank you for using Research Paper Explorer!")
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        print("Please check the error message above and try again.")
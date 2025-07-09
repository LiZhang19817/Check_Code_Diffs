#!/usr/bin/env python3

import os
import sys
import webbrowser
import time
import argparse
from threading import Timer
from dotenv import load_dotenv

def open_browser(port):
    """Open the web browser after a short delay."""
    webbrowser.open(f'http://localhost:{port}')

def main():
    """Start the web application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Quay QE Team Changes Analyzer Web Interface')
    parser.add_argument('--port', '-p', type=int, default=5000, 
                       help='Port to run the web server on (default: 5000)')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='Host to bind the web server to (default: 0.0.0.0)')
    parser.add_argument('--no-browser', action='store_true', 
                       help='Do not automatically open browser')
    args = parser.parse_args()
    
    print("🚀 Starting Quay QE Team Changes Analyzer Web Interface...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if required dependencies are installed
    try:
        import flask
        from github import Github
        print("✅ Dependencies verified")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Set environment variables for Flask
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    # Get GitHub token from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        print("✅ GitHub token found in environment")
    else:
        print("⚠️  No GitHub token found in environment")
        print("   You can set it in the web interface or create a .env file")
    
    print(f"\n🌐 Web interface will be available at:")
    print(f"   http://localhost:{args.port}")
    if args.host != '0.0.0.0':
        print(f"   http://{args.host}:{args.port}")
    print("\n📝 Features available:")
    print("   • Single branch analysis")
    print("   • Time-filtered branch comparison")
    print("   • Interactive web interface")
    print("   • Real-time GitHub data")
    
    print(f"\n🔧 Starting Flask development server on port {args.port}...")
    print("   Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Open browser after 2 seconds (unless disabled)
    if not args.no_browser:
        Timer(2.0, lambda: open_browser(args.port)).start()
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host=args.host, port=args.port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thank you for using Quay QE Team Changes Analyzer!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print(f"   Make sure port {args.port} is available")
        sys.exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Simple HTTP Server for CryptoPulse Dashboard
Opens http://localhost:8000 with live reload support
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        """Log HTTP requests"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def start_server():
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"\n🚀 Server running at {url}")
            print(f"📁 Serving files from: {DIRECTORY}")
            print(f"📊 Open index.html to view the dashboard")
            print(f"\nPress Ctrl+C to stop the server\n")
            
            # Try to open browser automatically
            try:
                webbrowser.open(url)
            except:
                print(f"Open your browser and go to {url}\n")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
    except OSError as e:
        print(f"\n✗ Error: {e}")
        if e.errno == 48:  # Port already in use
            print(f"Port {PORT} is already in use. Try killing the process or using a different port.")
        raise

if __name__ == "__main__":
    start_server()

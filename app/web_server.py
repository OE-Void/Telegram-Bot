import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'I am alive')

    def log_message(self, format, *args):
        # Silence server logs
        return

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting heartbeat server on port {port}")
    httpd.serve_forever()

def start_server_thread():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()

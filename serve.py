import http.server
import socketserver
import os

PORT = 8000
SUFFIXES = ('.html', '.json')

class GHPagesHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?', 1)[0].split('#', 1)[0]
        translated_path = self.translate_path(path)
        
        if os.path.isfile(translated_path):
            super().do_GET()
            return
        
        for suffix in SUFFIXES:
            if os.path.isfile(translated_path + suffix):
                self.path = path + suffix
                super().do_GET()
                return
            
            index_path = os.path.join(translated_path, 'index' + suffix)
            if not os.path.isfile(index_path):
                continue

            self.send_response(200)
            self.send_header('Content-Type', 'text/html' if suffix == '.html' else 'application/json')
            self.end_headers()
            with open(index_path, 'rb') as f:
                self.wfile.write(f.read())
            return

        self.send_error(404, 'File not found')
    
    def list_directory(self, path):
        self.send_error(404, 'Directory listing disabled')

with socketserver.TCPServer(('', PORT), GHPagesHandler) as httpd:
    print(f'Serving at http://localhost:{PORT}')
    httpd.serve_forever()

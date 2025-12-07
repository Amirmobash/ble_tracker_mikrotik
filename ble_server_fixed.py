# ble_server_fixed.py
import socket
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class BLEHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/live-open':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "ok",
                "server": "BLE Tracker",
                "ip": self.server.server_address[0],
                "port": self.server.server_address[1],
                "time": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            logging.info(f"GET {self.path} from {self.client_address[0]}")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"BLE Tracking Server - Use /api/live-open")
    
    def do_POST(self):
        if self.path == '/api/ingest':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                logging.info(f"📡 BLE Data from {self.client_address[0]}: MAC={data.get('mac')}, RSSI={data.get('rssi')}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    "status": "success",
                    "received": data,
                    "timestamp": datetime.now().isoformat(),
                    "gateway_ip": self.client_address[0]
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                logging.error(f"Error: {e}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())
    
    def log_message(self, format, *args):
        pass  # خودمان لاگ می‌کنیم

def get_local_ip():
    """Get local IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    HOST = '0.0.0.0'  # بسیار مهم!
    PORT = 5000
    
    server = HTTPServer((HOST, PORT), BLEHandler)
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("🚀 BLE TRACKING SERVER - ENTERPRISE EDITION")
    print("=" * 60)
    print(f"📡 Listening on: {HOST}:{PORT}")
    print(f"🏠 Local access: http://localhost:{PORT}")
    print(f"🌐 LAN access:   http://{local_ip}:{PORT}")
    print(f"📊 API endpoints:")
    print(f"   • GET  /api/live-open")
    print(f"   • POST /api/ingest")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
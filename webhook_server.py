import json
import re
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import firebase_setup

sys.stdout.reconfigure(encoding='utf-8')

PORT = int(os.getenv("WEBHOOK_PORT", "5000"))

class WebhookHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        self._set_headers(200)
        response = {
            "status": "online",
            "service": "Blinkit Stock Tracker Webhook Listener",
            "instructions": "Send HTTP POST to this endpoint with JSON body e.g. {\"message\": \"Check out this product on Blinkit - Hot Wheels Chop N Bloc Die Cast Car https://blinkit.com/prn/x/prid/787541\"}"
        }
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
            
            text_to_parse = ""
            if body:
                try:
                    data = json.loads(body)
                    text_to_parse = (
                        data.get('message') or 
                        data.get('text') or 
                        data.get('content') or 
                        data.get('url') or 
                        data.get('body') or 
                        str(data)
                    )
                except Exception:
                    text_to_parse = body

            if not text_to_parse:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "No text or message content found in POST body"}).encode('utf-8'))
                return

            print(f"\n[!] Webhook received payload: {text_to_parse[:120]}...")
            result = firebase_setup.parse_and_add_product(text_to_parse)

            if result:
                self._set_headers(200)
                response = {
                    "status": "success",
                    "message": f"Successfully registered '{result['product_name']}' (ID: {result['product_id']}) in Firebase across {result['locations_count']} location(s).",
                    "product_id": result['product_id'],
                    "product_name": result['product_name'],
                    "active_locations": result['locations_count'],
                    "monitors_created": result['monitors_created']
                }
                self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            else:
                self._set_headers(422)
                self.wfile.write(json.dumps({"error": "Could not extract Blinkit product ID from message payload"}).encode('utf-8'))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

def run_server(port=PORT):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"[+] HTTP Webhook Listener online on port {port} (http://0.0.0.0:{port}/)")
    print("Accepting incoming POST payloads to add products to Firebase...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Webhook Listener Server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()

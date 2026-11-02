import json
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse

PORT = 8080
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'krathongs.json')

# ฟังก์ชันอ่านข้อมูลกระทง
def read_krathongs():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

# ฟังก์ชันบันทึกข้อมูลกระทง
def write_krathongs(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class StarMoneyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # รองรับ CORS สำหรับการเรียก API
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        if url_parts.path == '/api/krathongs':
            data = read_krathongs()
            response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
            return
        # ให้บริการไฟล์ static (index.html, logo.png ฯลฯ)
        return super().do_GET()

    def do_POST(self):
        url_parts = urllib.parse.urlparse(self.path)
        if url_parts.path == '/api/krathongs':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                krathongs = read_krathongs()
                
                # ถ้าเป็นการล้างกระทงทั้งหมด (Reset) - ต้องตรวจสอบรหัสผ่าน 301069
                if payload.get('action') == 'reset':
                    if payload.get('pin') == '301069':
                        write_krathongs([])
                        resp = json.dumps({"status": "reset_success", "count": 0}).encode('utf-8')
                    else:
                        resp = json.dumps({"status": "error", "message": "Invalid PIN"}).encode('utf-8')
                        self.send_response(403)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.send_header('Content-Length', str(len(resp)))
                        self.end_headers()
                        self.wfile.write(resp)
                        return
                else:
                    # เพิ่มกระทงใหม่
                    krathongs.insert(0, payload)
                    write_krathongs(krathongs)
                    resp = json.dumps({"status": "success", "krathong": payload, "count": len(krathongs)}).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err_resp = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(err_resp)))
                self.end_headers()
                self.wfile.write(err_resp)
            return

        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # สร้างไฟล์เริ่มต้นว่างถ้ายังไม่มี
    if not os.path.exists(DATA_FILE):
        write_krathongs([])
    server = HTTPServer(('0.0.0.0', PORT), StarMoneyHandler)
    print(f"🌟 Star Money Server is running at http://localhost:{PORT}")
    print(f"💡 ทุกเครื่องที่เปิด URL นี้ จะมองเห็นกระทงที่คนอื่นกดปล่อยร่วมกันแบบ Real-time!")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

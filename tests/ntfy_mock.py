"""Локальна імітація ntfy.sh для тестів кооперативу через інтернет: POST /тема, GET /тема/sse.
Використання: python tests/ntfy_mock.py ПОРТ"""
import json,queue,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
subs={};cache={};lock=threading.Lock();seq=[0]
class H(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*a):pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','*');self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
    def do_OPTIONS(self):
        self.send_response(204);self.cors();self.send_header('Content-Length','0');self.end_headers()
    def do_POST(self):
        topic=self.path.strip('/').split('?')[0];n=int(self.headers.get('Content-Length') or 0);body=self.rfile.read(n).decode('utf-8')
        with lock:
            seq[0]+=1;msg={'id':str(seq[0]),'time':int(time.time()),'event':'message','topic':topic,'message':body}
            cache.setdefault(topic,[]).append(msg)
            for q in subs.get(topic,[]):q.put(msg)
        out=json.dumps(msg).encode();self.send_response(200);self.cors();self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(out)));self.end_headers();self.wfile.write(out)
    def do_GET(self):
        parts=self.path.strip('/').split('?')[0].split('/')
        if len(parts)==2 and parts[1]=='json' and 'poll=1' in self.path:
            with lock:out=''.join(json.dumps(m)+'\n' for m in cache.get(parts[0],[])).encode()
            self.send_response(200);self.cors();self.send_header('Content-Type','application/x-ndjson');self.send_header('Content-Length',str(len(out)));self.end_headers();self.wfile.write(out);return
        if len(parts)!=2 or parts[1]!='sse':
            self.send_response(404);self.cors();self.send_header('Content-Length','0');self.end_headers();return
        topic=parts[0];q=queue.Queue()
        with lock:subs.setdefault(topic,[]).append(q)
        self.send_response(200);self.cors();self.send_header('Content-Type','text/event-stream');self.send_header('Cache-Control','no-cache');self.end_headers()
        try:
            self.wfile.write(('event: open\ndata: '+json.dumps({'event':'open','topic':topic})+'\n\n').encode());self.wfile.flush()
            while True:
                try:m=q.get(timeout=15)
                except queue.Empty:self.wfile.write(b': keepalive\n\n');self.wfile.flush();continue
                self.wfile.write(('data: '+json.dumps(m)+'\n\n').encode());self.wfile.flush()
        except Exception:pass
        finally:
            with lock:subs[topic].remove(q)
if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),H).serve_forever()

"""Сервер кооперативу CAT & PIBBLE RPG.

Пересилає повідомлення між гравцями кімнати (WebSocket) і роздає саму гру.
Потрібен лише Python 3.8+ — без додаткових пакетів.

Запуск:  python coop-server.py            (порт 8787)
         python coop-server.py 9000       (інший порт)
Далі відкрий у браузері http://localhost:8787 — або дай друзям адресу тунелю (див. README.md поруч).
"""
import asyncio, base64, hashlib, json, os, pathlib, struct, sys, urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
HERE = pathlib.Path(__file__).resolve().parent
GAME = next((p for p in [HERE / 'cat-pibble-rpg.html', HERE.parent / 'cat-pibble-rpg.html'] if p.exists()), None)
GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
MAX_MSG = 4 * 1024 * 1024
rooms = {}  # код кімнати → {id гравця: Client}


class Client:
    def __init__(self, writer, room, cid):
        self.w, self.room, self.id = writer, room, cid
        self.lock = asyncio.Lock()

    async def send(self, text):
        data = text.encode('utf-8')
        n = len(data)
        head = bytes([0x81]) + (bytes([n]) if n < 126 else bytes([126]) + struct.pack('>H', n) if n < 65536 else bytes([127]) + struct.pack('>Q', n))
        try:
            async with self.lock:
                self.w.write(head + data)
                await self.w.drain()
        except Exception:
            pass


async def read_frame(r):
    """Повертає (opcode, payload) одного повного повідомлення."""
    parts, first_op = [], None
    while True:
        b1, b2 = await r.readexactly(2)
        fin, op, masked, n = b1 & 0x80, b1 & 0x0F, b2 & 0x80, b2 & 0x7F
        if n == 126: n = struct.unpack('>H', await r.readexactly(2))[0]
        elif n == 127: n = struct.unpack('>Q', await r.readexactly(8))[0]
        if n > MAX_MSG: raise ValueError('завелике повідомлення')
        mask = await r.readexactly(4) if masked else b'\0\0\0\0'
        data = bytearray(await r.readexactly(n))
        for i in range(n): data[i] ^= mask[i & 3]
        if op >= 8:  # керувальні кадри
            return op, bytes(data)
        if first_op is None: first_op = op
        parts.append(bytes(data))
        if fin: return first_op, b''.join(parts)


async def pong(w, data):
    w.write(bytes([0x8A, len(data)]) + data)
    await w.drain()


async def http_reply(w, code, ctype, body):
    w.write(f'HTTP/1.1 {code}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\nCache-Control: no-cache\r\nConnection: close\r\n\r\n'.encode() + body)
    await w.drain()
    w.close()


async def handle(r, w):
    try:
        head = await r.readuntil(b'\r\n\r\n')
    except Exception:
        w.close(); return
    lines = head.decode('latin-1').split('\r\n')
    method, target = (lines[0].split(' ') + ['', ''])[:2]
    hdr = {k.strip().lower(): v.strip() for k, v in (l.split(':', 1) for l in lines[1:] if ':' in l)}
    url = urllib.parse.urlparse(target)
    if url.path == '/ws' and hdr.get('upgrade', '').lower() == 'websocket':
        await websocket(r, w, hdr, urllib.parse.parse_qs(url.query))
    elif url.path in ('/', '/index.html', '/cat-pibble-rpg.html') and method == 'GET':
        if not GAME:
            await http_reply(w, '404 Not Found', 'text/plain; charset=utf-8', 'Поклади cat-pibble-rpg.html поруч із сервером.'.encode()); return
        html = GAME.read_text(encoding='utf-8').replace('</head>', '<script>window.CPR_SERVER=location.origin</script></head>', 1)
        await http_reply(w, '200 OK', 'text/html; charset=utf-8', html.encode('utf-8'))
    elif url.path == '/health':
        await http_reply(w, '200 OK', 'application/json', json.dumps({'ok': True, 'rooms': len(rooms)}).encode())
    else:
        await http_reply(w, '404 Not Found', 'text/plain', b'not found')


async def websocket(r, w, hdr, q):
    key = hdr.get('sec-websocket-key', '')
    acc = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    w.write(f'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {acc}\r\n\r\n'.encode())
    await w.drain()
    room = (q.get('room') or [''])[0].upper()[:8]
    cid = (q.get('id') or [''])[0][:24]
    me = Client(w, room, cid)
    members = rooms.setdefault(room, {})
    if not room or not cid:
        await me.send(json.dumps({'k': 'nope', 'msg': 'Неправильний запит до сервера.'})); w.close(); return
    if cid == 'host' and 'host' in members:
        await me.send(json.dumps({'k': 'nope', 'msg': 'Кімната з таким кодом уже є на сервері.'})); w.close(); return
    if cid != 'host' and 'host' not in members:
        await me.send(json.dumps({'k': 'nope', 'msg': 'Кімнату не знайдено на сервері. Перевір код.'})); w.close(); return
    members[cid] = me
    print(f'[{room}] + {cid} (у кімнаті: {len(members)})', flush=True)
    try:
        while True:
            op, data = await read_frame(r)
            if op == 8: break
            if op == 9: await pong(w, data); continue
            if op != 1: continue
            try:
                m = json.loads(data.decode('utf-8'))
            except Exception:
                continue
            if not isinstance(m, dict): continue
            m['from'] = cid
            text = json.dumps(m, ensure_ascii=False)
            to = m.get('to')
            if to:
                c = members.get(to)
                if c: await c.send(text)
            else:
                for oid, c in list(members.items()):
                    if oid != cid: await c.send(text)
    except Exception:
        pass
    finally:
        if members.get(cid) is me: del members[cid]
        print(f'[{room}] - {cid} (у кімнаті: {len(members)})', flush=True)
        note = {'k': 'end'} if cid == 'host' else {'k': 'bye', 'from': cid, 'to': 'host'}
        for c in list(members.values()):
            if cid == 'host' or c.id == 'host': await c.send(json.dumps(note))
        if not members: rooms.pop(room, None)
        try: w.close()
        except Exception: pass


async def main():
    srv = await asyncio.start_server(handle, '0.0.0.0', PORT)
    print(f'Сервер кооперативу працює: http://localhost:{PORT}', flush=True)
    print('Друзям через інтернет дай адресу тунелю (див. README.md). Зупинити — Ctrl+C.', flush=True)
    if not GAME: print('Увага: не знайдено cat-pibble-rpg.html — гра з сервера не відкриється, але пересилання працює.', flush=True)
    async with srv:
        await srv.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

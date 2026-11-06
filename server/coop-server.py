"""Сервер кооперативу CAT & PIBBLE RPG.

Пересилає повідомлення між гравцями кімнати (WebSocket) і роздає саму гру.
Потрібен лише Python 3.8+ — без додаткових пакетів.

Найпростіше — двічі клацнути start-server.bat (Windows): він усе підготує сам.
Вручну:  python coop-server.py --public      сервер для всіх гравців: сам відкриває тунель Cloudflare
                                             і повідомляє грі свою адресу (гра покаже «Сервер онлайн»)
         python coop-server.py               лише локально, http://localhost:8787
Параметри: --port 8787  --name "Сервер Ігоря"
"""
import argparse, asyncio, base64, hashlib, json, os, pathlib, platform, re, socket, struct, subprocess, sys, threading, time, urllib.parse, urllib.request

ap = argparse.ArgumentParser(description='Сервер кооперативу CAT & PIBBLE RPG')
ap.add_argument('port_pos', nargs='?', type=int, help=argparse.SUPPRESS)
ap.add_argument('--port', type=int, default=8787)
ap.add_argument('--public', action='store_true', help='відкрити тунель і оголосити сервер для всіх гравців')
ap.add_argument('--name', default='Сервер гри')
ap.add_argument('--announce-url', help=argparse.SUPPRESS)       # для тестів: оголосити цю адресу без тунелю
ap.add_argument('--brokers', default='broker.hivemq.com:1883,broker.emqx.io:1883,test.mosquitto.org:1883')
ap.add_argument('--ntfy', default='https://ntfy.sh/')
ARGS = ap.parse_args()
PORT = ARGS.port_pos or ARGS.port
TOPIC_MQTT = 'catpibble-rpg/v1/main-server'   # має збігатися з CONFIG.coop.mainServer у грі
TOPIC_NTFY = 'catpibble-rpg-v1-main-server'
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
    w.write(f'HTTP/1.1 {code}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\nCache-Control: no-cache\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n'.encode() + body)
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
        await http_reply(w, '200 OK', 'application/json', json.dumps({'ok': True, 'name': ARGS.name, 'rooms': len(rooms), 'players': sum(len(m) for m in rooms.values())}).encode())
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
        await me.send(json.dumps({'k': 'nope', 'code': 'noroom', 'msg': 'Кімнату не знайдено на сервері. Перевір код.'})); w.close(); return
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


# ---------- Оголошення сервера: гра знаходить його адресу сама ----------
def mqtt_publish(hostport, payload, retain=True):
    host, port = hostport.rsplit(':', 1)
    def mstr(b): return struct.pack('>H', len(b)) + b
    def pkt(h, body):
        n, rl = len(body), b''
        while True:
            d, n = n % 128, n // 128
            rl += bytes([d | (128 if n else 0)])
            if not n: break
        return bytes([h]) + rl + body
    with socket.create_connection((host, int(port)), timeout=8) as so:
        so.sendall(pkt(0x10, mstr(b'MQTT') + bytes([4, 2, 0, 30]) + mstr(('cprsrv' + os.urandom(4).hex()).encode())))
        ack = so.recv(4)
        if len(ack) < 4 or ack[0] != 0x20 or ack[3] != 0: raise OSError('брокер відмовив')
        so.sendall(pkt(0x31 if retain else 0x30, mstr(TOPIC_MQTT.encode()) + payload))
        so.sendall(bytes([0xE0, 0]))

def announce(url, online=True):
    data = json.dumps({'app': 'cpr-server', 'url': url, 'online': online, 'name': ARGS.name, 't': int(time.time())}, ensure_ascii=False).encode()
    ok = 0
    for b in [x.strip() for x in ARGS.brokers.split(',') if x.strip()]:
        try: mqtt_publish(b, data); ok += 1
        except Exception: pass
    if ARGS.ntfy:
        try:
            urllib.request.urlopen(urllib.request.Request(ARGS.ntfy.rstrip('/') + '/' + TOPIC_NTFY, data=data, method='POST'), timeout=8).read(); ok += 1
        except Exception: pass
    return ok

def cloudflared_path():
    sysname, arch = platform.system(), platform.machine().lower()
    exe = HERE / ('cloudflared.exe' if sysname == 'Windows' else 'cloudflared')
    if exe.exists(): return exe
    name = {'Windows': 'cloudflared-windows-amd64.exe', 'Linux': 'cloudflared-linux-arm64' if 'arm' in arch or 'aarch' in arch else 'cloudflared-linux-amd64'}.get(sysname)
    if not name:
        print('На цій системі встанови cloudflared вручну: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/', flush=True); return None
    print('Завантажую тунель Cloudflare (один раз, ~30 МБ)...', flush=True)
    urllib.request.urlretrieve('https://github.com/cloudflare/cloudflared/releases/latest/download/' + name, exe)
    if sysname != 'Windows': exe.chmod(0o755)
    return exe

def start_tunnel(on_url):
    exe = cloudflared_path()
    if not exe: return None
    proc = subprocess.Popen([str(exe), 'tunnel', '--no-autoupdate', '--protocol', 'http2', '--url', f'http://localhost:{PORT}'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    def reader():
        found = False
        for line in proc.stdout:
            m = re.search(r'https://[-a-z0-9]+\.trycloudflare\.com', line)
            if m and not found:
                found = True; on_url(m.group(0))
        print('Тунель зупинився.', flush=True)
    threading.Thread(target=reader, daemon=True).start()
    return proc

PUBLIC = {'url': None}
def http_ok(url):
    try:
        req = urllib.request.Request(url.rstrip('/') + '/health', headers={'User-Agent': 'catpibble-rpg-server'})
        return urllib.request.urlopen(req, timeout=10).status == 200
    except Exception:
        return False

def go_public(url):
    """Оголосити адресу (без перевірки тунелю — для тестів із --announce-url)."""
    PUBLIC['url'] = url
    n = announce(url)
    print(f'\n  СЕРВЕР ОНЛАЙН: {url}', flush=True)
    print(f'  Гравці бачать його автоматично (оголошено, сервісів: {n}). Не закривай це вікно.\n' if n else '  Увага: не вдалося оголосити адресу — перевір інтернет.\n', flush=True)

TUN = {'proc': None}
def tunnel_supervisor():
    """Відкриває тунель, перевіряє, що він справді працює з інтернету, оголошує адресу,
    а далі раз на хвилину перевіряє; якщо тунель обірвався — перезапускає його й оголошує нову адресу."""
    while True:
        found, box = threading.Event(), {}
        proc = start_tunnel(lambda u: (box.__setitem__('url', u), found.set()))
        TUN['proc'] = proc
        if not proc: return
        if not found.wait(90):
            print('Тунель не відкрився. Пробую ще раз...', flush=True); proc.terminate(); time.sleep(5); continue
        url = box['url']
        print('Перевіряю, чи сервер видно з інтернету...', flush=True)
        ok = False
        for _ in range(30):
            if http_ok(url): ok = True; break
            time.sleep(3)
        if not ok:
            print('Тунель не відповідає. Перезапускаю...', flush=True); proc.terminate(); time.sleep(3); continue
        go_public(url)
        fails, since_announce = 0, 0
        while proc.poll() is None:
            time.sleep(60); since_announce += 60
            if http_ok(url):
                fails = 0
                if since_announce >= 600: announce(url); since_announce = 0
            else:
                fails += 1
                if fails >= 2: break
        print('Тунель обірвався. Перезапускаю й оголошую нову адресу...', flush=True)
        announce(url, online=False); PUBLIC['url'] = None
        try: proc.terminate()
        except Exception: pass
        time.sleep(3)

async def main():
    srv = await asyncio.start_server(handle, '127.0.0.1', PORT)   # лише цей ПК: назовні — через тунель (без запиту брандмауера)
    print(f'Сервер кооперативу працює: http://localhost:{PORT}', flush=True)
    if not GAME: print('Увага: не знайдено cat-pibble-rpg.html — гра з сервера не відкриється, але пересилання працює.', flush=True)
    if ARGS.announce_url:
        threading.Thread(target=go_public, args=(ARGS.announce_url,), daemon=True).start()
    elif ARGS.public:
        print('Відкриваю тунель в інтернет...', flush=True)
        threading.Thread(target=tunnel_supervisor, daemon=True).start()
    else:
        print('Лише локально. Щоб сервер бачили всі гравці — запусти з --public (або start-server.bat).', flush=True)
    try:
        async with srv:
            await srv.serve_forever()
    finally:
        if PUBLIC['url']:
            print('Повідомляю гравцям, що сервер офлайн...', flush=True)
            announce(PUBLIC['url'], online=False); PUBLIC['url'] = None
        if TUN['proc']:
            try: TUN['proc'].terminate()
            except Exception: pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

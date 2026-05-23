# web_telem.py
import time

try:
    import network
    import socket
    import json
    _HAS_WIFI = True
except Exception:
    _HAS_WIFI = False


class WebTelem:
    
    def __init__(self, port=80):
        self.port = port
        self.ip = None
        self._sock = None
        self._latest = {"tag": "boot", "t": 0, "msg": "starting"}
        self._ok = False

    def start(self, ssid, password):
        if not _HAS_WIFI:
            print("[WEB] Wi-Fi not available (Pico W firmware?)")
            self._ok = False
            return False

        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)

            # Clean reconnect
            try:
                wlan.disconnect()
            except Exception:
                pass
            time.sleep_ms(300)

            print("[WEB] trying Wi-Fi:", ssid)
            wlan.connect(ssid, password)

            t0 = time.ticks_ms()
            last_status = None

            while True:
                status = wlan.status()

                if status != last_status:
                    print("[WEB] wlan status =", status)
                    last_status = status

                if wlan.isconnected():
                    break

                # Fail states on Pico W / MicroPython are often negative
                if status in (-1, -2, -3):
                    raise RuntimeError("Wi-Fi failed, status={}".format(status))

                if time.ticks_diff(time.ticks_ms(), t0) > 12000:
                    raise RuntimeError("Wi-Fi connect timeout, status={}".format(status))

                time.sleep_ms(250)

            self.ip = wlan.ifconfig()[0]
            print("[WEB] connected, IP =", self.ip)

            addr = socket.getaddrinfo("0.0.0.0", self.port)[0][-1]
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(addr)
            s.listen(1)
            s.settimeout(0.0)

            self._sock = s
            self._ok = True
            self.set({"tag": "boot", "t": time.ticks_ms(), "ip": self.ip, "msg": "server up"})
            return True

    except Exception as e:
        print("[WEB] start failed:", repr(e))
        self._ok = False
        self._sock = None
        return False

    def set(self, d):
        self._latest = d

    def tick(self):
        if not self._ok or self._sock is None:
            return

        try:
            conn, addr = self._sock.accept()
        except Exception:
            return  # no pending connection

        try:
            # Give the client a moment to actually send the HTTP request
            conn.settimeout(0.25)

            try:
                req = conn.recv(1024)
            except OSError as e:
                err = getattr(e, "errno", None)
                # MicroPython often puts errno in e.args[0]
                if err is None and e.args:
                    err = e.args[0]

                # 11 = EAGAIN (no data yet), 110 = ETIMEDOUT (client too slow / dropped)
                if err in (11, 110):
                    return
                raise

            req = req or b""
            path = self._parse_path(req)

            if path == "/favicon.ico":
                self._send(conn, 204, "text/plain", "")
                return

            if path == "/data":
                body = json.dumps(self._latest)
                self._send(conn, 200, "application/json", body)
            else:
                self._send(conn, 200, "text/html", self._page_html())

        except Exception as e:
            print("[WEB] tick handler error:", repr(e))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _parse_path(self, req_bytes):
        try:
            s = req_bytes.decode("utf-8", "ignore")
            first = s.split("\r\n")[0]
            parts = first.split(" ")
            if len(parts) >= 2:
                return parts[1]
        except Exception:
            pass
        return "/"

    def _send(self, conn, code, content_type, body_str):
        body_b = body_str.encode("utf-8")
        hdr = (
            "HTTP/1.1 {} OK\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(code, content_type, len(body_b))
        conn.send(hdr.encode("utf-8"))
        if len(body_b):
            conn.send(body_b)

    def _page_html(self):
        return """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ZillaBot Live</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 16px; }
    .card { padding: 12px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 12px; }
    .k { color: #555; }
    pre { background: #f6f6f6; padding: 10px; border-radius: 10px; overflow:auto; }
  </style>
</head>
<body>
  <h2>ZillaBot Live Telemetry</h2>
  <div class="card">
    <div><span class="k">Update:</span> <span id="t">-</span></div>
    <div><span class="k">Tag:</span> <span id="tag">-</span></div>
    <div><span class="k">Heading:</span> <span id="h">-</span></div>
    <div><span class="k">Target:</span> <span id="tgt">-</span></div>
    <div><span class="k">Error:</span> <span id="err">-</span></div>
    <div><span class="k">L/R:</span> <span id="lr">-</span></div>
    <div><span class="k">State:</span> <span id="st">-</span></div>
    <div><span class="k">Edges:</span> <span id="edges">-</span></div>
  </div>

  <div class="card">
    <div class="k">Raw JSON</div>
    <pre id="raw">{}</pre>
  </div>

<script>
async function poll(){
  try{
    const r = await fetch('/data', {cache:'no-store'});
    const j = await r.json();
    document.getElementById('raw').textContent = JSON.stringify(j, null, 2);

    document.getElementById('t').textContent = j.t ?? '-';
    document.getElementById('tag').textContent = j.tag ?? '-';
    document.getElementById('h').textContent = (j.h ?? '-');
    document.getElementById('tgt').textContent = (j.tgt ?? j.th ?? '-');
    document.getElementById('err').textContent = (j.err ?? '-');

    const L = (j.L ?? j.Lraw ?? '-');
    const R = (j.R ?? j.Rraw ?? '-');
    document.getElementById('lr').textContent = (L + ' / ' + R);

    document.getElementById('st').textContent = (j.st ?? '-');
    document.getElementById('edges').textContent = ((j.le ?? '-') + ' / ' + (j.re ?? '-'));
  }catch(e){}
  setTimeout(poll, 50);
}
poll();
</script>
</body>
</html>"""
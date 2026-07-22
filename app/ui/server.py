#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞牛IPTV播放器 - 独立Web服务器（带登录认证）
支持IP+端口独立访问，提供账号密码登录保护
"""

import os, sys, json, re, ssl, hashlib, time, subprocess, urllib.request, urllib.error, argparse, secrets, http.cookies, socket, threading
from urllib.parse import quote, unquote, unquote_plus, urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


class DualStackHTTPServer(ThreadingMixIn, HTTPServer):
    """同时监听IPv4和IPv6的多线程HTTP服务器"""
    address_family = socket.AF_INET6
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 100

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()

# ========== 配置 ==========
DEFAULT_PORT = 8899
DEFAULT_USER = "admin"
DEFAULT_PASS = "admin123"
SESSION_NAME = "iptv_session"
SESSION_TIMEOUT = 604800  # 7天

# ========== 全局变量 ==========
DATA_DIR = "/var/apps/fnnas.iptv/data"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ========== Session管理 ==========
class SessionManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.session_file = os.path.join(data_dir, "web_sessions.json")
        self.sessions = {}
        self._load()

    def _load(self):
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                self.sessions = json.load(f)
        except:
            self.sessions = {}
        # 清理过期session
        now = time.time()
        expired = [k for k, v in self.sessions.items() if now - v.get("created", 0) > SESSION_TIMEOUT]
        for k in expired:
            del self.sessions[k]
        if expired:
            self._save()

    def _save(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f)
        except:
            pass

    def create(self):
        token = secrets.token_hex(16)
        self.sessions[token] = {"created": time.time(), "last_used": time.time()}
        self._save()
        return token

    def validate(self, token):
        if not token or token not in self.sessions:
            return False
        s = self.sessions[token]
        if time.time() - s.get("created", 0) > SESSION_TIMEOUT:
            del self.sessions[token]
            self._save()
            return False
        s["last_used"] = time.time()
        return True

    def destroy(self, token):
        if token in self.sessions:
            del self.sessions[token]
            self._save()

session_mgr = None

# ========== 工具函数 ==========
def read_settings():
    settings_file = os.path.join(DATA_DIR, "settings.json")
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"epg_url": "https://epg.136605.xyz/3days.xml", "php_path": "", "logo_source": "github"}

def write_settings(data):
    try:
        settings_file = os.path.join(DATA_DIR, "settings.json")
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def get_ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# ========== HTTP请求处理器 ==========
class IPTVHandler(BaseHTTPRequestHandler):
    timeout = 30  # 单个连接超时30秒（防止线程永久阻塞）
    rbufsize = -1
    wbufsize = 0   # 无缓冲写入，流式传输

    def log_message(self, format, *args):
        pass

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_html(self, status, html):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        try:
            self.wfile.write(html.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_redirect(self, url):
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    def send_streaming_headers(self, status, content_type, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()

    def get_cookie(self, name):
        cookie_header = self.headers.get('Cookie', '')
        cookie = http.cookies.SimpleCookie(cookie_header)
        if name in cookie:
            return cookie[name].value
        return None

    def set_cookie(self, name, value, max_age=None):
        cookie = http.cookies.SimpleCookie()
        cookie[name] = value
        cookie[name]['path'] = '/'
        if max_age:
            cookie[name]['max-age'] = max_age
        self.send_header('Set-Cookie', cookie[name].OutputString())

    def clear_cookie(self, name):
        cookie = http.cookies.SimpleCookie()
        cookie[name] = ''
        cookie[name]['path'] = '/'
        cookie[name]['expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        self.send_header('Set-Cookie', cookie[name].OutputString())

    def is_authenticated(self):
        token = self.get_cookie(SESSION_NAME)
        return session_mgr.validate(token)

    def do_GET(self):
        self.route_request('GET')

    def do_POST(self):
        self.route_request('POST')

    def route_request(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parsed.query

        # 公开路径
        if path == '/login' and method == 'GET':
            return self.serve_login()
        if path == '/api/login' and method == 'POST':
            return self.handle_login()
        if path == '/api/logout':
            return self.handle_logout()
        if path == '/api/change_password' and method == 'POST':
            return self.handle_change_password()

        # M3U8订阅（公开访问，无需登录）
        if path == '/api/m3u' and method == 'GET':
            return self.handle_m3u()
        if path == '/api/ysp_proxy' and method == 'GET':
            params = {}
            if query:
                for pair in query.split('&'):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        params[unquote_plus(k)] = unquote_plus(v)
            return self.handle_ysp_proxy(params)
        if path == '/api/proxy_hls' and method == 'GET':
            params = {}
            if query:
                for pair in query.split('&'):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        params[unquote_plus(k)] = unquote_plus(v)
            return self.handle_proxy_hls(params)

        # 需要认证
        if not self.is_authenticated():
            if path.startswith('/api/'):
                return self.send_json(401, {"error": "未登录", "need_login": True})
            else:
                return self.send_redirect('/login')

        # 首页
        if path == '/' or path == '/index.html':
            return self.serve_index()

        # TS代理（二进制流，直接处理避免subprocess问题）
        if path == '/api/ts_proxy':
            params = {}
            if query:
                for pair in query.split('&'):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        params[unquote_plus(k)] = unquote_plus(v)
            return self.proxy_ts(params)

        # API -> 调用 index.cgi
        if path.startswith('/api/'):
            # 读取POST body
            body = ''
            if method in ('POST', 'PUT'):
                cl = int(self.headers.get('Content-Length', 0))
                if cl > 0:
                    body = self.rfile.read(cl).decode('utf-8')
            return self.call_cgi(path, query, method, body)

        # 静态文件
        return self.serve_static(path)

    def serve_login(self):
        if self.is_authenticated():
            return self.send_redirect('/')

        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>飞牛IPTV - 登录</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;height:100vh;display:flex;align-items:center;justify-content:center;font-family:-apple-system,"Noto Sans CJK SC","Microsoft YaHei",sans-serif}
.login-box{background:#111;padding:40px;border-radius:12px;width:90%;max-width:380px;border:1px solid #222}
.login-box h2{color:#3b82f6;font-size:20px;margin-bottom:8px;text-align:center}
.login-box p{color:#888;font-size:12px;margin-bottom:24px;text-align:center}
.input-group{margin-bottom:16px}
.input-group input{width:100%;background:#000;border:1px solid #222;color:#e2e8f0;padding:12px 14px;border-radius:8px;font-size:14px;outline:none}
.input-group input:focus{border-color:#3b82f6}
.login-btn{width:100%;background:#3b82f6;color:#fff;border:none;padding:12px;border-radius:8px;font-size:14px;cursor:pointer;transition:.2s}
.login-btn:hover{background:#2563eb}
.error{color:#ef4444;font-size:12px;margin-top:12px;text-align:center;display:none}
.tip{color:#666;font-size:11px;margin-top:16px;text-align:center}
</style>
</head>
<body>
<div class="login-box">
  <h2>飞牛IPTV</h2>
  <p>请输入账号密码登录</p>
  <form id="loginForm" onsubmit="return doLogin(event)">
    <div class="input-group">
      <input type="text" id="username" placeholder="账号" required autocomplete="username">
    </div>
    <div class="input-group">
      <input type="password" id="password" placeholder="密码" required autocomplete="current-password">
    </div>
    <button type="submit" class="login-btn">登录</button>
    <div class="error" id="error"></div>
    <div class="tip">默认账号: admin / 密码: admin123</div>
  </form>
</div>
<script>
function doLogin(e){
  e.preventDefault();
  var u=document.getElementById('username').value;
  var p=document.getElementById('password').value;
  fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'username='+encodeURIComponent(u)+'&password='+encodeURIComponent(p)})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.ok){location.href='/';}else{document.getElementById('error').textContent=d.error||'登录失败';document.getElementById('error').style.display='block';}
    });
  return false;
}
</script>
</body>
</html>'''
        self.send_html(200, html)

    def serve_index(self):
        index_path = os.path.join(SCRIPT_DIR, "index.html")
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_html(200, content)
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def serve_static(self, path):
        safe_path = os.path.normpath(path).lstrip('/')
        if safe_path.startswith('..'):
            return self.send_json(403, {"error": "Forbidden"})

        file_path = os.path.join(SCRIPT_DIR, safe_path)
        real_path = os.path.realpath(file_path)
        real_script_dir = os.path.realpath(SCRIPT_DIR)

        if not real_path.startswith(real_script_dir):
            return self.send_json(403, {"error": "Forbidden"})

        if not os.path.isfile(file_path):
            return self.send_json(404, {"error": "Not found"})

        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            ".js": "application/javascript",
            ".css": "text/css",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".html": "text/html; charset=utf-8",
            ".json": "application/json",
        }
        ct = mime_types.get(ext, "application/octet-stream")

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            try:
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_login(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else ''

        params = {}
        for pair in body.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                params[unquote_plus(k)] = unquote_plus(v)

        username = params.get('username', '')
        password = params.get('password', '')

        settings = read_settings()
        valid_user = settings.get('web_user', DEFAULT_USER)
        valid_pass = settings.get('web_pass', DEFAULT_PASS)

        if username == valid_user and password == valid_pass:
            token = session_mgr.create()
            self.send_response(200)
            self.set_cookie(SESSION_NAME, token, SESSION_TIMEOUT)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "账号或密码错误"}).encode('utf-8'))

    def handle_logout(self):
        token = self.get_cookie(SESSION_NAME)
        session_mgr.destroy(token)
        self.send_response(200)
        self.clear_cookie(SESSION_NAME)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))

    def handle_change_password(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else ''

        params = {}
        for pair in body.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                params[unquote_plus(k)] = unquote_plus(v)

        old_password = params.get('old_password', '')
        new_password = params.get('new_password', '')

        if not old_password or not new_password:
            self.send_json(200, {"ok": False, "error": "请填写完整信息"})
            return
        if len(new_password) < 4:
            self.send_json(200, {"ok": False, "error": "新密码长度至少4位"})
            return

        settings = read_settings()
        valid_user = settings.get('web_user', DEFAULT_USER)
        valid_pass = settings.get('web_pass', DEFAULT_PASS)

        if old_password != valid_pass:
            self.send_json(200, {"ok": False, "error": "原密码错误"})
            return

        settings['web_user'] = valid_user
        settings['web_pass'] = new_password
        if write_settings(settings):
            self.send_json(200, {"ok": True})
        else:
            self.send_json(200, {"ok": False, "error": "保存失败"})

    def proxy_ts(self, params):
        """TS分片代理（HTTPS下避免混合内容拦截）"""
        ts_url = params.get('url', '')
        if not ts_url or not ts_url.startswith('http'):
            self.send_streaming_headers(400, "text/plain", {})
            try:
                self.wfile.write(b"invalid url")
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        try:
            req = urllib.request.Request(ts_url, headers={
                "User-Agent": "qqlive",
                "Referer": "https://live.cctv.cn/",
                "Origin": "https://live.cctv.cn"
            })
            resp = urllib.request.urlopen(req, timeout=10, context=get_ssl_ctx())
            ct = resp.getheader("Content-Type", "video/mp2t")
            self.send_streaming_headers(200, ct, {"Cache-Control": "public, max-age=15"})
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
        except Exception as e:
            self.send_streaming_headers(502, "text/plain", {})
            try:
                self.wfile.write(("proxy error: " + str(e)[:100]).encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError):
                pass

    def handle_m3u(self):
        """生成M3U8播放列表"""
        host = self.headers.get('Host', 'localhost')
        base_url = f"http://{host}"

        # 频道映射（与ysp.php对应）
        ysp_channels = [
            ("cctv1", "CCTV-1 综合", "央视频道"),
            ("cctv2", "CCTV-2 财经", "央视频道"),
            ("cctv3", "CCTV-3 综艺", "央视频道"),
            ("cctv4", "CCTV-4 中文国际", "央视频道"),
            ("cctv5", "CCTV-5 体育", "央视频道"),
            ("cctv5p", "CCTV-5+ 体育赛事", "央视频道"),
            ("cctv6", "CCTV-6 电影", "央视频道"),
            ("cctv7", "CCTV-7 国防军事", "央视频道"),
            ("cctv8", "CCTV-8 电视剧", "央视频道"),
            ("cctv9", "CCTV-9 纪录", "央视频道"),
            ("cctv10", "CCTV-10 科教", "央视频道"),
            ("cctv11", "CCTV-11 戏曲", "央视频道"),
            ("cctv12", "CCTV-12 社会与法", "央视频道"),
            ("cctv13", "CCTV-13 新闻", "央视频道"),
            ("cctv14", "CCTV-14 少儿", "央视频道"),
            ("cctv15", "CCTV-15 音乐", "央视频道"),
            ("cctv16", "CCTV-16 奥林匹克", "央视频道"),
            ("cctv164k", "CCTV-16 4K", "央视频道"),
            ("cctv17", "CCTV-17 农业农村", "央视频道"),
            ("cctv4k", "CCTV-4K 超高清", "央视频道"),
            ("cctv8k", "CCTV-8K 超高清", "央视频道"),
            ("cgtn", "CGTN", "央视频道"),
            ("cgtnfy", "CGTN 法语", "央视频道"),
            ("cgtney", "CGTN 俄语", "央视频道"),
            ("cgtnalby", "CGTN 阿拉伯语", "央视频道"),
            ("cgtnxby", "CGTN 西班牙语", "央视频道"),
            ("cgtnwyjl", "CGTN 纪录", "央视频道"),
            ("bjws", "北京卫视", "卫视频道"),
            ("jsws", "江苏卫视", "卫视频道"),
            ("dfws", "东方卫视", "卫视频道"),
            ("zjws", "浙江卫视", "卫视频道"),
            ("hnws", "湖南卫视", "卫视频道"),
            ("hbws", "湖北卫视", "卫视频道"),
            ("gdws", "广东卫视", "卫视频道"),
            ("gxws", "广西卫视", "卫视频道"),
            ("hljws", "黑龙江卫视", "卫视频道"),
            ("hnws2", "海南卫视", "卫视频道"),
            ("cqws", "重庆卫视", "卫视频道"),
            ("szws", "深圳卫视", "卫视频道"),
            ("scws", "四川卫视", "卫视频道"),
            ("henanws", "河南卫视", "卫视频道"),
            ("fjdnhz", "东南卫视", "卫视频道"),
            ("gzhws", "贵州卫视", "卫视频道"),
            ("jxws", "江西卫视", "卫视频道"),
            ("lnws", "辽宁卫视", "卫视频道"),
            ("ahws", "安徽卫视", "卫视频道"),
            ("hbws2", "河北卫视", "卫视频道"),
            ("sdws", "山东卫视", "卫视频道"),
            ("tjws", "天津卫视", "卫视频道"),
            ("jlws", "吉林卫视", "卫视频道"),
            ("shanxiws", "陕西卫视", "卫视频道"),
            ("nxws", "宁夏卫视", "卫视频道"),
            ("nmgws", "内蒙古卫视", "卫视频道"),
            ("ynws", "云南卫视", "卫视频道"),
            ("shanxiws2", "山西卫视", "卫视频道"),
            ("qhws", "青海卫视", "卫视频道"),
            ("xzws", "西藏卫视", "卫视频道"),
            ("cetv1", "CETV-1", "卫视频道"),
            ("gxpd", "国学频道", "卫视频道"),
            ("xjws", "新疆卫视", "卫视频道"),
        ]

        lines = ["#EXTM3U"]
        for ch_id, ch_name, group in ysp_channels:
            lines.append(f'#EXTINF:-1 tvg-name="{ch_name}" group-title="{group}",{ch_name}')
            lines.append(f'{base_url}/api/ysp_proxy?id={ch_id}')

        # 添加自定义频道
        try:
            custom_file = os.path.join(DATA_DIR, "custom_channels.json")
            if os.path.isfile(custom_file):
                with open(custom_file, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
                for ch in custom:
                    name = ch.get('name', '未知频道')
                    url = ch.get('urls', [''])[0]
                    if url:
                        lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="自定义",{name}')
                        lines.append(url)
        except:
            pass

        m3u_content = '\n'.join(lines) + '\n'
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.apple.mpegurl; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(m3u_content.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            pass  # 客户端已断开，无需处理

    def rewrite_m3u_content(self, m3u_text, base_url):
        """解析M3U8内容，将所有外部URL替换为代理URL"""
        host = self.headers.get('Host', 'localhost')
        proxy_prefix = "http://" + host + "/api/proxy_hls?url="
        lines = []
        for line in m3u_text.split('\n'):
            line = line.rstrip('\r')
            stripped = line.strip()
            if stripped.startswith('#'):
                # 处理标签行中 URI="..." 的情况
                def replace_uri(m):
                    uri = m.group(1)
                    return 'URI="' + proxy_prefix + quote(uri, safe="") + '"'
                line = re.sub(r'URI="(http[^"]*)"', replace_uri, line)
                lines.append(line)
            elif stripped.startswith('http'):
                lines.append(proxy_prefix + quote(stripped, safe=''))
            elif stripped and not stripped.startswith('#'):
                # 相对URL，基于base_url转为绝对URL
                if base_url and '/' in base_url:
                    abs_url = base_url.rsplit('/', 1)[0] + '/' + stripped
                    lines.append(proxy_prefix + quote(abs_url, safe=''))
                else:
                    lines.append(line)
            else:
                lines.append(line)
        return '\n'.join(lines)

    def handle_ysp_proxy(self, params):
        """央视频道代理：调用ysp.php获取URL，返回全代理M3U8（解决第三方播放器Referer/UA问题）"""
        ch_id = params.get('id', '')
        if not ch_id:
            self.send_json(400, {"error": "缺少频道ID"})
            return
        php_bin = None
        for cmd in ['php', 'php8.2', 'php8.1', 'php8.0', 'php7.4']:
            try:
                result = subprocess.run([cmd, '-v'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    php_bin = cmd
                    break
            except:
                pass
        if not php_bin:
            self.send_json(503, {"error": "PHP环境不可用"})
            return
        ysp_script = os.path.join(SCRIPT_DIR, 'ysp.php')
        if not os.path.isfile(ysp_script):
            self.send_json(500, {"error": "ysp.php not found"})
            return
        try:
            result = subprocess.run(
                [php_bin, ysp_script, "id=" + ch_id],
                capture_output=True, text=True, timeout=30, cwd=SCRIPT_DIR
            )
            output = result.stdout.strip()
            # ysp.php通常返回一个播放URL
            if output.startswith('http'):
                real_url = output
                req = urllib.request.Request(real_url, headers={
                    "User-Agent": "qqlive",
                    "Referer": "https://live.cctv.cn/",
                    "Origin": "https://live.cctv.cn"
                })
                resp = urllib.request.urlopen(req, timeout=10, context=get_ssl_ctx())
                m3u_data = resp.read().decode('utf-8', errors='replace')
                rewritten = self.rewrite_m3u_content(m3u_data, real_url)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                self.send_header("Cache-Control", "max-age=10")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                try:
                    self.wfile.write(rewritten.encode('utf-8'))
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            # 如果输出是M3U8内容
            if output.startswith('#EXTM3U'):
                rewritten = self.rewrite_m3u_content(output, None)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                self.send_header("Cache-Control", "max-age=15")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                try:
                    self.wfile.write(rewritten.encode('utf-8'))
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            self.send_json(502, {"error": "获取播放地址失败", "detail": output[:200]})
        except subprocess.TimeoutExpired:
            self.send_json(504, {"error": "ysp.php 超时"})
        except Exception as e:
            self.send_json(500, {"error": "代理异常: " + str(e)})

    def handle_proxy_hls(self, params):
        """HLS全链路代理：代理外部M3U8和TS分片，自动处理Referer/UA
        M3U8文本：读取后重写URL返回
        TS分片：流式传输，不缓冲到内存"""
        target_url = params.get('url', '')
        if not target_url:
            self.send_json(400, {"error": "缺少url参数"})
            return
        try:
            req = urllib.request.Request(target_url, headers={
                "User-Agent": "qqlive",
                "Referer": "https://live.cctv.cn/",
                "Origin": "https://live.cctv.cn"
            })
            resp = urllib.request.urlopen(req, timeout=10, context=get_ssl_ctx())
            ct = resp.getheader("Content-Type", "")

            # 判断是否是M3U8（通过Content-Type或内容前缀）
            is_m3u8 = "mpegurl" in ct.lower() or "m3u" in ct.lower()
            first_chunk = b""

            if not is_m3u8:
                # 先读一小段判断是否是M3U8
                first_chunk = resp.read(20)
                try:
                    preview = first_chunk.decode('utf-8', errors='replace')
                    if preview.startswith('#EXTM3U'):
                        is_m3u8 = True
                except:
                    pass

            if is_m3u8:
                # M3U8文本：读取全部内容，重写URL
                remaining = resp.read()
                m3u_text = (first_chunk + remaining).decode('utf-8', errors='replace')
                rewritten = self.rewrite_m3u_content(m3u_text, target_url)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                self.send_header("Cache-Control", "max-age=10")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                try:
                    self.wfile.write(rewritten.encode('utf-8'))
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                # TS分片：流式传输，不缓冲到内存
                if not ct:
                    ct = "video/mp2t"
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Cache-Control", "public, max-age=15")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                # 先发送已读的第一段
                if first_chunk:
                    try:
                        self.wfile.write(first_chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                # 流式读取剩余数据
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        break
        except Exception as e:
            try:
                self.send_json(502, {"error": "代理失败", "detail": str(e)[:200]})
            except:
                pass

    def call_cgi(self, path, query, method, body=''):
        """通过subprocess调用index.cgi处理请求"""
        script_path = os.path.join(SCRIPT_DIR, 'index.cgi')
        if not os.path.isfile(script_path):
            return self.send_json(500, {"error": "index.cgi not found"})

        env = os.environ.copy()
        env['REQUEST_METHOD'] = method
        env['PATH_INFO'] = path
        env['QUERY_STRING'] = query
        env['SCRIPT_NAME'] = '/index.cgi'
        env['SCRIPT_FILENAME'] = script_path
        env['REMOTE_ADDR'] = self.client_address[0]
        env['SERVER_NAME'] = self.headers.get('Host', 'localhost').split(':')[0]
        env['SERVER_PORT'] = str(self.server.server_port)
        env['SERVER_PROTOCOL'] = 'HTTP/1.1'

        request_uri = path
        if query:
            request_uri += '?' + query
        env['REQUEST_URI'] = request_uri

        env['CONTENT_LENGTH'] = str(len(body.encode('utf-8')))
        env['CONTENT_TYPE'] = self.headers.get('Content-Type', '')

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                input=body,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout

            # 解析CGI输出（headers + body）
            headers_end = -1
            if '\n\n' in output:
                headers_end = output.index('\n\n')
            elif '\r\n\r\n' in output:
                headers_end = output.index('\r\n\r\n')

            if headers_end >= 0:
                headers_str = output[:headers_end]
                body_str = output[headers_end + 2:]
                # 跳过可能的额外换行
                while body_str.startswith('\n') or body_str.startswith('\r'):
                    body_str = body_str[1:]
            else:
                headers_str = output
                body_str = ''

            status = 200
            headers = {}
            for line in headers_str.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith('status:'):
                    parts = line.split(':', 1)[1].strip().split(' ')
                    if parts:
                        try:
                            status = int(parts[0])
                        except:
                            pass
                elif ':' in line:
                    k, v = line.split(':', 1)
                    headers[k.strip()] = v.strip()

            self.send_response(status)
            for k, v in headers.items():
                if k.lower() in ('transfer-encoding',):
                    continue
                self.send_header(k, v)
            self.end_headers()

            if body_str:
                try:
                    self.wfile.write(body_str.encode('utf-8'))
                except (BrokenPipeError, ConnectionResetError):
                    pass

        except subprocess.TimeoutExpired:
            self.send_json(504, {"error": "CGI timeout"})
        except Exception as e:
            self.send_json(500, {"error": "CGI error: " + str(e)})


# ========== SSL证书管理 ==========
def ensure_ssl_cert(data_dir):
    """确保SSL证书存在，不存在则生成自签名证书"""
    cert_file = os.path.join(data_dir, "server.crt")
    key_file = os.path.join(data_dir, "server.key")
    if os.path.isfile(cert_file) and os.path.isfile(key_file):
        return (cert_file, key_file)
    try:
        # 尝试使用OpenSSL生成证书
        subprocess.run([
            "openssl", "req", "-x509", "-nodes", "-days", "3650",
            "-newkey", "rsa:2048",
            "-keyout", key_file,
            "-out", cert_file,
            "-subj", "/C=CN/O=fnnas.iptv/CN=fnnas.iptv",
            "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"
        ], check=True, capture_output=True, timeout=30)
        print(f"SSL certificate generated: {cert_file}")
        return (cert_file, key_file)
    except Exception as e:
        print(f"Failed to generate SSL certificate: {e}")
        return None


# ========== 启动服务器 ==========
def write_pid(pid):
    """写入PID文件"""
    pid_file = os.path.join(DATA_DIR, "server.pid")
    try:
        with open(pid_file, 'w') as f:
            f.write(str(pid))
    except:
        pass

def remove_pid():
    """删除PID文件"""
    pid_file = os.path.join(DATA_DIR, "server.pid")
    try:
        if os.path.isfile(pid_file):
            os.remove(pid_file)
    except:
        pass

def run_server(port, data_dir):
    global DATA_DIR, session_mgr
    DATA_DIR = data_dir
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "logos"), exist_ok=True)
    session_mgr = SessionManager(DATA_DIR)

    write_pid(os.getpid())

    # 记录启动时间
    start_time = time.time()
    log_file = os.path.join(os.path.dirname(DATA_DIR), "server.log")

    def log(msg):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line)
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except:
            pass

    try:
        server = DualStackHTTPServer(('::', port), IPTVHandler)

        log(f"IPTV HTTP server started on port {port} (PID {os.getpid()})")

        # 设置超时，避免单个连接卡死整个服务
        server.timeout = 1
        log(f"Server is running. Uptime will be logged every hour.")

        while True:
            try:
                server.handle_request()
            except KeyboardInterrupt:
                break
            except SystemExit:
                break
            except Exception as e:
                # 捕获所有未处理异常，防止服务崩溃
                log(f"Request error (non-fatal): {e}")
                time.sleep(0.1)

    except Exception as e:
        log(f"Server crashed: {e}")
    finally:
        log(f"Server shutting down. Uptime: {int(time.time() - start_time)}s")
        remove_pid()


if __name__ == '__main__':
    import signal
    # 忽略SIGHUP（终端断开时不退出）
    try:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
    except:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--data-dir', default=DATA_DIR)
    args = parser.parse_args()
    run_server(args.port, args.data_dir)

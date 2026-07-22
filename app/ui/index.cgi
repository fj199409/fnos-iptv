#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞牛IPTV播放器 v2.0.2 - CGI后端
- 集成央视频(ysp.php)直播源
- 自定义频道管理
- M3U播放列表导入
- 台标代理
- EPG节目单
"""

import os, sys, json, re, ssl, hashlib, time, subprocess, urllib.request, urllib.error
from urllib.parse import quote, unquote, unquote_plus, urlencode, urlparse
import xml.etree.ElementTree as ET

# ========== CGI环境 ==========
REQUEST_URI = os.environ.get("REQUEST_URI", "")
QUERY_STRING = os.environ.get("QUERY_STRING", "")
REQUEST_METHOD = os.environ.get("REQUEST_METHOD", "GET")
PATH_INFO_ENV = os.environ.get("PATH_INFO", "")
CONTENT_LENGTH = os.environ.get("CONTENT_LENGTH", "")
CONTENT_TYPE = os.environ.get("CONTENT_TYPE", "")
IS_HTTPS = os.environ.get("HTTPS", "").lower() == "on" or os.environ.get("REQUEST_SCHEME", "").lower() == "https" or os.environ.get("SERVER_PORT", "") == "443" or os.environ.get("HTTP_X_FORWARDED_PROTO", "").lower() == "https" or os.environ.get("HTTP_X_FORWARDED_SSL", "").lower() == "on"

if not QUERY_STRING and "?" in REQUEST_URI:
    QUERY_STRING = REQUEST_URI.split("?", 1)[1]
if "index.cgi" in REQUEST_URI:
    PATH_INFO = REQUEST_URI.split("index.cgi", 1)[1]
else:
    PATH_INFO = REQUEST_URI
PATH_INFO = PATH_INFO.split("?", 1)[0]
if not PATH_INFO and PATH_INFO_ENV:
    PATH_INFO = PATH_INFO_ENV

# ========== CGI基础路径（用于构建代理URL） ==========
_REQUEST_PATH = REQUEST_URI.split("?", 1)[0]
if "index.cgi" in _REQUEST_PATH:
    CGI_BASE = _REQUEST_PATH.split("index.cgi")[0] + "index.cgi"
else:
    CGI_BASE = ""

# ========== 常量 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
YSP_PHP = os.path.join(SCRIPT_DIR, "ysp.php")
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "logos"), exist_ok=True)
except:
    DATA_DIR = "/var/apps/fnnas.iptv/data"
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, "logos"), exist_ok=True)
    except: pass

CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
EPG_CACHE_FILE = os.path.join(DATA_DIR, "epg_cache.json")

# ========== 默认频道（央视频） ==========
DEFAULT_CHANNELS = [
    {"id":"cctv1","name":"CCTV-1 综合","group":"央视频道","cnlid":"2024078201","livepid":"600001859","defn":"fhd","logo":""},
    {"id":"cctv2","name":"CCTV-2 财经","group":"央视频道","cnlid":"2024078203","livepid":"600001860","defn":"fhd","logo":""},
    {"id":"cctv3","name":"CCTV-3 综艺","group":"央视频道","cnlid":"2024078205","livepid":"600001861","defn":"fhd","logo":""},
    {"id":"cctv4","name":"CCTV-4 中文国际","group":"央视频道","cnlid":"2024078207","livepid":"600001862","defn":"fhd","logo":""},
    {"id":"cctv5","name":"CCTV-5 体育","group":"央视频道","cnlid":"2024078209","livepid":"600001863","defn":"fhd","logo":""},
    {"id":"cctv5p","name":"CCTV-5+ 体育赛事","group":"央视频道","cnlid":"2024078211","livepid":"600001864","defn":"fhd","logo":""},
    {"id":"cctv6","name":"CCTV-6 电影","group":"央视频道","cnlid":"2024078213","livepid":"600001865","defn":"fhd","logo":""},
    {"id":"cctv7","name":"CCTV-7 国防军事","group":"央视频道","cnlid":"2024078215","livepid":"600001866","defn":"fhd","logo":""},
    {"id":"cctv8","name":"CCTV-8 电视剧","group":"央视频道","cnlid":"2024078217","livepid":"600001867","defn":"fhd","logo":""},
    {"id":"cctv9","name":"CCTV-9 纪录","group":"央视频道","cnlid":"2024078219","livepid":"600001868","defn":"fhd","logo":""},
    {"id":"cctv10","name":"CCTV-10 科教","group":"央视频道","cnlid":"2024078221","livepid":"600001869","defn":"fhd","logo":""},
    {"id":"cctv11","name":"CCTV-11 戏曲","group":"央视频道","cnlid":"2024078223","livepid":"600001870","defn":"fhd","logo":""},
    {"id":"cctv12","name":"CCTV-12 社会与法","group":"央视频道","cnlid":"2024078225","livepid":"600001871","defn":"fhd","logo":""},
    {"id":"cctv13","name":"CCTV-13 新闻","group":"央视频道","cnlid":"2024078227","livepid":"600001872","defn":"fhd","logo":""},
    {"id":"cctv14","name":"CCTV-14 少儿","group":"央视频道","cnlid":"2024078229","livepid":"600001873","defn":"fhd","logo":""},
    {"id":"cctv15","name":"CCTV-15 音乐","group":"央视频道","cnlid":"2024078231","livepid":"600001874","defn":"fhd","logo":""},
    {"id":"cctv16","name":"CCTV-16 奥林匹克","group":"央视频道","cnlid":"2024078233","livepid":"600001875","defn":"fhd","logo":""},
    {"id":"cctv17","name":"CCTV-17 农业农村","group":"央视频道","cnlid":"2024078235","livepid":"600001876","defn":"fhd","logo":""},
    {"id":"cctv4k","name":"CCTV-4K 超高清","group":"央视频道","cnlid":"3000000003","livepid":"600002264","defn":"uhd","logo":""},
    {"id":"cctv8k","name":"CCTV-8K 超高清","group":"央视频道","cnlid":"3000000004","livepid":"600002265","defn":"uhd","logo":""},
    {"id":"cgtn","name":"CGTN 英语","group":"央视频道","cnlid":"2024078237","livepid":"600001877","defn":"fhd","logo":""},
    {"id":"cgtn-doc","name":"CGTN 纪录","group":"央视频道","cnlid":"2024078243","livepid":"600001880","defn":"fhd","logo":""},
    {"id":"cgtn-fra","name":"CGTN 法语","group":"央视频道","cnlid":"2024078239","livepid":"600001878","defn":"fhd","logo":""},
    {"id":"cgtn-rus","name":"CGTN 俄语","group":"央视频道","cnlid":"2024078241","livepid":"600001879","defn":"fhd","logo":""},
    {"id":"cgtn-ara","name":"CGTN 阿拉伯语","group":"央视频道","cnlid":"2024078245","livepid":"600001881","defn":"fhd","logo":""},
    {"id":"cgtn-spa","name":"CGTN 西班牙语","group":"央视频道","cnlid":"2024078247","livepid":"600001882","defn":"fhd","logo":""},
    # 风云系列
    {"id":"fy-drama","name":"风云剧场","group":"央视频道","cnlid":"2024078249","livepid":"600001883","defn":"fhd","logo":""},
    {"id":"fy-music","name":"风云音乐","group":"央视频道","cnlid":"2024078251","livepid":"600001884","defn":"fhd","logo":""},
    {"id":"fy-football","name":"风云足球","group":"央视频道","cnlid":"2024078253","livepid":"600001885","defn":"fhd","logo":""},
    {"id":"fy-golf","name":"高尔夫网球","group":"央视频道","cnlid":"2024078255","livepid":"600001886","defn":"fhd","logo":""},
    # 卫视
    {"id":"btv","name":"北京卫视","group":"卫视频道","cnlid":"2024078301","livepid":"600001900","defn":"fhd","logo":""},
    {"id":"stv","name":"东方卫视","group":"卫视频道","cnlid":"2024078303","livepid":"600001901","defn":"fhd","logo":""},
    {"id":"gdtv","name":"广东卫视","group":"卫视频道","cnlid":"2024078305","livepid":"600001902","defn":"fhd","logo":""},
    {"id":"zjtv","name":"浙江卫视","group":"卫视频道","cnlid":"2024078307","livepid":"600001903","defn":"fhd","logo":""},
    {"id":"jstv","name":"江苏卫视","group":"卫视频道","cnlid":"2024078309","livepid":"600001904","defn":"fhd","logo":""},
    {"id":"hntv","name":"湖南卫视","group":"卫视频道","cnlid":"2024078311","livepid":"600001905","defn":"fhd","logo":""},
    {"id":"hbtv","name":"湖北卫视","group":"卫视频道","cnlid":"2024078313","livepid":"600001906","defn":"fhd","logo":""},
    {"id":"sdtv","name":"山东卫视","group":"卫视频道","cnlid":"2024078315","livepid":"600001907","defn":"fhd","logo":""},
    {"id":"hntv2","name":"河南卫视","group":"卫视频道","cnlid":"2024078317","livepid":"600001908","defn":"fhd","logo":""},
    {"id":"sctv","name":"四川卫视","group":"卫视频道","cnlid":"2024078319","livepid":"600001909","defn":"fhd","logo":""},
    {"id":"litv","name":"重庆卫视","group":"卫视频道","cnlid":"2024078321","livepid":"600001910","defn":"fhd","logo":""},
    {"id":"gxtv","name":"广西卫视","group":"卫视频道","cnlid":"2024078323","livepid":"600001911","defn":"fhd","logo":""},
    {"id":"xmtv","name":"厦门卫视","group":"卫视频道","cnlid":"2024078325","livepid":"600001912","defn":"fhd","logo":""},
    {"id":"bjkids","name":"卡酷少儿","group":"卫视频道","cnlid":"2024078327","livepid":"600001913","defn":"fhd","logo":""},
    {"id":"hktv","name":"深圳卫视","group":"卫视频道","cnlid":"2024078329","livepid":"600001914","defn":"fhd","logo":""},
    {"id":"tjtv","name":"天津卫视","group":"卫视频道","cnlid":"2024078331","livepid":"600001915","defn":"fhd","logo":""},
    {"id":"ahdtv","name":"安徽卫视","group":"卫视频道","cnlid":"2024078333","livepid":"600001916","defn":"fhd","logo":""},
    {"id":"fztv","name":"东南卫视","group":"卫视频道","cnlid":"2024078335","livepid":"600001917","defn":"fhd","logo":""},
    {"id":"gntv","name":"江西卫视","group":"卫视频道","cnlid":"2024078337","livepid":"600001918","defn":"fhd","logo":""},
    {"id":"hhtv","name":"河北卫视","group":"卫视频道","cnlid":"2024078339","livepid":"600001919","defn":"fhd","logo":""},
    {"id":"sxdtv","name":"山西卫视","group":"卫视频道","cnlid":"2024078341","livepid":"600001920","defn":"fhd","logo":""},
    {"id":"lntv","name":"辽宁卫视","group":"卫视频道","cnlid":"2024078343","livepid":"600001921","defn":"fhd","logo":""},
    {"id":"jltv","name":"吉林卫视","group":"卫视频道","cnlid":"2024078345","livepid":"600001922","defn":"fhd","logo":""},
    {"id":"hltv","name":"黑龙江卫视","group":"卫视频道","cnlid":"2024078347","livepid":"600001923","defn":"fhd","logo":""},
    {"id":"hunan-jj","name":"湖南金鹰纪实","group":"卫视频道","cnlid":"2024078349","livepid":"600001924","defn":"fhd","logo":""},
    {"id":"sxtv","name":"陕西卫视","group":"卫视频道","cnlid":"2024078351","livepid":"600001925","defn":"fhd","logo":""},
    {"id":"gstv","name":"甘肃卫视","group":"卫视频道","cnlid":"2024078353","livepid":"600001926","defn":"fhd","logo":""},
    {"id":"nxtv","name":"宁夏卫视","group":"卫视频道","cnlid":"2024078355","livepid":"600001927","defn":"fhd","logo":""},
    {"id":"qhtv","name":"青海卫视","group":"卫视频道","cnlid":"2024078357","livepid":"600001928","defn":"fhd","logo":""},
    {"id":"xjtv","name":"新疆卫视","group":"卫视频道","cnlid":"2024078359","livepid":"600001929","defn":"fhd","logo":""},
    {"id":"xztv","name":"西藏卫视","group":"卫视频道","cnlid":"2024078361","livepid":"600001930","defn":"fhd","logo":""},
    {"id":"mntv","name":"内蒙古卫视","group":"卫视频道","cnlid":"2024078363","livepid":"600001931","defn":"fhd","logo":""},
    {"id":"yntv","name":"云南卫视","group":"卫视频道","cnlid":"2024078365","livepid":"600001932","defn":"fhd","logo":""},
    {"id":"gztv","name":"贵州卫视","group":"卫视频道","cnlid":"2024078367","livepid":"600001933","defn":"fhd","logo":""},
    {"id":"hainan","name":"海南卫视","group":"卫视频道","cnlid":"2024078369","livepid":"600001934","defn":"fhd","logo":""},
]

# ========== 台标URL映射 ==========
# 使用 jsdelivr 镜像（gcore 节点国内可用性高），路径为 img/（非 tv/）
LOGO_BASE = "https://gcore.jsdelivr.net/gh/wanglindl/TVlogo@main/img/"

LOGO_MAP = {
    "cctv1": LOGO_BASE+"CCTV1.png", "cctv2": LOGO_BASE+"CCTV2.png",
    "cctv3": LOGO_BASE+"CCTV3.png", "cctv4": LOGO_BASE+"CCTV4.png",
    "cctv5": LOGO_BASE+"CCTV5.png", "cctv5p": LOGO_BASE+"CCTV5plus.png",
    "cctv6": LOGO_BASE+"CCTV6.png", "cctv7": LOGO_BASE+"CCTV7.png",
    "cctv8": LOGO_BASE+"CCTV8.png", "cctv9": LOGO_BASE+"CCTV9.png",
    "cctv10": LOGO_BASE+"CCTV10.png", "cctv11": LOGO_BASE+"CCTV11.png",
    "cctv12": LOGO_BASE+"CCTV12.png", "cctv13": LOGO_BASE+"CCTV13.png",
    "cctv14": LOGO_BASE+"CCTV14.png", "cctv15": LOGO_BASE+"CCTV15.png",
    "cctv16": LOGO_BASE+"CCTV16.png", "cctv17": LOGO_BASE+"CCTV17.png",
    "cctv4k": LOGO_BASE+"CCTV4K.png", "cctv8k": LOGO_BASE+"CCTV8K.png",
    "cgtn": LOGO_BASE+"CGTN.png", "cgtn-doc": LOGO_BASE+"CGTNjilu.png",
    "cgtn-fra": LOGO_BASE+"CGTNfy.png", "cgtn-rus": LOGO_BASE+"CGTNey.png",
    "cgtn-ara": LOGO_BASE+"CGTNalby.png", "cgtn-spa": LOGO_BASE+"CGTNxbyy.png",
    "fy-drama": LOGO_BASE+"CCTVdyjc.png", "fy-music": LOGO_BASE+"CCTVfyyy.png",
    "fy-football": LOGO_BASE+"CCTVfyzq.png", "fy-golf": LOGO_BASE+"CCTVgefwq.png",
    "btv": LOGO_BASE+"Beijing.png", "stv": LOGO_BASE+"Dongfang.png",
    "gdtv": LOGO_BASE+"Guangdong.png", "zjtv": LOGO_BASE+"Zhejiang.png",
    "jstv": LOGO_BASE+"Jiangsu.png", "hntv": LOGO_BASE+"Hunan.png",
    "hbtv": LOGO_BASE+"Hubei.png", "sdtv": LOGO_BASE+"Shandong.png",
    "hntv2": LOGO_BASE+"Henan.png", "sctv": LOGO_BASE+"Sichuan.png",
    "litv": LOGO_BASE+"Chongqing.png", "gxtv": LOGO_BASE+"Guangxi.png",
    "xmtv": LOGO_BASE+"Xiamen.png", "bjkids": LOGO_BASE+"kakushaoer.png",
    "hktv": LOGO_BASE+"Shenzhen.png", "tjtv": LOGO_BASE+"Tianjin.png",
    "ahdtv": LOGO_BASE+"Anhui.png", "fztv": LOGO_BASE+"Dongnan.png",
    "gntv": LOGO_BASE+"Jiangxi.png", "hhtv": LOGO_BASE+"Hebei.png",
    "sxdtv": LOGO_BASE+"Shanxi.png", "lntv": LOGO_BASE+"Liaoning.png",
    "jltv": LOGO_BASE+"Jilin.png", "hltv": LOGO_BASE+"Heilongjiang.png",
    "gstv": LOGO_BASE+"Gansu.png", "nxtv": LOGO_BASE+"Ningxia.png",
    "qhtv": LOGO_BASE+"Qinghai.png", "xjtv": LOGO_BASE+"Xinjiang.png",
    "xztv": LOGO_BASE+"Xizang.png", "mntv": LOGO_BASE+"Neimeng.png",
    "yntv": LOGO_BASE+"Yunnan.png", "gztv": LOGO_BASE+"Guizhou.png",
    "hainan": LOGO_BASE+"Hainan.png",
}

# ========== HTTP响应 ==========
def send_json(status, data):
    print(f"Status: {status}")
    print("Content-Type: application/json; charset=utf-8")
    print("Cache-Control: no-cache, no-store, must-revalidate")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS")
    print("Access-Control-Allow-Headers: *")
    print()
    sys.stdout.flush()
    body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    sys.stdout.buffer.write(body.encode('utf-8'))
    sys.stdout.buffer.flush()

def send_redirect(url):
    print("Status: 302")
    print(f"Location: {url}")
    print("Access-Control-Allow-Origin: *")
    print()
    sys.stdout.flush()

def send_html(html):
    print("Status: 200")
    print("Content-Type: text/html; charset=utf-8")
    print("Access-Control-Allow-Origin: *")
    print()
    sys.stdout.flush()
    sys.stdout.buffer.write(html.encode('utf-8'))
    sys.stdout.buffer.flush()

def send_streaming_headers(status, content_type, extra_headers=None):
    print(f"Status: {status}")
    print(f"Content-Type: {content_type}")
    print("Access-Control-Allow-Origin: *")
    if extra_headers:
        for k, v in extra_headers.items(): print(f"{k}: {v}")
    print()
    sys.stdout.flush()

def write_chunk(data):
    if isinstance(data, str): sys.stdout.buffer.write(data.encode('utf-8'))
    else: sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()

# ========== 请求体/参数 ==========
def get_request_body():
    if CONTENT_LENGTH:
        try:
            cl = int(CONTENT_LENGTH)
            if cl > 0: return sys.stdin.read(cl)
        except: pass
    try:
        import select
        if select.select([sys.stdin], [], [], 0.1)[0]:
            data = sys.stdin.read()
            if data: return data
    except: pass
    return ''

def get_params():
    params = {}
    if QUERY_STRING:
        for pair in QUERY_STRING.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[unquote_plus(k)] = unquote_plus(v)
    if REQUEST_METHOD in ("POST", "PUT", "DELETE"):
        body = get_request_body()
        if body:
            if CONTENT_TYPE and "json" in CONTENT_TYPE.lower():
                try:
                    j = json.loads(body)
                    if isinstance(j, dict): params.update(j)
                except: pass
            else:
                for pair in body.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        params[unquote_plus(k)] = unquote_plus(v)
    return params

def get_ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def http_get(url, headers=None, raw=False, timeout=20):
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        if headers:
            for k, v in headers.items(): req.add_header(k, v)
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=get_ssl_ctx()))
        resp = opener.open(req, timeout=timeout)
        content = resp.read()
        if raw: return content.decode('utf-8', errors='ignore')
        return json.loads(content.decode('utf-8', errors='ignore'))
    except Exception as e:
        if raw: return ''
        return {"error": str(e)}

# ========== 数据管理 ==========
def read_channels():
    try:
        channels = json.load(open(CHANNELS_FILE, 'r', encoding='utf-8'))
        ysp = channels.get("ysp", [])
        # 检测旧版分组数据，自动重置
        old_groups = {"港澳", "央视付费"}
        if ysp and any(ch.get("group") in old_groups for ch in ysp):
            channels["ysp"] = DEFAULT_CHANNELS
            write_channels(channels)
        return channels
    except:
        # 初始化默认频道
        channels = {"ysp": DEFAULT_CHANNELS, "custom": []}
        write_channels(channels)
        return channels

def write_channels(data):
    try:
        with open(CHANNELS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except: return False

def read_settings():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except:
        return {"epg_url": "https://epg.136605.xyz/3days.xml", "php_path": "", "logo_source": "github"}

def write_settings(data):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except: return False

# ========== PHP调用 ==========
_PHP_CACHE = None  # 进程内缓存（单次请求内复用）
# 飞牛OS常见PHP路径（Docker容器映射、WebOps、第三方安装）
PHP_SEARCH_PATHS = [
    "/usr/bin/php", "/usr/local/bin/php", "/usr/bin/php8.2", "/usr/bin/php8.1",
    "/usr/bin/php8.0", "/usr/bin/php7.4", "/usr/local/bin/php8.2",
    # WebOps / 宝塔 / 1Panel 等常见安装路径
    "/www/server/php/82/bin/php", "/www/server/php/81/bin/php", "/www/server/php/80/bin/php",
    "/opt/1panel/runtime/php/php", "/opt/php/bin/php",
]

def find_php():
    """查找PHP可执行文件，结果缓存到 settings.json 避免每次查找"""
    global _PHP_CACHE
    if _PHP_CACHE is not None:
        return _PHP_CACHE if _PHP_CACHE != "" else None
    settings = read_settings()
    # 优先使用用户手动配置的路径
    cached = settings.get("php_path", "")
    if cached and os.path.isfile(cached):
        _PHP_CACHE = cached
        return cached
    # 方式1: which 命令查找
    for cmd in ["php", "php-cgi", "php8.2", "php8.1", "php8.0", "php7.4"]:
        try:
            result = subprocess.run(["which", cmd], capture_output=True, text=True, timeout=3)
            if result.returncode == 0 and result.stdout.strip():
                php_bin = result.stdout.strip()
                if os.path.isfile(php_bin):
                    settings["php_path"] = php_bin
                    write_settings(settings)
                    _PHP_CACHE = php_bin
                    return php_bin
        except: pass
    # 方式2: 检查常见安装路径
    for path in PHP_SEARCH_PATHS:
        if os.path.isfile(path):
            try:
                result = subprocess.run([path, "-v"], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    settings["php_path"] = path
                    write_settings(settings)
                    _PHP_CACHE = path
                    return path
            except: pass
    # 方式3: 通过Docker查找运行中的PHP容器
    try:
        result = subprocess.run(
            ["docker", "exec", "php", "which", "php"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            # 测试 docker exec 是否可以正常运行 PHP
            test = subprocess.run(
                ["docker", "exec", "php", "php", "-v"],
                capture_output=True, text=True, timeout=5
            )
            if test.returncode == 0:
                php_bin = "docker:php"  # 特殊标记，call_ysp 中识别
                settings["php_path"] = php_bin
                write_settings(settings)
                _PHP_CACHE = php_bin
                return php_bin
    except: pass
    _PHP_CACHE = ""
    return None

# CGI频道ID -> ysp.php频道ID 映射表
PHP_ID_MAP = {
    "btv": "bjws", "stv": "dfws", "gdtv": "gdws", "zjtv": "zjws",
    "jstv": "jsws", "hntv": "hnws", "hbtv": "hbws", "sdtv": "sdws",
    "hntv2": "henanws", "sctv": "scws", "litv": "cqws", "gxtv": "gxws",
    "hktv": "szws", "tjtv": "tjws", "ahdtv": "ahws", "fztv": "fjdnhz",
    "gntv": "jxws", "hhtv": "hbws2", "sxdtv": "shanxiws2", "sxtv": "shanxiws",
    "lntv": "lnws", "jltv": "jlws", "hltv": "hljws", "gstv": "nxws",
    "nxtv": "nxws", "qhtv": "qhws", "xztv": "xzws", "mntv": "nmgws",
    "yntv": "ynws", "gztv": "gzhws", "hainan": "hnws2", "xjtv": "xjws",
    "cgtn-doc": "cgtnwyjl", "cgtn-fra": "cgtnfy", "cgtn-rus": "cgtney",
    "cgtn-ara": "cgtnalby", "cgtn-spa": "cgtnxby",
    "fy-drama": "cctvdyjc", "fy-music": "cctvfyyy", "fy-football": "cctvfyzq",
    "fy-golf": "cctvgeqwq", "xmtv": "cetv1",
}

def call_ysp(channel_id, playseek=""):
    """调用ysp.php获取直播流"""
    # 转换CGI频道ID为ysp.php频道ID
    php_channel_id = PHP_ID_MAP.get(channel_id, channel_id)
    php_bin = find_php()
    if not php_bin:
        return {"error": "PHP未安装，请在设置中配置PHP路径或安装php-cli", "php_found": False}
    
    if not os.path.isfile(YSP_PHP):
        return {"error": "ysp.php文件不存在", "php_found": True}
    
    # 构建PHP CGI环境
    env = os.environ.copy()
    query = f"id={php_channel_id}"
    if playseek: query += f"&playseek={playseek}"
    env["QUERY_STRING"] = query
    env["REQUEST_METHOD"] = "GET"
    env["SCRIPT_FILENAME"] = YSP_PHP
    env["SCRIPT_NAME"] = "/ysp.php"
    env["REDIRECT_STATUS"] = "1"
    
    # CLI模式下$_GET为空，把query参数作为命令行参数传递
    # ysp.php开头会用 parse_str(implode('&', array_slice($argv,1)), $_GET) 解析
    cli_args = [f"id={php_channel_id}"]
    if playseek: cli_args.append(f"playseek={playseek}")
    
    try:
        result = subprocess.run([php_bin, "-f", YSP_PHP] + cli_args, env=env, capture_output=True, timeout=30, text=True)
        output = result.stdout.strip()
        stderr = result.stderr.strip()
        
        # PHP CGI可能输出headers
        if "\n\n" in output:
            headers_part, body = output.split("\n\n", 1)
            output = body.strip()
        
        # 检查是否是M3U8内容
        if output.startswith("#EXTM3U"):
            return {"m3u8_content": output, "php_found": True}
        
        # 检查是否是URL（302跳转目标）
        if output.startswith("http"):
            return {"url": output.strip(), "php_found": True}
        
        # 尝试解析JSON
        try:
            j = json.loads(output)
            return {"data": j, "php_found": True, "raw": output[:500]}
        except:
            pass
        
        return {"error": "PHP返回异常", "php_found": True, "output": output[:500], "stderr": stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"error": "PHP执行超时", "php_found": True}
    except Exception as e:
        return {"error": str(e), "php_found": True}

# ========== M3U解析 ==========
def parse_m3u(content):
    """解析M3U播放列表"""
    channels = []
    lines = content.strip().split("\n")
    current = None
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            # 解析属性
            name = ""
            logo = ""
            group = ""
            # 提取name
            if "," in line:
                name = line.split(",")[-1].strip()
            # 提取tvg-logo
            m = re.search(r'tvg-logo="([^"]*)"', line)
            if m: logo = m.group(1)
            # 提取group-title
            m = re.search(r'group-title="([^"]*)"', line)
            if m: group = m.group(1)
            current = {"name": name, "logo": logo, "group": group or "导入", "url": ""}
        elif line and not line.startswith("#") and current:
            current["url"] = line
            current["id"] = "custom_" + hashlib.md5(line.encode()).hexdigest()[:8]
            channels.append(current)
            current = None
    return channels

# ========== EPG ==========
def fetch_epg(url):
    """获取EPG数据"""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=get_ssl_ctx()))
        resp = opener.open(req, timeout=30)
        content = resp.read().decode('utf-8', errors='ignore')
        return content
    except Exception as e:
        return None

def parse_epg(xml_text, channel_ids=None):
    """解析EPG XML，返回精简的节目单"""
    programmes = []
    try:
        root = ET.fromstring(xml_text)
        # 构建频道ID -> 频道名称映射表
        ch_map = {}
        for ch in root.findall('.//channel'):
            ch_id = ch.get('id', '')
            names = ch.findall('display-name')
            if names:
                ch_map[ch_id] = names[0].text or ''
        for prog in root.findall('.//programme'):
            ch_id = prog.get('channel', '')
            # 用频道名称替换数字ID，便于前端匹配
            ch_name = ch_map.get(ch_id, ch_id)
            start = prog.get('start', '').split(' ')[0]
            stop = prog.get('stop', '').split(' ')[0]
            title_el = prog.find('title')
            title = title_el.text if title_el is not None else ''
            desc_el = prog.find('desc')
            desc = desc_el.text if desc_el is not None else ''
            programmes.append({
                "channel": ch_name, "start": start, "stop": stop,
                "title": title, "desc": desc or ""
            })
            if len(programmes) >= 8000: break  # 限制数量
    except Exception as e:
        return {"error": str(e)}
    return programmes

def get_epg_cache():
    try:
        with open(EPG_CACHE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"data": [], "updated": 0}

def save_epg_cache(data):
    try:
        with open(EPG_CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)
    except: pass

# ========== 直播流缓存 ==========
STREAM_CACHE_FILE = os.path.join(DATA_DIR, "stream_cache.json")
STREAM_CACHE_TTL = 5  # M3U8内容缓存秒数（5秒平衡新鲜度和PHP调用开销，避免频繁执行PHP进程）

def get_stream_cache():
    try:
        with open(STREAM_CACHE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_stream_cache(data):
    try:
        with open(STREAM_CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)
    except: pass

def get_cached_stream(ch_id, playseek=""):
    """获取缓存的直播流（未过期才返回）"""
    cache = get_stream_cache()
    key = ch_id + "|" + playseek
    entry = cache.get(key)
    if entry and time.time() - entry.get("ts", 0) < STREAM_CACHE_TTL:
        return entry
    return None

def set_cached_stream(ch_id, playseek, result):
    """缓存直播流结果"""
    cache = get_stream_cache()
    key = ch_id + "|" + playseek
    cache[key] = {"ts": time.time(), "result": result}
    # 清理过期条目
    now = time.time()
    cache = {k: v for k, v in cache.items() if now - v.get("ts", 0) < STREAM_CACHE_TTL * 3}
    save_stream_cache(cache)

# ========== Logo代理 ==========
def proxy_logo(url):
    """代理台标图片，首次下载后缓存到本地"""
    try:
        # 基于URL哈希生成本地缓存文件名
        cache_name = hashlib.md5(url.encode()).hexdigest() + ".png"
        cache_path = os.path.join(DATA_DIR, "logos", cache_name)
        
        # 命中本地缓存直接返回
        if os.path.isfile(cache_path):
            with open(cache_path, 'rb') as f:
                content = f.read()
            send_streaming_headers(200, "image/png", {"Cache-Control": "public, max-age=604800"})
            write_chunk(content)
            return
        
        if url.startswith("http"):
            # github raw 自动转换为 jsdelivr 镜像以提高国内可用性
            fetch_url = url
            if "raw.githubusercontent.com" in url:
                m = re.match(r'https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)', url)
                if m:
                    fetch_url = "https://gcore.jsdelivr.net/gh/%s/%s@%s/%s" % (m.group(1), m.group(2), m.group(3), m.group(4))
            req = urllib.request.Request(fetch_url)
            req.add_header("User-Agent", "Mozilla/5.0")
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=get_ssl_ctx()))
            resp = opener.open(req, timeout=15)
            content = resp.read()
            ct = resp.headers.get("Content-Type", "image/png")
            # 写入本地缓存
            try:
                with open(cache_path, 'wb') as f: f.write(content)
            except: pass
            send_streaming_headers(200, ct, {"Cache-Control": "public, max-age=604800"})
            write_chunk(content)
        else:
            # 本地文件
            logo_path = os.path.join(DATA_DIR, "logos", os.path.basename(url))
            if os.path.isfile(logo_path):
                with open(logo_path, 'rb') as f:
                    content = f.read()
                send_streaming_headers(200, "image/png", {"Cache-Control": "public, max-age=86400"})
                write_chunk(content)
            else:
                send_json(404, {"error": "Logo not found"})
    except Exception as e:
        send_json(500, {"error": str(e)})

# ========== 主路由 ==========
def main():
    # 首页
    if PATH_INFO == "/" or PATH_INFO == "" or PATH_INFO == "/index.cgi":
        html_path = os.path.join(SCRIPT_DIR, "index.html")
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                send_html(f.read())
        except:
            send_json(500, {"error": "index.html not found"})
        sys.exit(0)

    # ===== 频道列表 =====
    if PATH_INFO == "/api/channels":
        channels = read_channels()
        # 补充台标URL
        for ch in channels.get("ysp", []):
            if not ch.get("logo"):
                ch["logo"] = LOGO_MAP.get(ch["id"], "")
            ch["logo_url"] = ch["logo"] if ch["logo"] else (LOGO_MAP.get(ch["id"], ""))
        for ch in channels.get("custom", []):
            if ch.get("logo"):
                ch["logo_url"] = ch["logo"]
        send_json(200, channels)
        sys.exit(0)

    # ===== 添加自定义频道 =====
    if PATH_INFO == "/api/channels/add" and REQUEST_METHOD == "POST":
        params = get_params()
        channels = read_channels()
        new_ch = {
            "id": "custom_" + hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
            "name": params.get("name", ""),
            "group": params.get("group", "自定义"),
            "url": params.get("url", ""),
            "logo": params.get("logo", ""),
            "type": "custom"
        }
        if not new_ch["name"] or not new_ch["url"]:
            send_json(400, {"error": "频道名称和URL不能为空"}); sys.exit(0)
        channels["custom"].append(new_ch)
        write_channels(channels)
        send_json(200, {"ok": True, "channel": new_ch})
        sys.exit(0)

    # ===== 删除频道 =====
    if PATH_INFO.startswith("/api/channels/delete/") and REQUEST_METHOD == "POST":
        ch_id = PATH_INFO[len("/api/channels/delete/"):]
        channels = read_channels()
        channels["custom"] = [c for c in channels["custom"] if c["id"] != ch_id]
        write_channels(channels)
        send_json(200, {"ok": True})
        sys.exit(0)

    # ===== 获取直播流URL =====
    if PATH_INFO == "/api/stream":
        params = get_params()
        ch_id = params.get("id", "")
        playseek = params.get("playseek", "")
        
        channels = read_channels()
        channel = None
        for ch in channels.get("ysp", []):
            if ch["id"] == ch_id:
                channel = ch; break
        for ch in channels.get("custom", []):
            if ch["id"] == ch_id:
                channel = ch; break
        
        if not channel:
            send_json(404, {"error": "频道不存在"}); sys.exit(0)
        
        # 自定义频道直接返回URL
        if channel.get("type") == "custom" or channel.get("url"):
            send_json(200, {"url": channel["url"], "type": "custom"})
            sys.exit(0)
        
        # 央视频频道：先检查PHP是否可用
        php_bin = find_php()
        if not php_bin:
            send_json(500, {"error": "PHP未安装，请在设置中点击一键安装PHP", "need_php": True})
            sys.exit(0)
        
        # 返回 /api/m3u8 代理URL
        proxy_url = CGI_BASE + "/api/m3u8?id=" + quote(ch_id, safe='') + "&playseek=" + quote(playseek, safe='')
        send_json(200, {"url": proxy_url, "type": "ysp"})
        sys.exit(0)

    # ===== M3U8代理（支持直播列表刷新 + 短缓存减少PHP调用） =====
    if PATH_INFO == "/api/m3u8":
        params = get_params()
        ch_id = params.get("id", "")
        playseek = params.get("playseek", "")
        
        # 10秒短缓存，减少PHP调用频率
        cached = get_cached_stream(ch_id, playseek)
        if cached and time.time() - cached.get("ts", 0) < STREAM_CACHE_TTL:
            m3u8_content = cached.get("result", {}).get("m3u8", "")
        else:
            result = call_ysp(ch_id, playseek)
            if result.get("m3u8_content"):
                m3u8_content = result["m3u8_content"]
                set_cached_stream(ch_id, playseek, {"m3u8": m3u8_content, "type": "ysp"})
            elif result.get("url"):
                send_redirect(result["url"])
                sys.exit(0)
            else:
                send_json(500, result)
                sys.exit(0)
        
        # 验证返回内容是否为有效的M3U8
        if not m3u8_content or not m3u8_content.strip().startswith("#EXTM3U"):
            send_streaming_headers(500, "application/json", {})
            write_chunk(json.dumps({"error": "获取直播流失败", "detail": (m3u8_content or "")[:300]}))
            sys.exit(0)
        
        # HTTPS下将TS分片URL代理到CGI，避免浏览器混合内容拦截
        is_https = IS_HTTPS or params.get("https") == "1"
        if is_https:
            import re as _re
            def rewrite_ts_url(match):
                ts_url = match.group(0)
                return CGI_BASE + "/api/ts_proxy?url=" + quote(ts_url, safe='')
            m3u8_content = _re.sub(r'^(https?://[^\s]+)$', rewrite_ts_url, m3u8_content, flags=_re.MULTILINE)
        send_streaming_headers(200, "application/vnd.apple.mpegurl", {"Cache-Control": "no-cache"})
        write_chunk(m3u8_content)
        sys.exit(0)

    # ===== TS分片代理（HTTPS下避免混合内容拦截） =====
    if PATH_INFO == "/api/ts_proxy":
        params = get_params()
        ts_url = params.get("url", "")
        if not ts_url or not ts_url.startswith("http"):
            send_streaming_headers(400, "text/plain", {})
            write_chunk("invalid url")
            sys.exit(0)
        try:
            req = urllib.request.Request(ts_url, headers={
                "User-Agent": "qqlive",
                "Referer": "https://live.cctv.cn/",
                "Origin": "https://live.cctv.cn"
            })
            resp = urllib.request.urlopen(req, timeout=15, context=get_ssl_ctx())
            ct = resp.getheader("Content-Type", "video/mp2t")
            send_streaming_headers(200, ct, {"Cache-Control": "public, max-age=15"})
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                write_chunk(chunk)
            sys.exit(0)
        except Exception as e:
            send_streaming_headers(502, "text/plain", {})
            write_chunk("proxy error: " + str(e)[:100])
            sys.exit(0)

    # ===== 导入M3U播放列表 =====
    if PATH_INFO == "/api/import_m3u" and REQUEST_METHOD == "POST":
        params = get_params()
        m3u_content = params.get("content", "")
        m3u_url = params.get("url", "")
        
        if m3u_url and not m3u_content:
            m3u_content = http_get(m3u_url, raw=True, timeout=30)
        
        if not m3u_content:
            send_json(400, {"error": "M3U内容为空"}); sys.exit(0)
        
        imported = parse_m3u(m3u_content)
        channels = read_channels()
        for ch in imported:
            ch["type"] = "custom"
            channels["custom"].append(ch)
        write_channels(channels)
        send_json(200, {"ok": True, "imported": len(imported), "total_custom": len(channels["custom"])})
        sys.exit(0)

    # ===== EPG节目单 =====
    if PATH_INFO == "/api/epg":
        params = get_params()
        force = params.get("force", "")
        settings = read_settings()
        epg_url = params.get("url", settings.get("epg_url", ""))
        
        cache = get_epg_cache()
        # 缓存6小时
        if not force and cache.get("data") and time.time() - cache.get("updated", 0) < 21600:
            send_json(200, {"data": cache["data"], "updated": cache["updated"], "cached": True})
            sys.exit(0)
        
        if not epg_url:
            epg_url = "https://epg.136605.xyz/3days.xml"
        
        xml_text = fetch_epg(epg_url)
        if not xml_text:
            send_json(500, {"error": "EPG获取失败", "url": epg_url})
            sys.exit(0)
        
        programmes = parse_epg(xml_text)
        cache = {"data": programmes, "updated": time.time(), "url": epg_url}
        save_epg_cache(cache)
        send_json(200, {"data": programmes, "updated": cache["updated"], "cached": False})
        sys.exit(0)

    # ===== 台标代理 =====
    if PATH_INFO.startswith("/api/logo"):
        params = get_params()
        url = params.get("url", "")
        ch_id = params.get("id", "")
        if url:
            proxy_logo(url)
        elif ch_id:
            logo_url = LOGO_MAP.get(ch_id, "")
            if logo_url:
                proxy_logo(logo_url)
            else:
                send_json(404, {"error": "No logo for channel"})
        else:
            send_json(400, {"error": "Missing url or id"})
        sys.exit(0)

    # ===== 设置 =====
    if PATH_INFO == "/api/settings":
        if REQUEST_METHOD == "POST":
            params = get_params()
            settings = read_settings()
            for k in ["epg_url", "php_path", "logo_source"]:
                if k in params: settings[k] = params[k]
            write_settings(settings)
            send_json(200, {"ok": True, "settings": settings})
        else:
            settings = read_settings()
            php_bin = find_php()
            settings["php_found"] = php_bin is not None
            settings["php_binary"] = php_bin or ""
            send_json(200, settings)
        sys.exit(0)

    # ===== 修改登录密码（CGI模式和独立服务器共用） =====
    if PATH_INFO == "/api/change_password" and REQUEST_METHOD == "POST":
        params = get_params()
        old_password = params.get("old_password", "")
        new_password = params.get("new_password", "")
        if not old_password or not new_password:
            send_json(200, {"ok": False, "error": "请填写完整信息"})
            sys.exit(0)
        if len(new_password) < 4:
            send_json(200, {"ok": False, "error": "新密码长度至少4位"})
            sys.exit(0)
        settings = read_settings()
        valid_pass = settings.get("web_pass", "admin123")
        if old_password != valid_pass:
            send_json(200, {"ok": False, "error": "原密码错误"})
            sys.exit(0)
        settings["web_user"] = settings.get("web_user", "admin")
        settings["web_pass"] = new_password
        write_settings(settings)
        send_json(200, {"ok": True})
        sys.exit(0)

    # ===== 状态检查 =====
    if PATH_INFO == "/api/status":
        php_bin = find_php()
        channels = read_channels()
        send_json(200, {
            "php_found": php_bin is not None,
            "php_binary": php_bin or "",
            "ysp_exists": os.path.isfile(YSP_PHP),
            "ysp_channels": len(channels.get("ysp", [])),
            "custom_channels": len(channels.get("custom", [])),
            "version": "2.0.2"
        })
        sys.exit(0)

    # ===== 一键安装PHP =====
    if PATH_INFO == "/api/install_php" and REQUEST_METHOD == "POST":
        import shutil
        # 检查是否已安装
        existing = find_php()
        if existing:
            send_json(200, {"ok": True, "message": "PHP已安装: " + existing, "php_path": existing})
            sys.exit(0)
        # 检查apt-get是否可用（fnOS基于Debian）
        apt = shutil.which("apt-get")
        if not apt:
            send_json(500, {"error": "系统不支持apt-get，请手动安装PHP CLI", "suggestion": "在飞牛应用商店安装WebOps或手动安装php-cli"})
            sys.exit(0)
        try:
            # 安装php-cli及必要扩展（curl用于HTTP请求，mbstring用于字符串处理）
            result = subprocess.run(
                [apt, "install", "-y", "php-cli", "php-curl", "php-mbstring", "php-xml"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                # 尝试先update再install
                subprocess.run([apt, "update"], capture_output=True, text=True, timeout=60)
                result = subprocess.run(
                    [apt, "install", "-y", "php-cli", "php-curl", "php-mbstring", "php-xml"],
                    capture_output=True, text=True, timeout=120
                )
            if result.returncode == 0:
                # 清除缓存的PHP路径，重新查找
                globals()["_PHP_CACHE"] = None
                settings = read_settings()
                settings.pop("php_path", None)
                write_settings(settings)
                php_bin = find_php()
                if php_bin:
                    send_json(200, {"ok": True, "message": "PHP安装成功: " + php_bin, "php_path": php_bin})
                else:
                    send_json(200, {"ok": True, "message": "PHP安装完成，但未找到可执行文件", "output": result.stdout[-500:]})
            else:
                send_json(500, {"error": "PHP安装失败", "stderr": result.stderr[-500:], "stdout": result.stdout[-500:]})
        except subprocess.TimeoutExpired:
            send_json(500, {"error": "安装超时，请稍后重试或在SSH中手动执行: apt-get install -y php-cli"})
        except Exception as e:
            send_json(500, {"error": "安装异常: " + str(e)})
        sys.exit(0)

    # ===== 卸载PHP =====
    if PATH_INFO == "/api/uninstall_php" and REQUEST_METHOD == "POST":
        import shutil
        existing = find_php()
        if not existing:
            send_json(200, {"ok": True, "message": "PHP未安装，无需卸载"})
            sys.exit(0)
        apt = shutil.which("apt-get")
        if not apt:
            send_json(500, {"error": "系统不支持apt-get"})
            sys.exit(0)
        try:
            globals()["_PHP_CACHE"] = None
            settings = read_settings()
            settings.pop("php_path", None)
            write_settings(settings)
            # 卸载所有PHP相关包
            result = subprocess.run(
                [apt, "purge", "-y", "php-cli", "php-curl", "php-mbstring", "php-xml", "php-common"],
                capture_output=True, text=True, timeout=60
            )
            # 自动清理不再需要的依赖
            subprocess.run([apt, "autoremove", "-y"], capture_output=True, text=True, timeout=60)
            # 验证是否真的卸载了
            remaining = find_php()
            if remaining:
                send_json(200, {"warning": True, "message": "PHP包已卸载，但仍检测到 " + remaining + "，可能需要手动删除"})
            else:
                send_json(200, {"ok": True, "message": "PHP已卸载"})
        except Exception as e:
            send_json(500, {"error": "卸载异常: " + str(e)})
        sys.exit(0)

    # ===== 诊断 =====
    if PATH_INFO == "/api/diagnose" and REQUEST_METHOD == "POST":
        diag = {"steps": []}
        
        # 步骤1: 检查PHP
        php_bin = find_php()
        if php_bin:
            diag["steps"].append({"step": "PHP", "ok": True, "msg": "PHP路径: " + php_bin})
            # 获取PHP版本
            try:
                r = subprocess.run([php_bin, "-v"], capture_output=True, text=True, timeout=5)
                ver = r.stdout.split("\n")[0] if r.stdout else "未知"
                diag["steps"].append({"step": "PHP版本", "ok": True, "msg": ver})
            except: pass
            # 检查扩展
            try:
                r = subprocess.run([php_bin, "-m"], capture_output=True, text=True, timeout=5)
                mods = r.stdout.lower()
                for ext in ["curl", "mbstring", "json", "openssl"]:
                    has = ext in mods
                    diag["steps"].append({"step": "扩展-" + ext, "ok": has, "msg": "已安装" if has else "缺失! 请执行: apt-get install -y php-" + ext})
            except: pass
        else:
            diag["steps"].append({"step": "PHP", "ok": False, "msg": "PHP未安装"})
            send_json(200, diag)
            sys.exit(0)
        
        # 步骤2: 检查ysp.php文件
        if os.path.isfile(YSP_PHP):
            diag["steps"].append({"step": "ysp.php", "ok": True, "msg": "文件存在"})
        else:
            diag["steps"].append({"step": "ysp.php", "ok": False, "msg": "ysp.php文件缺失"})
            send_json(200, diag)
            sys.exit(0)
        
        # 步骤3: 执行ysp.php获取CCTV1直播流
        diag["steps"].append({"step": "调用ysp.php", "ok": True, "msg": "正在获取CCTV1直播流..."})
        result = call_ysp("cctv1", "")
        
        if result.get("m3u8_content"):
            m3u8 = result["m3u8_content"]
            diag["steps"].append({"step": "M3U8获取", "ok": True, "msg": "成功获取M3U8 (" + str(len(m3u8)) + "字节)"})
            
            # 步骤4: 提取TS分片URL并测试连通性
            ts_urls = []
            for line in m3u8.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and line.startswith("http"):
                    ts_urls.append(line)
            
            if ts_urls:
                diag["steps"].append({"step": "TS分片", "ok": True, "msg": "找到" + str(len(ts_urls)) + "个TS分片"})
                # 测试第一个TS分片能否访问（HEAD请求）
                test_url = ts_urls[0]
                try:
                    r = subprocess.run(
                        ["curl", "-s", "--max-time", "10", "-o", "/dev/null", "-w", "%{http_code}",
                         "-H", "Referer: https://live.cctv.cn/",
                         "-H", "User-Agent: qqlive",
                         test_url],
                        capture_output=True, text=True, timeout=15
                    )
                    code = r.stdout.strip()
                    if code in ["200", "206", "302", "301"]:
                        diag["steps"].append({"step": "CDN连通性", "ok": True, "msg": "TS分片可访问 (HTTP " + code + ")"})
                    elif code == "403":
                        diag["steps"].append({"step": "CDN连通性", "ok": False, "msg": "TS分片返回403(鉴权失败)，直播流已过期，请刷新重试"})
                    else:
                        diag["steps"].append({"step": "CDN连通性", "ok": False, "msg": "TS分片返回HTTP " + code + "，NAS无法访问CDN"})
                except subprocess.TimeoutExpired:
                    diag["steps"].append({"step": "CDN连通性", "ok": False, "msg": "TS分片访问超时，NAS网络无法访问CDN"})
                except Exception as e:
                    # curl不存在，用Python测试
                    try:
                        req = urllib.request.Request(test_url, headers={
                            "User-Agent": "qqlive",
                            "Referer": "https://live.cctv.cn/"
                        })
                        resp = urllib.request.urlopen(req, timeout=10, context=get_ssl_ctx())
                        diag["steps"].append({"step": "CDN连通性", "ok": True, "msg": "TS分片可访问 (HTTP " + str(resp.status) + ")"})
                    except Exception as e2:
                        diag["steps"].append({"step": "CDN连通性", "ok": False, "msg": "TS分片访问失败: " + str(e2)[:100]})
            else:
                diag["steps"].append({"step": "TS分片", "ok": False, "msg": "M3U8中未找到TS分片URL"})
        elif result.get("url"):
            diag["steps"].append({"step": "M3U8获取", "ok": True, "msg": "获取到跳转URL: " + result["url"][:80]})
        else:
            err = result.get("error", "未知错误")
            stderr = result.get("stderr", "")
            output = result.get("output", "")
            diag["steps"].append({"step": "M3U8获取", "ok": False, "msg": err + (("\nstderr: " + stderr) if stderr else "") + (("\noutput: " + output) if output else "")})
        
        diag["ok"] = all(s["ok"] for s in diag["steps"])
        send_json(200, diag)
        sys.exit(0)

    # ===== 独立Web服务器管理（带保活检查）=====
    APP_BASE = "/var/apps/fnnas.iptv"
    SERVER_PID_FILE = os.path.join(APP_BASE, "server.pid")
    SERVER_LOG_FILE = os.path.join(APP_BASE, "server.log")
    SERVER_SCRIPT = os.path.join(SCRIPT_DIR, "server.py")
    DEFAULT_SERVER_PORT = 8899

    def get_web_server_status():
        """检查独立Web服务器状态"""
        settings = read_settings()
        port = settings.get("web_port", DEFAULT_SERVER_PORT)
        # 检查PID文件
        pid = None
        running = False
        if os.path.isfile(SERVER_PID_FILE):
            try:
                with open(SERVER_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                # 检查进程是否存在
                os.kill(pid, 0)
                running = True
            except:
                running = False
                pid = None
        return {"port": port, "pid": pid, "running": running}

    def try_auto_restart():
        """保活检查：如果PID文件存在但进程已死，自动重启"""
        if not os.path.isfile(SERVER_PID_FILE):
            return False
        try:
            with open(SERVER_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return False  # 进程还活着，不需要重启
        except:
            pass  # 进程已死，需要重启
        # 检查是否之前用户手动启动过（通过settings中的标记）
        settings = read_settings()
        if not settings.get("web_server_enabled", False):
            return False
        # 自动重启
        port = settings.get("web_port", DEFAULT_SERVER_PORT)
        try:
            os.makedirs(APP_BASE, exist_ok=True)
            proc = subprocess.Popen(
                [sys.executable, SERVER_SCRIPT, "--port", str(port), "--data-dir", DATA_DIR],
                stdout=open(SERVER_LOG_FILE, 'a'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            with open(SERVER_PID_FILE, 'w') as f:
                f.write(str(proc.pid))
            time.sleep(1)
            try:
                os.kill(proc.pid, 0)
                return True
            except:
                return False
        except:
            return False

    if PATH_INFO == "/api/web_server" and REQUEST_METHOD == "GET":
        # 保活检查
        restarted = try_auto_restart()
        status = get_web_server_status()
        # 读取日志最后20行
        log_tail = ""
        if os.path.isfile(SERVER_LOG_FILE):
            try:
                with open(SERVER_LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                    log_tail = ''.join(lines[-20:])
            except:
                log_tail = "(无法读取日志)"
        result = {"status": status, "log_tail": log_tail}
        if restarted:
            result["auto_restarted"] = True
        send_json(200, result)
        sys.exit(0)

    if PATH_INFO == "/api/web_server/start" and REQUEST_METHOD == "POST":
        status = get_web_server_status()
        if status["running"]:
            send_json(200, {"ok": True, "message": "服务器已在运行 (端口" + str(status["port"]) + ", PID " + str(status["pid"]) + ")"})
            sys.exit(0)
        # 启动服务器
        settings = read_settings()
        port = settings.get("web_port", DEFAULT_SERVER_PORT)
        try:
            os.makedirs(APP_BASE, exist_ok=True)
            log_f = open(SERVER_LOG_FILE, 'a')
            log_f.write("\n--- " + time.strftime("%Y-%m-%d %H:%M:%S") + " Starting web server on port " + str(port) + " ---\n")
            log_f.close()
            proc = subprocess.Popen(
                [sys.executable, SERVER_SCRIPT, "--port", str(port), "--data-dir", DATA_DIR],
                stdout=open(SERVER_LOG_FILE, 'a'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            with open(SERVER_PID_FILE, 'w') as f:
                f.write(str(proc.pid))
            time.sleep(1)
            # 验证是否启动成功
            try:
                os.kill(proc.pid, 0)
                # 标记为已启用（保活用）
                settings = read_settings()
                settings["web_server_enabled"] = True
                write_settings(settings)
                send_json(200, {"ok": True, "message": "服务器已启动 (端口" + str(port) + ", PID " + str(proc.pid) + ")"})
            except:
                send_json(200, {"ok": False, "error": "启动失败，请查看日志", "log_tail": "启动后进程立即退出"})
        except Exception as e:
            send_json(200, {"ok": False, "error": "启动异常: " + str(e)})
        sys.exit(0)

    if PATH_INFO == "/api/web_server/stop" and REQUEST_METHOD == "POST":
        status = get_web_server_status()
        if not status["running"]:
            # 清除保活标记
            settings = read_settings()
            settings["web_server_enabled"] = False
            write_settings(settings)
            send_json(200, {"ok": True, "message": "服务器未运行"})
            sys.exit(0)
        try:
            os.kill(status["pid"], 15)
            time.sleep(0.5)
            try:
                os.kill(status["pid"], 9)
            except:
                pass
            if os.path.isfile(SERVER_PID_FILE):
                os.remove(SERVER_PID_FILE)
            # 清除保活标记
            settings = read_settings()
            settings["web_server_enabled"] = False
            write_settings(settings)
            send_json(200, {"ok": True, "message": "服务器已停止"})
        except Exception as e:
            send_json(200, {"ok": False, "error": "停止异常: " + str(e)})
        sys.exit(0)

    if PATH_INFO == "/api/web_server/restart" and REQUEST_METHOD == "POST":
        # 先停再启
        status = get_web_server_status()
        if status["running"]:
            try:
                os.kill(status["pid"], 15)
                time.sleep(0.5)
                try:
                    os.kill(status["pid"], 9)
                except:
                    pass
            except:
                pass
        if os.path.isfile(SERVER_PID_FILE):
            os.remove(SERVER_PID_FILE)
        time.sleep(0.5)
        settings = read_settings()
        port = settings.get("web_port", DEFAULT_SERVER_PORT)
        try:
            os.makedirs(APP_BASE, exist_ok=True)
            log_f = open(SERVER_LOG_FILE, 'a')
            log_f.write("\n--- " + time.strftime("%Y-%m-%d %H:%M:%S") + " Restarting web server on port " + str(port) + " ---\n")
            log_f.close()
            proc = subprocess.Popen(
                [sys.executable, SERVER_SCRIPT, "--port", str(port), "--data-dir", DATA_DIR],
                stdout=open(SERVER_LOG_FILE, 'a'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            with open(SERVER_PID_FILE, 'w') as f:
                f.write(str(proc.pid))
            time.sleep(1)
            try:
                os.kill(proc.pid, 0)
                send_json(200, {"ok": True, "message": "服务器已重启 (端口" + str(port) + ", PID " + str(proc.pid) + ")"})
            except:
                send_json(200, {"ok": False, "error": "重启后进程立即退出，请查看日志"})
        except Exception as e:
            send_json(200, {"ok": False, "error": "重启异常: " + str(e)})
        sys.exit(0)

    if PATH_INFO == "/api/web_server/port" and REQUEST_METHOD == "POST":
        params = get_params()
        new_port = params.get("port", "")
        try:
            new_port = int(new_port)
            if new_port < 1024 or new_port > 65535:
                send_json(200, {"ok": False, "error": "端口号范围: 1024-65535"})
                sys.exit(0)
        except:
            send_json(200, {"ok": False, "error": "请输入有效的端口号"})
            sys.exit(0)
        settings = read_settings()
        settings["web_port"] = new_port
        write_settings(settings)
        send_json(200, {"ok": True, "message": "端口已修改为 " + str(new_port) + "，需重启服务器生效"})
        sys.exit(0)

    # ===== M3U8订阅（公开访问，无需登录） =====
    if PATH_INFO == "/api/m3u" and REQUEST_METHOD == "GET":
        host = os.environ.get('HTTP_HOST', 'localhost')
        base_url = "http://" + host

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
            lines.append('#EXTINF:-1 tvg-name="' + ch_name + '" group-title="' + group + '",' + ch_name)
            lines.append(base_url + '/api/ysp_proxy?id=' + ch_id)

        # 添加自定义频道
        try:
            custom_file = os.path.join(DATA_DIR, "custom_channels.json")
            if os.path.isfile(custom_file):
                with open(custom_file, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
                for ch in custom:
                    name = ch.get('name', '未知频道')
                    urls = ch.get('urls', [])
                    if urls:
                        lines.append('#EXTINF:-1 tvg-name="' + name + '" group-title="自定义",' + name)
                        lines.append(urls[0])
        except:
            pass

        m3u_content = '\n'.join(lines) + '\n'
        print("Content-Type: application/vnd.apple.mpegurl; charset=utf-8")
        print("Cache-Control: no-cache")
        print("Access-Control-Allow-Origin: *")
        print()
        print(m3u_content, end='')
        sys.stdout.flush()
        sys.exit(0)

    # ===== M3U8 URL重写工具 =====
    def rewrite_m3u_content(m3u_text, base_url):
        """解析M3U8内容，将所有外部URL替换为代理URL"""
        host = os.environ.get('HTTP_HOST', 'localhost')
        proxy_prefix = "http://" + host + "/api/proxy_hls?url="
        lines = []
        for line in m3u_text.split('\n'):
            line = line.rstrip('\r')
            stripped = line.strip()
            if stripped.startswith('#'):
                import re
                def replace_uri(m):
                    uri = m.group(1)
                    return 'URI="' + proxy_prefix + quote(uri, safe="") + '"'
                line = re.sub(r'URI="(http[^"]*)"', replace_uri, line)
                lines.append(line)
            elif stripped.startswith('http'):
                lines.append(proxy_prefix + quote(stripped, safe=''))
            elif stripped and not stripped.startswith('#'):
                if base_url and '/' in base_url:
                    abs_url = base_url.rsplit('/', 1)[0] + '/' + stripped
                    lines.append(proxy_prefix + quote(abs_url, safe=''))
                else:
                    lines.append(line)
            else:
                lines.append(line)
        return '\n'.join(lines)

    # ===== HLS全链路代理（proxy_hls）公开访问 =====
    if PATH_INFO == "/api/proxy_hls" and REQUEST_METHOD == "GET":
        params = get_params()
        target_url = params.get("url", "")
        if not target_url:
            send_json(400, {"error": "缺少url参数"})
            sys.exit(0)
        try:
            req = urllib.request.Request(target_url, headers={
                "User-Agent": "qqlive",
                "Referer": "https://live.cctv.cn/",
                "Origin": "https://live.cctv.cn"
            })
            resp = urllib.request.urlopen(req, timeout=10, context=get_ssl_ctx())
            ct = resp.getheader("Content-Type", "")
            is_m3u8 = "mpegurl" in ct.lower() or "m3u" in ct.lower()
            first_chunk = b""
            if not is_m3u8:
                first_chunk = resp.read(20)
                try:
                    preview = first_chunk.decode('utf-8', errors='replace')
                    if preview.startswith('#EXTM3U'):
                        is_m3u8 = True
                except:
                    pass
            if is_m3u8:
                remaining = resp.read()
                m3u_text = (first_chunk + remaining).decode('utf-8', errors='replace')
                rewritten = rewrite_m3u_content(m3u_text, target_url)
                print("Content-Type: application/vnd.apple.mpegurl")
                print("Cache-Control: max-age=10")
                print("Access-Control-Allow-Origin: *")
                print()
                print(rewritten, end='')
                sys.stdout.flush()
            else:
                if not ct:
                    ct = "video/mp2t"
                print("Content-Type: " + ct)
                print("Cache-Control: public, max-age=15")
                print("Access-Control-Allow-Origin: *")
                print()
                if first_chunk:
                    sys.stdout.buffer.write(first_chunk)
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    sys.stdout.buffer.write(chunk)
                sys.stdout.flush()
        except Exception as e:
            send_json(502, {"error": "代理失败", "detail": str(e)[:200]})
        sys.exit(0)

    # ===== 央视频道代理（ysp_proxy）公开访问 =====
    if PATH_INFO == "/api/ysp_proxy" and REQUEST_METHOD == "GET":
        params = get_params()
        ch_id = params.get("id", "")
        if not ch_id:
            send_json(400, {"error": "缺少频道ID"})
            sys.exit(0)
        php_bin = find_php()
        if not php_bin:
            send_json(503, {"error": "PHP环境不可用"})
            sys.exit(0)
        if not os.path.isfile(YSP_PHP):
            send_json(500, {"error": "ysp.php not found"})
            sys.exit(0)
        try:
            result = subprocess.run(
                [php_bin, YSP_PHP, "id=" + ch_id],
                capture_output=True, text=True, timeout=30,
                cwd=SCRIPT_DIR
            )
            output = result.stdout.strip()
            if output.startswith('http'):
                real_url = output
                req = urllib.request.Request(real_url, headers={
                    "User-Agent": "qqlive",
                    "Referer": "https://live.cctv.cn/",
                    "Origin": "https://live.cctv.cn"
                })
                resp = urllib.request.urlopen(req, timeout=15, context=get_ssl_ctx())
                m3u_data = resp.read().decode('utf-8', errors='replace')
                rewritten = rewrite_m3u_content(m3u_data, real_url)
                print("Content-Type: application/vnd.apple.mpegurl")
                print("Cache-Control: max-age=15")
                print("Access-Control-Allow-Origin: *")
                print()
                print(rewritten, end='')
                sys.stdout.flush()
                sys.exit(0)
            if output.startswith("#EXTM3U"):
                rewritten = rewrite_m3u_content(output, None)
                print("Content-Type: application/vnd.apple.mpegurl")
                print("Cache-Control: max-age=15")
                print("Access-Control-Allow-Origin: *")
                print()
                print(rewritten, end='')
                sys.stdout.flush()
                sys.exit(0)
            send_json(502, {"error": "获取播放地址失败", "detail": output[:200]})
        except subprocess.TimeoutExpired:
            send_json(504, {"error": "ysp.php 超时"})
        except Exception as e:
            send_json(500, {"error": "代理异常: " + str(e)})
        sys.exit(0)

    # ===== 静态文件服务（CGI模式下hls.min.js等需通过CGI返回） =====
    if PATH_INFO and not PATH_INFO.startswith("/api/"):
        static_path = os.path.join(SCRIPT_DIR, PATH_INFO.lstrip("/"))
        # 安全检查：防止目录遍历
        if os.path.isfile(static_path) and os.path.realpath(static_path).startswith(os.path.realpath(SCRIPT_DIR)):
            ext = os.path.splitext(static_path)[1].lower()
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
                with open(static_path, 'rb') as f:
                    content = f.read()
                send_streaming_headers(200, ct, {"Cache-Control": "public, max-age=86400"})
                write_chunk(content)
                sys.exit(0)
            except:
                pass

    # 404
    send_json(404, {"error": "Not found", "path": PATH_INFO})

if __name__ == "__main__":
    main()

"""极客时间视频课播放链路辅助模块。

播放链路（与网页播放器一致）：
  1. video_play_auth  (POST time.geekbang.org/serv/v3/source_auth/video_play_auth)
       -> 返回 play_auth（base64 编码的 JSON，内含 STS 临时凭证 + 区域 + AuthInfo + VideoId）
  2. 从 play_auth 解析 STS 凭证，按阿里云 OpenAPI(RPC) 规范自签名，构造
     GetPlayInfo (GET vod.<region>.aliyuncs.com) 请求
       -> 返回 m3u8 播放地址 + Plaintext 解密密钥（AliyunVoDEncryption）
  3. 下载 m3u8 -> 把密钥本地化 -> 由 ffmpeg 解密并合并为 mp4（离线可看）

注意：play_auth / STS 令牌约 4 分钟过期，因此「鉴权 -> 取播放地址 -> 开始下载」
必须在同一次爬取内连续完成，不能先把地址存下来以后再下。
"""

import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import uuid

try:
    import requests
except ImportError:  # pragma: no cover - requests 在运行环境一定存在
    requests = None


# --------------------------------------------------------------------------- #
# 1. play_auth 解析
# --------------------------------------------------------------------------- #
def parse_play_auth(play_auth):
    """把 play_auth（base64 编码的 JSON）解码成 dict。

    返回 dict 含：AccessKeyId / AccessKeySecret / SecurityToken / Region /
    ExpiryTime / MediaId / PlayDomain / AuthInfo(字符串) / VideoMeta 等。
    geekbang 的 play_auth 是**单层** base64(JSON)；这里做一点容错（含 URL-safe
    变体、以及偶尔出现的 JWT 三段式）。
    """
    if not play_auth:
        raise ValueError("play_auth 为空")
    raw = play_auth.strip()

    # 优先：标准 base64(JSON)
    try:
        return json.loads(_b64decode(raw))
    except Exception:
        pass

    # 兜底：JWT 三段式 header.payload.signature
    if raw.count(".") == 2:
        try:
            payload = raw.split(".")[1]
            return json.loads(_b64decode(payload))
        except Exception:
            pass

    raise ValueError("无法解析 play_auth（既不是 base64(JSON) 也不是 JWT）")


def _b64decode(s):
    s = s.replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    return base64.b64decode(s)


# --------------------------------------------------------------------------- #
# 2. GetPlayInfo 签名与 URL 构造（阿里云 OpenAPI RPC 规范）
# --------------------------------------------------------------------------- #
def _percent_encode(s):
    """阿里云 percentEncode：除 A-Za-z0-9-_.~ 外全部按 RFC3986 编码（大写十六进制）。

    Python 标准库 urllib.parse.quote(safe='') 正好满足：保留字母数字与 -_.~，
    其余（含空格、/、=、+、{、}、:、,、" 等）都编码。
    """
    from urllib.parse import quote
    return quote(str(s), safe="")


def _locate_node():
    """定位 node 可执行文件：VOD_NODE_BIN 环境变量 > PATH > WorkBuddy managed node。"""
    env = os.environ.get("VOD_NODE_BIN")
    if env and os.path.exists(env):
        return env
    p = shutil.which("node")
    if p:
        return p
    import glob
    for cand in glob.glob(os.path.expanduser(
            "~/.workbuddy/binaries/node/versions/*/node.exe")):
        return cand
    return None


def _locate_jsdom():
    """定位 jsdom 包所在目录（作为 NODE_PATH）：VOD_JSDOM_PATH > 项目内 > WorkBuddy workspace。"""
    env = os.environ.get("VOD_JSDOM_PATH")
    if env and os.path.isdir(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (
        os.path.join(here, "..", "node_modules"),
        os.path.join(here, "..", "..", "node_modules"),
        os.path.expanduser("~/.workbuddy/binaries/node/workspace/node_modules"),
    ):
        if os.path.isdir(os.path.join(cand, "jsdom")):
            return cand
    return None


def _gen_vod_rand():
    """生成阿里云 VOD 加密视频 GetPlayInfo 的 Rand 参数。

    关键：Rand 不是随机字节，而是 Aliplayer 2.8.2 加密分支
    `_sce_lgtcaygl(_sce_r_skjhfnck())` 的输出（64 字节随机数的加密结果，算法与密钥
    封装在阿里云 jsvm 虚拟机里，静态无法复现）。UUID、短 base64、随机 64 字节
    base64 都会被服务端拒绝（InvalidParameter: Rand is not valid）。
    这里通过 Node + jsdom 真实运行 Aliplayer 加密模块生成（约 2 秒/次）。
    """
    node = _locate_node()
    if not node:
        raise RuntimeError(
            "未找到 node：视频 Rand 需由 Aliplayer 的 jsvm 生成。"
            "请安装 Node.js，或用 VOD_NODE_BIN 指定路径。")
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_gen_vod_rand.js")
    if not os.path.exists(script):
        raise RuntimeError("缺少 _gen_vod_rand.js（Aliplayer Rand 生成脚本）")
    env = os.environ.copy()
    jsdom_path = _locate_jsdom()
    if jsdom_path:
        env["NODE_PATH"] = jsdom_path
    try:
        proc = subprocess.run(
            [node, script], capture_output=True, text=True,
            timeout=60, env=env, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        raise RuntimeError("生成 Rand 超时（node 60s）")
    if proc.returncode != 0:
        raise RuntimeError(f"生成 Rand 失败（node）：{proc.stderr.strip()[:300]}")
    rand = proc.stdout.strip()
    if len(rand) != 88:
        raise RuntimeError(f"生成 Rand 格式异常（长度 {len(rand)}，应为 88）：{rand[:50]}")
    return rand


def build_get_play_info_url(play_auth_obj, video_id):
    """根据 play_auth 解析出的凭证，构造已签名的 GetPlayInfo GET URL。

    video_id 既可用文章里的 video_id，也可直接用 play_auth 里的 MediaId（两者一致）。
    返回的 URL 直接喂给 scrapy.Request(method='GET') 即可。
    """
    access_key_id = play_auth_obj["AccessKeyId"]
    access_key_secret = play_auth_obj["AccessKeySecret"]
    security_token = play_auth_obj["SecurityToken"]
    region = play_auth_obj.get("Region") or "cn-shanghai"
    auth_info = play_auth_obj.get("AuthInfo")
    if isinstance(auth_info, (dict, list)):
        auth_info = json.dumps(auth_info, separators=(",", ":"))

    params = {
        "Action": "GetPlayInfo",
        "AuthInfo": auth_info or "",
        "AuthTimeout": "7200",
        "Channel": "HTML5",
        "Definition": "",
        "Format": "JSON",
        "Formats": "",
        "PlayConfig": "{}",
        "PlayerVersion": "2.8.2",
        # Rand：阿里云播放器协议要求，加密视频必须是 Aliplayer jsvm 生成的
        # 64 字节加密串（88 字符 base64）。UUID/短 base64/纯随机字节都会被拒
        # （InvalidParameter: Rand is not valid），故用 Node 跑官方加密模块生成。
        "Rand": _gen_vod_rand(),
        "ReAuthInfo": "{}",
        "SecurityToken": security_token,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": str(uuid.uuid4()),
        "SignatureVersion": "1.0",
        "StreamType": "video",
        "Version": "2017-03-21",
        "VideoId": video_id,
        "AccessKeyId": access_key_id,
    }
    # 若 play_auth 里带了 MediaId 且与 video_id 不同（一般相同），以 video_id 为准即可。

    # 1) 按 key 升序拼 canonical query
    ordered = sorted(params.items(), key=lambda kv: kv[0])
    canonical = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in ordered
    )
    # 2) StringToSign
    string_to_sign = "GET&" + _percent_encode("/") + "&" + _percent_encode(canonical)
    # 3) Signature = Base64(HMAC-SHA1(AccessKeySecret + "&", StringToSign))
    signature = base64.b64encode(
        hmac.new(
            (access_key_secret + "&").encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("ascii")
    params["Signature"] = signature

    host = f"vod.{region}.aliyuncs.com"
    query = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in params.items()
    )
    return f"https://{host}/?{query}"


# --------------------------------------------------------------------------- #
# 3. 下载 m3u8 + 解密合并为 mp4
# --------------------------------------------------------------------------- #
def find_ffmpeg(preferred="ffmpeg"):
    """定位可用的 ffmpeg 可执行文件。

    优先级：
      1) 环境变量 FFMPEG_BIN（显式指定绝对路径最稳）
      2) PATH 里的 ffmpeg（shutil.which）
      3) 常见「自带 ffmpeg」的第三方软件目录（剪映 JianyingPro、Krita、conda 等，
         用版本无关的通配符，避免写死版本号）。很多用户机器上已经躺着一个真 ffmpeg，
         只是没加进 PATH——这里自动找到它，省去用户手动安装。
    返回绝对路径；都找不到返回 None。
    """
    env = os.environ.get("FFMPEG_BIN")
    if env and os.path.exists(env):
        return env
    if preferred and preferred != "ffmpeg" and os.path.exists(preferred):
        return preferred
    p = shutil.which(preferred or "ffmpeg")
    if p:
        return p
    import glob
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\Apps\*\ffmpeg.exe"),
        r"D:\software\Krita*\bin\ffmpeg.exe",
        r"D:\software\miniconda\Library\bin\ffmpeg.exe",
        r"D:\software\miniconda\Scripts\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ]
    for pat in candidates:
        for hit in sorted(glob.glob(pat), reverse=True):
            if os.path.exists(hit):
                return hit
    return None


def ffmpeg_available(ffmpeg_bin="ffmpeg"):
    return find_ffmpeg(ffmpeg_bin) is not None


def _proxy_dict():
    """从环境变量读取代理，供 requests / ffmpeg 使用。"""
    proxies = {}
    for proto in ("http", "https"):
        env = os.environ.get(proto.upper() + "_PROXY") or os.environ.get(
            proto.upper() + "_PROXY"
        )
        if env:
            proxies[proto] = env
    return proxies or None


def download_and_mux(m3u8_url, plaintext, out_mp4, ffmpeg_bin="ffmpeg",
                     timeout=60, ffmpeg_timeout=3600):
    """下载 AliyunVoDEncryption 的 m3u8，用 Plaintext 密钥本地化后由 ffmpeg 解密合并为 mp4。

    返回 (ok: bool, msg: str)。
    - plaintext: GetPlayInfo 返回的 Plaintext 字段（base64 字符串），即内容密钥。
    - ffmpeg 通过 find_ffmpeg 自动定位（PATH / FFMPEG_BIN / 常见自带目录）；都找不到才报缺。
    """
    ffmpeg_real = find_ffmpeg(ffmpeg_bin)
    if not ffmpeg_real:
        return False, ("ffmpeg 未找到（PATH 无 ffmpeg，且未在常见目录发现；"
                       "可用环境变量 FFMPEG_BIN 指定绝对路径，或把 ffmpeg 加入 PATH）")

    import tempfile

    proxies = _proxy_dict()
    tmpdir = tempfile.mkdtemp(prefix="jk_vod_")
    try:
        # 1) 下载 m3u8
        resp = requests.get(m3u8_url, timeout=timeout, proxies=proxies)
        if resp.status_code != 200:
            return False, f"下载 m3u8 失败 status={resp.status_code}"
        m3u8_text = resp.text

        # 2) 解析 #EXT-X-KEY：AliyunVoDEncryption 的 m3u8 里会带 METHOD=AES-128 与密钥 URI，
        #    我们把 URI 替换成本地 key.key，并把 Plaintext 解码后写入该文件。
        key_bytes = base64.b64decode(plaintext)
        key_path = os.path.join(tmpdir, "key.key")
        with open(key_path, "wb") as f:
            f.write(key_bytes)

        local_m3u8 = m3u8_text
        # 把密钥 URI 指向本地文件（保留原有 IV 等属性）
        def _replace_key(m):
            attrs = m.group(2)
            # 仅替换 URI="..."，保留 METHOD / IV 等
            attrs = re.sub(r'URI="[^"]*"', f'URI="key.key"', attrs)
            return f"{m.group(1)}{attrs}"

        local_m3u8 = re.sub(
            r'(#EXT-X-KEY:)([^\\n]*)',
            _replace_key,
            local_m3u8,
        )

        # 3) 让分片 URL 绝对化（若 m3u8 里是相对路径，基于 m3u8 地址补全）
        base = m3u8_url.rsplit("/", 1)[0] + "/"
        lines = []
        for line in local_m3u8.splitlines():
            if line and not line.startswith("#") and not line.startswith("http"):
                line = base + line
            lines.append(line)
        local_m3u8 = "\n".join(lines)
        local_m3u8_path = os.path.join(tmpdir, "index.m3u8")
        with open(local_m3u8_path, "w", encoding="utf-8") as f:
            f.write(local_m3u8)

        # 4) ffmpeg 解密合并（-c copy 不重编码，速度快；-allowed_extensions ALL 允许 key.key）
        ffmpeg_cmd = [
            ffmpeg_real, "-allowed_extensions", "ALL",
            "-i", local_m3u8_path,
            "-c", "copy", "-y", out_mp4,
        ]
        env = dict(os.environ)
        px = _proxy_dict()
        if px:
            # ffmpeg 用第一个代理（http/https 都可以访问 CDN）
            proxy_url = px.get("https") or px.get("http")
            if proxy_url:
                env["HTTP_PROXY"] = proxy_url
                env["HTTPS_PROXY"] = proxy_url
        proc = subprocess.run(
            ffmpeg_cmd, capture_output=True, text=True, env=env, timeout=ffmpeg_timeout
        )
        if proc.returncode != 0:
            return False, f"ffmpeg 失败: {proc.stderr[-500:]}"
        if not os.path.exists(out_mp4) or os.path.getsize(out_mp4) == 0:
            return False, "ffmpeg 未产出有效 mp4"
        return True, out_mp4
    except Exception as exc:  # noqa: BLE001
        return False, f"下载/合并异常: {exc}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

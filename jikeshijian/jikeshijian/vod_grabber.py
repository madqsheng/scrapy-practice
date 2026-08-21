# -*- coding: utf-8 -*-
"""视频课 mp4 抓取器：真实 Chrome 播放 Aliplayer 视频，截获解密后的 fMP4 合并为 mp4。

背景：极客时间视频课使用阿里云 AliyunVoDEncryption **私有加密**——TS 包级加密
（容器/PAT/PMT 明文，音视频 PES payload 密文），算法与密钥封装在阿里云 jsvm
虚拟机里无法静态复现；ffmpeg 的标准 HLS AES-128 解密对它无效（还会被 m3u8 里
拼错成 MEATHOD 的假 KEY 行误导）。

唯一可靠的解路径：让真实播放器（Aliplayer 2.8.2 + hls.js）解密，再截获它交给
MSE 的**解密后**数据（SourceBuffer.appendBuffer 的参数，即 remux 后的 fMP4，
视频/音频各一个 SourceBuffer），分别保存后用 ffmpeg 无损合并为最终 mp4。

性能：每视频约 播放时长/4 + 启动开销（秒），全部 CPU 软解。
"""
import json
import os
import re
import subprocess
import tempfile
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

_HERE = os.path.dirname(os.path.abspath(__file__))
_ALIPLAYER_JS = os.path.join(_HERE, "..", "_aliplayer_282.js")
_ALIPLAYER_VOD_JS = os.path.join(_HERE, "..", "_aliplayer_vod_282.js")


def _ffmpeg_path():
    from jikeshijian.vod_helper import find_ffmpeg
    return find_ffmpeg()


def _grab_in_browser(play_auth, video_id, timeout=600, playback_rate=4):
    """在 Chrome 里播放视频并截获解密后的 fMP4 数据。

    返回 (ok, data_dict|msg)。data_dict = {sb1: bytes, sb2: bytes, log: [...]}
    """
    HOOK = """
window.__buffers = {};
window.__plog = [];
(function () {
  var origAppend = SourceBuffer.prototype.appendBuffer;
  SourceBuffer.prototype.appendBuffer = function (data) {
    try {
      if (!this.__id) {
        this.__id = 'sb' + (Object.keys(window.__buffers).length + 1);
        window.__buffers[this.__id] = [];
      }
      window.__buffers[this.__id].push(new Uint8Array(data));
    } catch (e) {}
    return origAppend.call(this, data);
  };
})();
"""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1000,700")
    opts.add_argument("--autoplay-policy=no-user-gesture-required")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": HOOK})
        driver.get("https://example.com/")
        time.sleep(2)

        with open(_ALIPLAYER_JS, encoding="utf-8") as f:
            js1 = f.read()
        with open(_ALIPLAYER_VOD_JS, encoding="utf-8") as f:
            js2 = f.read()
        driver.execute_script(js1)
        driver.execute_script(js2)
        if driver.execute_script("return typeof Aliplayer;") != "function":
            return False, "Aliplayer 加载失败"

        init = """
        var div = document.createElement('div');
        div.id = 'player-div'; div.style.width='640px'; div.style.height='360px';
        document.body.appendChild(div);
        var cfg = %s;
        window.__player = new Aliplayer(cfg, function(){ window.__plog.push('cb:ready'); });
        window.__player.on('ready', function(){ window.__plog.push('ev:ready'); });
        window.__player.on('error', function(e){ window.__plog.push('ev:error:' + JSON.stringify(e)); });
        return 'init';
        """ % json.dumps({
            "id": "player-div",
            "vid": video_id,
            "playauth": play_auth,
            "encryptType": 1,
            "autoplay": True,
            "mediaType": "video",
        })
        driver.execute_script(init)
        time.sleep(4)
        driver.execute_script(
            "try{var v=document.querySelector('video'); v.playbackRate = %d;}catch(e){}" % playback_rate)

        # 轮询等待播放到结尾（或超时）
        deadline = time.time() + timeout
        last_report = 0
        while time.time() < deadline:
            state = driver.execute_script(
                "try{var v=document.querySelector('video');"
                "return JSON.stringify({d:v.duration,c:v.currentTime,p:v.paused});}catch(e){return '{}';}")
            st = json.loads(state)
            d, c = st.get("d", 0) or 0, st.get("c", 0) or 0
            now = time.time()
            if now - last_report > 20:
                print(f"  播放进度 {c:.0f}/{d:.0f}s")
                last_report = now
            if d > 0 and c >= d * 0.95:
                break
            if "ev:error" in driver.execute_script("return JSON.stringify(window.__plog||[]);"):
                break
            time.sleep(2)

        log = driver.execute_script("return JSON.stringify(window.__plog);")
        keys = driver.execute_script("return Object.keys(window.__buffers);")
        if any("error" in k for k in json.loads(log or "[]")):
            return False, f"播放器报错: {log}"
        if len(keys) < 2:
            return False, f"未收集到完整音视频数据 (buffers={keys}, log={log})"

        data = {}
        for key in keys:
            total = driver.execute_script(
                "return window.__buffers['%s'].reduce(function(a,c){return a+c.length;},0);" % key)
            driver.execute_script(
                "var cs=window.__buffers['%s']; var t=cs.reduce(function(a,c){return a+c.length;},0);"
                "var o=new Uint8Array(t); var p=0;"
                "for(var i=0;i<cs.length;i++){o.set(cs[i],p);p+=cs[i].length;} window.__out=o;" % key)
            buf = bytearray()
            step = 2 * 1024 * 1024
            for off in range(0, total, step):
                part = driver.execute_script(
                    "var a=window.__out.slice(%d,%d); return Array.from(a);"
                    % (off, min(off + step, total)))
                buf.extend(bytes(part))
            data[key] = bytes(buf)
        return True, {"buffers": data, "log": log}
    finally:
        driver.quit()


def _probe_streams(path):
    """ffmpeg 探测文件里的流：返回 (has_video, has_audio)。"""
    ff = _ffmpeg_path()
    if not ff:
        return False, False
    proc = subprocess.run([ff, "-i", path], capture_output=True, text=True, timeout=30)
    err = proc.stderr
    return ("Video:" in err and "Video:" in err.split("Stream #")[-1] or True), ("Audio:" in err)


def grab_mp4(play_auth, video_id, out_mp4, timeout=600, playback_rate=4):
    """抓取视频课 mp4。返回 (ok, msg)。

    play_auth: video_play_auth 接口返回的 play_auth（base64 JSON）。
    """
    ok, res = _grab_in_browser(play_auth, video_id, timeout=timeout,
                               playback_rate=playback_rate)
    if not ok:
        return False, res
    buffers = res["buffers"]
    ff = _ffmpeg_path()
    if not ff:
        return False, "未找到 ffmpeg，无法合并抓取到的音视频流"
    tmp = tempfile.mkdtemp(prefix="jk_grab_")
    try:
        paths = []
        for key, data in buffers.items():
            p = os.path.join(tmp, f"{key}.mp4")
            with open(p, "wb") as f:
                f.write(data)
            paths.append((key, p))
        # 探测：视频流文件作为第一个输入
        video_path, audio_path = None, None
        for key, p in paths:
            proc = subprocess.run([ff, "-i", p], capture_output=True, text=True, timeout=30)
            err = proc.stderr
            if "Audio:" in err:
                audio_path = p
            if "Video:" in err:
                video_path = p
        if not video_path or not audio_path:
            return False, f"抓取结果缺少音/视频流 (video={video_path}, audio={audio_path})"
        os.makedirs(os.path.dirname(os.path.abspath(out_mp4)) or ".", exist_ok=True)
        proc = subprocess.run(
            [ff, "-i", video_path, "-i", audio_path, "-c", "copy", "-y", out_mp4],
            capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            return False, f"ffmpeg 合并失败: {proc.stderr[-400:]}"
        if not os.path.exists(out_mp4) or os.path.getsize(out_mp4) < 100000:
            return False, "合并产物过小或缺失"
        return True, out_mp4
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

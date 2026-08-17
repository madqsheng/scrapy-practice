# 重建 course_index.json —— 按浏览器规律: size=20, prev=0,1,2,3...(页索引语义)
# 固定: product_type=0, pvip=0, with_articles=false
# 边爬边存; 间隔 3s 防限额; 前台执行
import json, urllib.request, urllib.error, time, os, importlib.util

PROXY = "127.0.0.1:7897"
URL = "https://time.geekbang.org/serv/v4/pvip/product_list"
INDEX_PATH = r"C:/Users/admin/Desktop/scrapy-practice/jikeshijian/jikeshijian/course_index.json"
HERE = os.path.dirname(os.path.abspath(__file__))  # jikeshijian/ 项目根

def load_cookie():
    # 优先: 读 settings.py 的 MY_COOKIE(与爬虫同一处, 单一来源)
    settings_path = os.path.join(HERE, "jikeshijian", "settings.py")
    if os.path.exists(settings_path):
        try:
            spec = importlib.util.spec_from_file_location("jk_settings", settings_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            c = getattr(mod, "MY_COOKIE", "") or ""
            if c.strip():
                return c.strip(), "settings.py:MY_COOKIE"
        except Exception as e:
            print("  读 settings.py 失败:", e)
    # 兜底: 项目根目录的 .cookie.txt
    alt = os.path.join(HERE, ".cookie.txt")
    if os.path.exists(alt):
        return open(alt, encoding="utf-8").read().strip(), ".cookie.txt"
    raise SystemExit("找不到 cookie: 请更新 settings.py 的 MY_COOKIE, 或在 jikeshijian/ 下放 .cookie.txt")

cookie, cookie_src = load_cookie()
print("使用 cookie 来源:", cookie_src)
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": "http://" + PROXY, "https": "http://" + PROXY})
)
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://time.geekbang.org/",
    "Origin": "https://time.geekbang.org/",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

DELAY = 3
MAX_PREV = 40          # 上限保险; 若页索引成立, prev=27 即够 560
TARGET = 560

# 先重置文件
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    json.dump({"updated_at": None, "total": 0, "by_title": {}}, f, ensure_ascii=False, indent=2)

by_title = {}
prev = 0
consecutive_empty = 0

print("开始: size=20, prev=0,1,2,...  目标", TARGET)
while prev <= MAX_PREV:
    payload = {
        "tag_ids": [], "product_form": 0, "product_type": 0, "pvip": 0,
        "prev": prev, "size": 20, "sort": 8, "with_articles": False,
    }
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), method="POST", headers=HEADERS)
    req.add_header("Cookie", cookie)
    try:
        with opener.open(req, timeout=30) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  prev={prev} HTTPError {e.code}")
        if e.code in (451, 452):
            print("  疑似限流, 暂停30s后重试同一页")
            time.sleep(30)
            continue
        break
    except Exception as e:
        print(f"  prev={prev} 异常 {e}")
        time.sleep(5)
        continue

    arr = resp.get("data", {}).get("products") or []
    new = 0
    for p in arr:
        tid = p.get("id")
        ttitle = p.get("title")
        if tid is None or not ttitle:
            continue
        key = str(ttitle)
        if key not in by_title:
            by_title[key] = tid
            new += 1

    more = resp.get("data", {}).get("page", {}).get("more")
    print(f"  prev={prev:>2}: 本页 {len(arr):>2} 门, 新增 {new:>2}, 累计 {len(by_title):>3}, more={more}")

    # 进度落盘
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(by_title),
            "by_title": by_title,
        }, f, ensure_ascii=False, indent=2)

    if new == 0:
        consecutive_empty += 1
        if consecutive_empty >= 3:
            print("  连续3页无新增 -> 停止(机制可能失效或已到底)")
            break
    else:
        consecutive_empty = 0

    if len(by_title) >= TARGET:
        print(f"  已达 {TARGET}, 停止")
        break

    prev += 1
    time.sleep(DELAY)

print("结束. 最终 by_title 数量:", len(by_title))

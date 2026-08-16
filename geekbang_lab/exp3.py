import json
import time
import urllib.request

BASE = "https://time.geekbang.org/serv/v4/pvip/product_list"
COOKIE_FILE = r"C:/Users/admin/Desktop/scrapy-practice/geekbang_lab/.cookie.txt"
OUT = r"C:/Users/admin/Desktop/scrapy-practice/geekbang_lab/exp3_raw.json"
PROXY = "http://127.0.0.1:7897"
DELAY = 4  # 秒，控节奏防限流


def load_cookie():
    with open(COOKIE_FILE, encoding="utf-8") as f:
        return f.read().strip()


def main():
    cookie = load_cookie()
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Referer": "https://time.geekbang.org/",
        "Cookie": cookie,
        "Content-Type": "application/json",
    }
    # 固定 product_type=0, pvip=0, with_articles=false，只变 size/prev
    groups = [
        (10, 0),
        (10, 10),
        (10, 20),
        (10, 30),
        (10, 40),
    ]
    results = []
    for i, (size, prev) in enumerate(groups):
        payload = {
            "tag_ids": [],
            "product_form": 0,
            "product_type": 0,
            "pvip": 0,
            "prev": prev,
            "size": size,
            "sort": 8,
            "with_articles": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(BASE, data=data, headers=headers, method="POST")
        try:
            with opener.open(req, timeout=30) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8")
            parsed = json.loads(body)
            n = len(parsed.get("data", {}).get("products", []) or parsed.get("data", {}).get("list", []))
        except Exception as e:
            parsed = {"__error__": str(e)}
            status = None
            n = 0
        entry = {
            "group": i + 1,
            "size": size,
            "prev": prev,
            "url": BASE,
            "payload": payload,
            "status": status,
            "response": parsed,
        }
        results.append(entry)
        # 边执行边保存
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[done] group={i + 1} size={size} prev={prev} status={status} products={n} saved {len(results)}/5", flush=True)
        if i != len(groups) - 1:
            print(f"[sleep] {DELAY}s ...", flush=True)
            time.sleep(DELAY)
    print("[finish] all 5 requests done -> " + OUT, flush=True)


if __name__ == "__main__":
    main()

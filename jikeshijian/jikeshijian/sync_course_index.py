#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性把极客时间「课程名 -> 课程 id」抓全，固化到 course_index.json（提交进仓库）。

为什么要有这个文件：
- 之前爬虫每次运行都靠运行时接口（learn/product、product_list）按名解析课程 id，
  既慢又容易被限流，而且目录翻不全时会让你手改课名。
- 现在把目录离线固化：爬虫优先读 course_index.json 做离线精确匹配，不再依赖网络。

用法（在仓库根目录 jikeshijian/ 下执行）：
    python jikeshijian/sync_course_index.py

依赖：仅标准库（urllib）。cookie / UA 取自 jikeshijian/settings.py 的 MY_COOKIE / MY_USER_AGENT。
注意：cookie 有有效期，若执行后看到 code=-2000 / 登录失效，请更新 settings.MY_COOKIE 后重跑。

EXTRA 是「用户确认但 product_list 目录翻不到」的课程的固化映射（id 由用户提供，VIP 可访问）。
重跑本脚本会自动把 EXTRA 重新写回索引，不会被覆盖丢。
"""
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETTINGS_PATH = HERE / "settings.py"
OUT_PATH = HERE / "course_index.json"

# ---- 载入 settings 里的登录态 ----
spec = importlib.util.spec_from_file_location("jk_settings", str(SETTINGS_PATH))
jk_settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jk_settings)
COOKIE = getattr(jk_settings, "MY_COOKIE", "")
UA = getattr(jk_settings, "MY_USER_AGENT", "Mozilla/5.0")

PRODUCT_LIST_URL = "https://time.geekbang.org/serv/v4/pvip/product_list"
PRODUCT_URL = "https://time.geekbang.org/serv/v3/learn/product"

# 用户在对话里明确给出 id 的课程：product_list 目录翻不到（公开课/另一类目），
# 但 VIP 可访问。把「用户写的名字 -> id + 规范标题」固化在这里，爬虫离线即可解析，
# 用户无需再手改 MY_COURSES 里的名字。
EXTRA = [
    {"name": "LangChain 实战课", "id": 100617601, "title": "LangChain实战课"},
    {"name": "Claude Code 工程化实战", "id": 101119601, "title": "Claude Code Skill入门实战课"},
    {"name": "RAG 快速开发实战", "id": 100799801, "title": "RAG前沿入门课"},
    {"name": "AI Agent 系统设计面试现场", "id": 101069801, "title": "AI Agent入门第一课：零基础玩转智能体"},
    {"name": "AI Agent 智能体实战课", "id": 101069801, "title": "AI Agent入门第一课：零基础玩转智能体"},
    {"name": "Agent 设计模式之美", "id": 100039001, "title": "设计模式之美"},
    {"name": "Harness Agent 脚手架实战课", "id": 101170001, "title": "Harness Agent 脚手架实战课"},
    {"name": "Claude Code 企业级全链路开发实战", "id": 101128701, "title": "Claude Code 企业级全链路开发实战"},
]


def _make_request(url, data):
    import urllib.request as ur
    req = ur.Request(url, data=json.dumps(data).encode("utf-8"), method="POST")
    req.add_header("User-Agent", UA)
    req.add_header("Cookie", COOKIE)
    req.add_header("Content-Type", "application/json")
    req.add_header("Referer", "https://time.geekbang.org/dashboard/course")
    req.add_header("Accept", "application/json")
    with ur.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_product_list_all_types():
    """全站目录：遍历 product_type 0~7（覆盖专栏/视频/微课/每日一课等），分页抓全。"""
    out = {}
    for pt in range(0, 8):
        prev = 0
        size = 100
        pages = 0
        while True:
            body = {"tag_ids": [], "product_type": pt, "product_form": 0, "pvip": 0,
                    "prev": prev, "size": size, "sort": 8, "with_articles": False}
            try:
                resp = _make_request(PRODUCT_LIST_URL, body)
            except Exception as e:
                print(f"  [product_list pt={pt}] 请求异常：{e}")
                break
            if resp.get("code") != 0:
                print(f"  [product_list pt={pt}] 返回异常 code={resp.get('code')} msg={resp.get('msg')}")
                break
            data = resp.get("data") or {}
            products = data.get("products") or []
            for p in products:
                title = (p.get("title") or "").strip()
                pid = p.get("id")
                if title and pid is not None:
                    out.setdefault(title, pid)
            pages += 1
            page = data.get("page") or {}
            if (not page.get("more")) or (not products):
                break
            if pages >= 100:
                print(f"  [product_list pt={pt}] 已达 100 页上限")
                break
            prev += len(products)
        print(f"  [product_list pt={pt}] 累计去重 {len(out)} 门")
    return out


def fetch_learn_product():
    """「我的课程」（已购/在学），返回 {title: id}。"""
    out = {}
    prev = 0
    size = 100
    while True:
        body = {"desc": "true", "expire": 1, "last_learn": 0, "learn_status": 0,
                "prev": prev, "size": size, "sort": 1, "type": "c1", "with_learn_count": 1}
        try:
            resp = _make_request(PRODUCT_URL, body)
        except Exception as e:
            print("  [learn/product] 请求异常：", e)
            break
        if resp.get("code") != 0:
            print("  [learn/product] 返回异常 code=", resp.get("code"), "msg=", resp.get("msg"))
            break
        data = resp.get("data") or {}
        products = data.get("products") or []
        for p in products:
            title = (p.get("title") or "").strip()
            pid = p.get("id")
            if title and pid is not None:
                out[title] = pid
        page = data.get("page") or {}
        if (not page.get("more")) or (not products):
            break
        prev += size
    return out


def main():
    if not COOKIE:
        print("错误：settings.MY_COOKIE 为空，无法请求。请先配置登录 cookie。")
        sys.exit(1)
    print("开始同步课程目录（product_list 全类型 + learn/product）...")
    lp = fetch_learn_product()
    print(f"  [learn/product] 共 {len(lp)} 门")
    pl = fetch_product_list_all_types()
    by_title = {}
    by_title.update(lp)
    by_title.update(pl)  # product_list 覆盖，通常更全

    result = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "learn_count": len(lp),
        "product_list_count": len(pl),
        "total": len(by_title),
        "by_title": by_title,
        "extra": EXTRA,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n已写入 {OUT_PATH.name}：learn={len(lp)} + product_list={len(pl)} = 去重后 {len(by_title)} 门；"
          f"另固化 EXTRA 手动映射 {len(EXTRA)} 条")

    # 对照 MY_COURSES：catalog 精确命中 / EXTRA 命中 / 仍未命中
    my_courses = list(getattr(jk_settings, "MY_COURSES", []) or [])
    extra_by_name = {e["name"]: e for e in EXTRA}
    print("\n对照 MY_COURSES 解析结果：")
    still_missing = []
    for name in my_courses:
        n = (name or "").strip()
        if n in by_title:
            print(f"  ✅[目录] {n} -> {by_title[n]}")
        elif n in extra_by_name:
            e = extra_by_name[n]
            print(f"  🆔[EXTRA] {n} -> {e['id']}（规范标题：{e['title']}）")
        else:
            print(f"  ❌ 未命中（目录与 EXTRA 均无）：{n}")
            still_missing.append(n)
    if still_missing:
        print("\n以下仍需处理（目录与 EXTRA 都无，请提供课程页 id 或确认课名）：")
        for n in still_missing:
            print(f"   - {n}")


if __name__ == "__main__":
    main()

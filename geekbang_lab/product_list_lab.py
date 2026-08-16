"""
product_list_lab.py
=====================================================================
极客时间 product_list 接口「参数 ↔ 响应」对照实验台（独立于 scrapy 框架）。

目的：通过控制变量实验，搞清楚
    https://time.geekbang.org/serv/v4/pvip/product_list
各个参数（tag_ids / product_type / product_form / pvip / prev / size /
sort / with_articles）到底如何影响响应，最终找到「VIP 用户下获取最全面、
准确的 课程名↔id 映射表」的传参方法。

只复用 settings.py 里的 MY_COOKIE / MY_USER_AGENT / MY_REFERER（不改动爬虫代码）。

运行：
    python product_list_lab.py                 # 跑全部实验
    python product_list_lab.py --exp exp2      # 只跑某个实验
    python product_list_lab.py --exp exp6 --type 3   # 只扫某 product_type
    python product_list_lab.py --proxy http://127.0.0.1:7897   # 走本机代理

说明：
    - 浏览器真实请求体：{"tag_ids":[],"product_type":0,"product_form":0,
      "pvip":0,"prev":0,"size":20,"sort":8,"with_articles":true}
    - prev 是分页游标（偏移量），size=20 时第 N 页 prev=(N-1)*20。
    - 请求间隔 DELAY 用于降低 451/452 限流概率。
=====================================================================
"""
import argparse
import importlib.util
import json
import time
import urllib.request as ur
from pathlib import Path

# ---------------- 读取配置（复用 settings） ----------------
ROOT = Path(__file__).resolve().parent.parent          # scrapy-practice/
SPEC = importlib.util.spec_from_file_location(
    's', str(ROOT / 'jikeshijian' / 'jikeshijian' / 'settings.py'))
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)
COOKIE = S.MY_COOKIE
UA = S.MY_USER_AGENT
REF = S.MY_REFERER

URL = "https://time.geekbang.org/serv/v4/pvip/product_list"
DELAY = 1.0          # 请求间隔（秒）
HEADERS = (
    ('User-Agent', UA),
    ('Cookie', COOKIE),
    ('Content-Type', 'application/json'),
    ('Referer', REF),
    ('Accept', 'application/json'),
)

# 我们要在全集里重点验证的 5 门「之前被认为不在 product_list 里」的课
TARGETS = {
    101119601: "Claude Code Skill入门实战课",
    100799801: "RAG前沿入门课",
    101069801: "AI Agent入门第一课：零基础玩转智能体",
    101170001: "Harness Agent 脚手架实战课",
    101128701: "Claude Code 企业级全链路开发实战",
}
TARGET_SUB = ['Claude Code Skill', 'RAG前沿', 'AI Agent入门第一课',
              'Harness Agent', 'Claude Code 企业级']


def post(body, proxy=None):
    data = json.dumps(body).encode('utf-8')
    req = ur.Request(URL, data=data, method='POST')
    for k, v in HEADERS:
        req.add_header(k, v)
    if proxy:
        opener = ur.build_opener(ur.ProxyHandler({'http': proxy, 'https': proxy}))
        resp = opener.open(req, timeout=30)
    else:
        resp = ur.urlopen(req, timeout=30)
    return json.loads(resp.read().decode('utf-8'))


def bp(**over):
    """构造基础请求体（默认 = 浏览器真实请求）。"""
    b = {"tag_ids": [], "product_type": 0, "product_form": 0,
         "pvip": 0, "prev": 0, "size": 20, "sort": 8, "with_articles": True}
    b.update(over)
    return b


def collect_type(product_type, pvip=0, with_articles=True, size=20,
                 max_pages=300, proxy=None):
    """翻完某个 product_type 的全部页，返回 {id: title} 与元信息。"""
    out = {}
    prev = 0
    pages = 0
    total = None
    first_ids = None
    while True:
        b = bp(product_type=product_type, pvip=pvip,
               with_articles=with_articles, size=size, prev=prev)
        r = post(b, proxy)
        if r.get('code') != 0:
            return {'error': r.get('code'), 'msg': r.get('msg')}
        d = r.get('data') or {}
        ps = d.get('products') or []
        if total is None:
            total = (d.get('page') or {}).get('total')
        if first_ids is None and ps:
            first_ids = [p.get('id') for p in ps[:3]]
        for p in ps:
            i = p.get('id')
            t = (p.get('title') or '').strip()
            if i is not None:
                out[i] = t
        pg = d.get('page') or {}
        more = pg.get('more')
        pages += 1
        if not more or not ps:
            break
        prev += len(ps)
        if pages >= max_pages:
            break
        time.sleep(DELAY)
    return {'map': out, 'pages': pages, 'total': total, 'first_ids': first_ids}


# ============================ 实验 ============================
def exp1_baseline(proxy=None):
    """实验1：基线。用浏览器真实请求体取第 1 页，看清响应结构。"""
    r = post(bp(), proxy)
    d = r.get('data') or {}
    ps = d.get('products') or []
    return {
        'input': {'body': bp()},
        'output': {
            'code': r.get('code'),
            'data_keys': list(d.keys()),
            'page': d.get('page'),
            'count_this_page': len(ps),
            'sample_product_fields': list(ps[0].keys()) if ps else [],
            'sample_product[0]': ({k: ps[0].get(k) for k in
                                   ('id', 'title', 'type', 'is_opencourse',
                                    'in_pvip', 'is_column')} if ps else None),
        },
        'conclusion': '记录真实响应的字段与分页结构，作为后续对照基准。',
    }


def exp2_with_articles(proxy=None):
    """实验2（控制变量：with_articles）：true vs false，课程集合是否不同。"""
    a = post(bp(with_articles=True), proxy)
    b = post(bp(with_articles=False), proxy)
    sa = {p.get('id') for p in (a.get('data') or {}).get('products') or []}
    sb = {p.get('id') for p in (b.get('data') or {}).get('products') or []}
    return {
        'input': {'body_true': bp(with_articles=True),
                  'body_false': bp(with_articles=False)},
        'output': {
            'count_true': len(sa),
            'count_false': len(sb),
            'ids_only_in_true': list(sa - sb)[:20],
            'ids_only_in_false': list(sb - sa)[:20],
            'sets_equal': sa == sb,
        },
        'conclusion': ('对比 with_articles 对「返回课程集合」的影响；'
                       '若集合不同则说明之前用 false 漏掉了课程。'),
    }


def exp3_pvip(proxy=None):
    """实验3（控制变量：pvip）：0 vs 1，课程集合是否不同。"""
    a = post(bp(pvip=0), proxy)
    b = post(bp(pvip=1), proxy)
    sa = {p.get('id') for p in (a.get('data') or {}).get('products') or []}
    sb = {p.get('id') for p in (b.get('data') or {}).get('products') or []}
    return {
        'input': {'body_pvip0': bp(pvip=0), 'body_pvip1': bp(pvip=1)},
        'output': {
            'count_pvip0': len(sa),
            'count_pvip1': len(sb),
            'ids_only_in_pvip0': list(sa - sb)[:20],
            'ids_only_in_pvip1': list(sb - sa)[:20],
            'sets_equal': sa == sb,
        },
        'conclusion': '对比 pvip 对课程集合的影响；VIP 全集可能需要 pvip=0 与 pvip=1 取并集。',
    }


def exp4_size(proxy=None):
    """实验4（控制变量：size）：size=20/50/100，服务端是否真的按 size 返回。"""
    out = {}
    for sz in (20, 50, 100):
        ps = (post(bp(size=sz), proxy).get('data') or {}).get('products') or []
        out[sz] = len(ps)
    return {
        'input': {'size_values': [20, 50, 100], 'body_template': bp(size='<sz>')},
        'output': {'returned_count_per_size': out},
        'conclusion': '观察 size 是否被服务端遵守；决定翻页步长。',
    }


def exp5_prev(proxy=None):
    """实验5（控制变量：prev 游标）：prev=0/20/40 是否互不重叠且累积。"""
    seen = {}
    union = set()
    pages_detail = []
    for prev in (0, 20, 40):
        ps = (post(bp(prev=prev), proxy).get('data') or {}).get('products') or []
        ids = {p.get('id') for p in ps}
        pages_detail.append({'prev': prev, 'count': len(ids),
                             'new_ids': len(ids - union)})
        union |= ids
        seen[prev] = ids
    return {
        'input': {'prev_values': [0, 20, 40], 'body_template': bp(prev='<prev>')},
        'output': {'pages': pages_detail, 'cumulative_ids': len(union)},
        'conclusion': '验证 prev 作为偏移游标：每页 +size 即可不重不漏翻完。',
    }


def exp6_full_sweep(proxy=None, only_type=None):
    """实验6：全类型 × (pvip=0,1) 全量翻页，并集后检索目标 5 门课。
    这是「最全面映射」的核心实验。"""
    types = [only_type] if only_type is not None else list(range(0, 13))
    union_map = {}
    per_type = {}
    for pvip in (0, 1):
        for pt in types:
            res = collect_type(pt, pvip=pvip, proxy=proxy)
            if 'error' in res:
                per_type[f'pt{pt}_pvip{pvip}'] = res
                continue
            m = res['map']
            per_type[f'pt{pt}_pvip{pvip}'] = {
                'courses': len(m), 'pages': res['pages'], 'total': res['total']}
            for i, t in m.items():
                union_map[i] = t
            time.sleep(DELAY)

    # 检索目标 5 门
    hit_id = {i: union_map.get(i) for i in TARGETS if i in union_map}
    hit_name = []
    for i, t in union_map.items():
        for sub in TARGET_SUB:
            if sub.lower() in t.lower():
                hit_name.append((i, t, sub))
    return {
        'input': {'types': types, 'pvip': [0, 1],
                  'body_template': bp(product_type='<pt>', pvip='<pvip>', prev='<+size>')},
        'output': {
            'total_unique_courses': len(union_map),
            'per_type': per_type,
            'target_id_hits': hit_id,
            'target_name_hits': hit_name,
        },
        'conclusion': ('并集是否覆盖目标 5 门；据此确定最终传参方法。'),
    }


EXPERIMENTS = {
    'exp1': ('基线：真实请求体第1页结构', exp1_baseline),
    'exp2': ('控制变量：with_articles true/false', exp2_with_articles),
    'exp3': ('控制变量：pvip 0/1', exp3_pvip),
    'exp4': ('控制变量：size 20/50/100', exp4_size),
    'exp5': ('控制变量：prev 游标 0/20/40', exp5_prev),
    'exp6': ('全类型×pvip 全集扫描+目标检索', exp6_full_sweep),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exp', help='只跑某个实验，如 exp2')
    ap.add_argument('--type', type=int, help='exp6 只扫该 product_type')
    ap.add_argument('--proxy', help='如 http://127.0.0.1:7897')
    ap.add_argument('--out', default='lab_results.json', help='结果输出文件')
    args = ap.parse_args()

    proxy = args.proxy
    results = {}
    names = [args.exp] if args.exp else list(EXPERIMENTS.keys())
    for name in names:
        if name not in EXPERIMENTS:
            print(f'未知实验 {name}')
            continue
        title, fn = EXPERIMENTS[name]
        print(f'\n===== {name}: {title} =====')
        if name == 'exp6' and args.type is not None:
            res = fn(proxy=proxy, only_type=args.type)
        else:
            res = fn(proxy=proxy)
        results[name] = res
        print(json.dumps(res, ensure_ascii=False, indent=2))

    Path(args.out).write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n[done] 结果已写入 {args.out}')


if __name__ == '__main__':
    main()

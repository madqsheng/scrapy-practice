import os
import scrapy
import json
from pathlib import Path

from jikeshijian.items import ArticleItem, CourseItem
# 复用 pipeline 的文件名安全化规则，保证「跳过判断」与「落盘命名」完全一致，不会比错文件。
from jikeshijian.pipelines import _safe_filename

# 离线课程索引（由 sync_course_index.py 生成，提交进仓库）。优先用它离线解析课名，
# 不再依赖运行时接口；索引缺失时才回退到 learn/product + product_list 运行时解析。
_INDEX_PATH = Path(__file__).resolve().parent.parent / 'course_index.json'


class JkArticleSpider(scrapy.Spider):
    name = "jk"
    allowed_domains = ["time.geekbang.org"]
    start_urls = ["http://time.geekbang.org/"]

    # 我的课程：返回课程id
    product_url = "https://time.geekbang.org/serv/v3/learn/product"

    # 指定获取的课程，返回该课程的每一篇文章的id
    articles_url = "https://time.geekbang.org/serv/v1/column/articles"

    # 具体文章的内容，需要id
    article_url = "https://time.geekbang.org/serv/v1/article"

    # 文章评论区
    comment_url = "https://time.geekbang.org/serv/v4/comment/list"

    # 全站课程目录（含 VIP 可访问但未单买的课程），用于按名解析课程 id
    product_list_url = "https://time.geekbang.org/serv/v4/pvip/product_list"

    def __init__(self, limit=None, courses=None, course_ids=None, force=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._products = []  # 跨页累加「我的课程」，最后统一筛选

        # force：强制全量重爬开关（-a force=1）。默认 False（增量模式：本地已存的
        # 文章 html 自动跳过，只补缺失/新增）。设 True 时忽略本地已存、全部重新抓取。
        self.force = str(force or '').strip() in ('1', 'true', 'True', 'yes')

        # 增量统计：本次新抓 / 跳过已存 的篇数，结束时汇总打印
        self._fetched_count = 0
        self._skipped_count = 0

        # courses：命令行指定要爬的课程名（精确匹配 title）。
        #   支持两种写法：
        #     逗号分隔字符串  -a courses="A,B"
        #     JSON 数组字符串  -a courses='["A","B"]'（课程名本身含逗号时用）
        #   若命令行未传，则回退到 settings.py 里的 MY_COURSES。
        self.courses = self._parse_courses_arg(courses)

        # course_ids：命令行直接指定课程 id（绕过名称解析）。用于「VIP 可看但
        # product_list 目录翻不到」的课程。支持逗号分隔或 JSON 数组。
        # 也可在 settings.py 用 MY_COURSE_IDS 持久化。
        self.course_ids = self._parse_course_ids(course_ids)

        # limit：只爬「我的课程」列表里的前 N 门；不传则爬全部。
        if limit is not None:
            try:
                self.limit = int(limit)
            except (TypeError, ValueError):
                self.logger.warning("limit 参数无效（%r），将爬取全部课程", limit)
                self.limit = None
        else:
            self.limit = None

        # 一旦指定了 courses，limit 失效（指定优先于前 N）
        if self.courses:
            self.limit = None

    @staticmethod
    def _parse_courses_arg(courses):
        """把 -a courses=... 解析成课程名列表；未传返回 None。"""
        if courses is None:
            return None
        if isinstance(courses, (list, tuple)):
            return [str(c).strip() for c in courses if str(c).strip()]
        s = str(courses).strip()
        if not s:
            return None
        # 形如 ["A","B"] 的 JSON 数组：避免课程名含逗号被误切
        if s.startswith('['):
            try:
                import json as _json
                val = _json.loads(s)
                if isinstance(val, list):
                    return [str(c).strip() for c in val if str(c).strip()]
            except Exception:
                pass
        # 否则按逗号分隔
        return [p.strip() for p in s.split(',') if p.strip()]

    @staticmethod
    def _parse_course_ids(val):
        """把 -a course_ids=... 解析成 int 列表；未传返回 []。"""
        if val is None:
            return []
        if isinstance(val, (list, tuple)):
            out = []
            for x in val:
                try:
                    out.append(int(x))
                except (TypeError, ValueError):
                    pass
            return out
        s = str(val).strip()
        if not s:
            return []
        if s.startswith('['):
            try:
                import json as _json
                v = _json.loads(s)
                if isinstance(v, list):
                    out = []
                    for x in v:
                        try:
                            out.append(int(x))
                        except (TypeError, ValueError):
                            pass
                    return out
            except Exception:
                pass
        out = []
        for x in s.split(','):
            x = x.strip()
            if x.isdigit():
                out.append(int(x))
        return out

    async def start(self):
        # Scrapy 2.13+ 用 async def start() 取代旧的 start_requests()
        # 构造「我的课程」请求体。指定课程模式下去掉 type 过滤，否则非专栏课程
        # （p29/q/p35/c3 等）会被漏掉，导致按名匹配不到。
        # 离线课名解析放在 _resolve_courses（同步回调）里做，这里只负责拿到课程列表。
        product_data = dict(self.settings['MY_PRODUCT_DATA'])
        wanted = self._get_wanted()
        if wanted:
            # 指定课程模式：去掉 type 过滤，否则非专栏课程（p29/q/p35/c3 等）
            # 会被漏掉，导致按名匹配不到。
            product_data.pop('type', None)
        self._product_body = product_data
        yield scrapy.Request(
            url=self.product_url,  # 获取课程
            method='POST',
            headers={'Referer': 'https://time.geekbang.org/dashboard/course'},
            body=json.dumps(self._product_body),
            callback=self.parse_product
        )

    # 解析我的课程列表（支持跨页累加，最后按指定课程名 / limit 筛选）
    def parse_product(self, response):
        data = json.loads(response.text)
        payload = data.get('data') or {}
        self._products.extend(payload.get('products', []))

        page = payload.get('page', {}) or {}
        if page.get('more'):
            # 还有下一页：累加所有「我的课程」，确保指定课程哪怕在后面几页也能被找到
            step = self._product_body.get('size', 100) or 100
            self._product_body = dict(self._product_body)
            self._product_body['prev'] = self._product_body.get('prev', 0) + step
            yield scrapy.Request(
                url=self.product_url,
                method='POST',
                headers={'Referer': 'https://time.geekbang.org/dashboard/course'},
                body=json.dumps(self._product_body),
                callback=self.parse_product
            )
            return

        # —— 所有课程收集完毕，开始解析 ——
        yield from self._resolve_courses()

    def _get_wanted(self):
        """返回指定课程名列表；无指定则返回 None（表示走 全部/limit 模式）。

        优先级：-a courses  >  -a limit  >  settings.MY_COURSES  >  全部。
        即：命令行 courses 优先；其次若给了 limit 则按数量爬前 N 门；再次用
        配置文件 MY_COURSES；都没有才爬「我的课程」全部。这样即便 MY_COURSES
        非空，-a limit=N 仍能正常触发数量模式。
        """
        if self.courses:
            return self.courses
        if self.limit is not None:
            return None
        mc = list(self.settings.get('MY_COURSES', []) or [])
        return mc if mc else None

    def _is_specified_mode(self):
        """是否处于「指定课程」模式：传了课程名 或 直接指定了课程 id。"""
        return (self._get_wanted() is not None) or bool(self.course_ids)

    def _resolve_courses(self):
        """根据模式筛选课程并下发文章列表请求。"""
        wanted = self._get_wanted()
        if not wanted and not self.course_ids:
            # 全部 / limit 模式：直接发「我的课程」里收集到的课程
            products = self._products
            if self.limit is not None:
                products = products[:self.limit]
            yield from self._emit_resolved(products)
            return

        # 指定课程模式：优先用离线索引 course_index.json 离线解析（不发网络、名字匹配更稳）
        resolver = self._load_course_index()
        if resolver is not None:
            yield from self._resolve_offline(wanted, resolver)
            return

        # —— 离线索引缺失：回退到运行时解析（learn/product -> product_list） ——
        wanted_set = {str(w).strip() for w in wanted} if wanted else set()
        by_title = {str(p.get('title', '')).strip(): p for p in self._products}
        found = set(by_title.keys()) & wanted_set
        missing = wanted_set - found

        if not missing:
            yield from self._emit_resolved([by_title[t] for t in found])
            return

        # 指定课程中有名字没在「我的课程」匹配到：可能是 VIP 可看但未单买，
        # 回退到全站目录 product_list 继续按名匹配（VIP 能访问的课程大多在里面）。
        self.logger.info(
            "以下 %d 门未在「我的课程」匹配到，转从全站目录(product_list)解析（VIP 可访问课程）：%s",
            len(missing), "、".join(sorted(missing))
        )
        self._missing = missing
        self._catalog = {}
        self._catalog_prev = 0
        self._pl_pages = 0
        yield from self._fetch_product_list_page()

    @staticmethod
    def _load_course_index():
        """载入离线课程索引 course_index.json，返回 课程名 -> (id, 课程名) 解析表（课程名与 id 一一对应）。
        文件不存在或读取失败返回 None（调用方回退到运行时解析）。"""
        if not _INDEX_PATH.exists():
            return None
        try:
            with open(_INDEX_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("course_index.json 读取失败，回退运行时解析：%s", e)
            return None
        by_title = data.get('by_title') or {}
        resolver = {}
        for t, i in by_title.items():
            resolver[str(t).strip()] = (i, str(t).strip())
        return resolver

    def _resolve_offline(self, wanted, resolver):
        """用离线索引解析指定课程名，直接拿到 id 下发，不发任何查目录的网络请求。
        wanted 为 None 表示全部/limit 模式（不应走到这里）。"""
        wanted_set = {str(w).strip() for w in wanted} if wanted else set()
        resolved = []
        missing = []
        for name in wanted_set:
            if name in resolver:
                cid, title = resolver[name]
                resolved.append({'id': cid, 'title': title, 'intro_html': '', 'column': {}})
            else:
                missing.append(name)
        # 直接指定 id 的，追加（按 id 去重，避免 EXTRA 把同名不同写法映射成同一门重复爬）
        if self.course_ids:
            resolved_ids = {int(c['id']) for c in resolved}
            for cid in self.course_ids:
                if cid in resolved_ids:
                    continue
                resolved.append({'id': cid, 'title': str(cid), 'intro_html': '', 'column': {}})
        seen = set()
        uniq = []
        for c in resolved:
            if c['id'] in seen:
                continue
            seen.add(c['id'])
            uniq.append(c)
        resolved = uniq

        for m in sorted(missing):
            self.logger.warning(
                "课程「%s」在离线索引(course_index.json)中未匹配到，已跳过。"
                "若确属 VIP 可看但未列目录的课程，请把课程页 id 加到 settings.MY_COURSE_IDS 或 -a course_ids", m
            )
        yield from self._emit_courses(resolved)

    def _emit_resolved(self, resolved_courses):
        """在按名解析出的课程基础上，追加「直接指定 id」的课程（MY_COURSE_IDS /
        -a course_ids），再统一下发。仅指定课程模式下才追加 id。"""
        if self._is_specified_mode() and self.course_ids:
            id_title = {}
            for p in self._products:
                if p.get('id') is not None:
                    id_title[int(p['id'])] = p.get('title', str(p['id']))
            for p in getattr(self, '_catalog', {}).values():
                if p.get('id') is not None:
                    id_title.setdefault(int(p['id']), p.get('title', str(p['id'])))
            resolved_ids = {int(c['id']) for c in resolved_courses if c.get('id') is not None}
            extra = []
            for cid in self.course_ids:
                if cid in resolved_ids:
                    continue
                extra.append({'id': cid, 'title': id_title.get(cid, str(cid)),
                              'intro_html': '', 'column': {}})
            resolved_courses = resolved_courses + extra
        yield from self._emit_courses(resolved_courses)

    def _emit_courses(self, courses):
        for course in courses:
            course_item = CourseItem()
            course_item['course_id'] = course['id']
            course_item['course_name'] = course['title']
            course_item['course_description'] = course.get('intro_html', '')
            course_item['course_catalog_pic_url'] = (course.get('column') or {}).get('catalog_pic_url', '')
            yield course_item

            self.settings['COURSE_DATA']['cid'] = str(course['id'])
            Referer = 'https://time.geekbang.org/column/intro/{}?tab=catalog'.format(
                course['id'])
            yield scrapy.Request(
                url=self.articles_url,  # 获取课程里的文章
                method='POST',
                headers={'Referer': Referer},
                body=json.dumps(self.settings['COURSE_DATA']),
                callback=self.parse_course,
                meta={
                    'course_id': course['id'],
                    'course_name': course['title']
                }
            )

    def _fetch_product_list_page(self):
        body = {
            "tag_ids": [], "product_type": 0, "product_form": 0, "pvip": 0,
            "prev": self._catalog_prev, "size": 20, "sort": 8, "with_articles": False
        }
        yield scrapy.Request(
            url=self.product_list_url,
            method='POST',
            headers={'Referer': 'https://time.geekbang.org/dashboard/course'},
            body=json.dumps(body),
            callback=self.parse_product_list,
            errback=self._pl_errback
        )

    def _pl_errback(self, failure):
        """product_list 某页请求失败时：停止翻页，用已收集数据发出已命中课程。"""
        self.logger.warning("product_list 请求失败，停止目录翻页并以已收集数据发出：%s", failure.value)
        by_title = {str(p.get('title', '')).strip(): p for p in self._products}
        by_title.update(getattr(self, '_catalog', {}))
        wanted_set = {str(w).strip() for w in self._get_wanted()}
        resolved = [by_title[t] for t in wanted_set if t in by_title]
        yield from self._emit_resolved(resolved)

    def parse_product_list(self, response):
        payload = (json.loads(response.text) or {}).get('data') or {}
        products = payload.get('products', []) or []
        for p in products:
            title = str(p.get('title', '')).strip()
            if title:
                self._catalog[title] = p

        # 已经在本页解析出来的，从 missing 中剔除
        resolved_now = set(self._catalog.keys()) & self._missing
        self._missing -= resolved_now

        page = payload.get('page', {}) or {}
        self._pl_pages = getattr(self, '_pl_pages', 0) + 1
        # 继续翻下一页的条件：仍有缺失 + 接口说还有 + 本页有数据 + 不超过 10 页
        # （该接口对单账号实际只吐 ~40 门就会 more:false，加页面数与空页保护防卡死）
        if self._missing and page.get('more') and products and self._pl_pages < 10:
            self._catalog_prev += len(products)
            yield from self._fetch_product_list_page()
            return

        # 目录翻完（或全部命中）：汇总 learn + catalog，发出命中的课程
        if self._missing:
            self.logger.warning(
                "以下课程在「我的课程」与全站目录(product_list)中均未匹配到（请检查名称是否完全一致；"
                "若确属 VIP 可看但目录翻不到的课程，可在 settings.MY_COURSE_IDS 直接填课程 id）：%s",
                "、".join(sorted(self._missing))
            )
        by_title = {str(p.get('title', '')).strip(): p for p in self._products}
        by_title.update(self._catalog)
        wanted_set = {str(w).strip() for w in self._get_wanted()}
        resolved = [by_title[t] for t in wanted_set if t in by_title]
        yield from self._emit_resolved(resolved)

    # 解析课程里的文章列表
    def parse_course(self, response):
        json_response = json.loads(response.text)
        articles = json_response['data']['list']
        file_dir = self.settings.get('FILES_STORE') or ''
        for article in articles:
            course_id = response.meta['course_id']
            course_name = response.meta['course_name']
            article_id = article['id']
            article_title = article['article_title']

            # —— 增量/续爬：本地已存该文章 html 且未强制重爬，则跳过（不重写、不浪费请求）——
            # 命名规则与 pipeline 完全一致（_safe_filename），目录结构 <课程名>/<文章标题>.html。
            if not self.force and file_dir:
                existing = os.path.join(
                    file_dir,
                    _safe_filename(course_name),
                    _safe_filename(article_title) + '.html',
                )
                if os.path.exists(existing):
                    self._skipped_count += 1
                    self.logger.debug("已存在，跳过（增量）：%s/%s", course_name, article_title)
                    continue

            self._fetched_count += 1
            self.settings['ARTICLE_DATA']['id'] = str(article_id)
            Referer = 'https://time.geekbang.org/column/article/{}'.format(
                article_id)
            yield scrapy.Request(
                url=self.article_url,  # 获取课程里的文章
                method='POST',
                headers={'Referer': Referer},
                body=json.dumps(self.settings['ARTICLE_DATA']),  # 表单数据，以字典形式提供
                callback=self.parse_article,
                meta={
                    'course_id': course_id,
                    'course_name': course_name,
                    'article_id': article_id,
                    'article_title': article_title
                }
            )

    def parse_article(self, response):
        meta = response.meta
        article = json.loads(response.text)['data']

        # 构建 item 草稿，正文先填好；评论区分「最新」(sort=0) 和「精选」(sort=1)
        # 两次请求获取。采用链式（先最新后精选）+ errback 兜底，保证即使某个
        # 评论请求失败（如 451 限流），正文也一定会落盘，不会整篇丢失。
        item = ArticleItem()
        item['course_id'] = meta['course_id']
        item['course_name'] = meta['course_name']
        item['article_id'] = meta['article_id']
        item['article_title'] = meta['article_title']
        item['article_content'] = article['article_content']
        item['article_audio_url'] = article['audio_download_url']
        item['comments'] = None
        item['comments_essence'] = None

        Referer = 'https://time.geekbang.org/column/article/{}'.format(
            meta['article_id'])

        # 先取「最新」（sort=0），成功后再取「精选」（sort=1）
        yield scrapy.Request(
            url=self.comment_url,
            method='POST',
            headers={'Referer': Referer},
            body=json.dumps({"aid": meta['article_id'], "prev": 0, "sort": 0}),
            callback=self.parse_comments,
            errback=self.parse_comments_err,
            meta={'item': item, 'sort': 0, 'referer': Referer}
        )

    def parse_comments(self, response):
        meta = response.meta
        item = meta['item']
        sort = meta['sort']
        data = json.loads(response.text)['data']
        if sort == 0:
            item['comments'] = data
            # 接着请求「精选」（sort=1）
            Referer = meta['referer']
            yield scrapy.Request(
                url=self.comment_url,
                method='POST',
                headers={'Referer': Referer},
                body=json.dumps({"aid": item['article_id'], "prev": 0, "sort": 1}),
                callback=self.parse_comments,
                errback=self.parse_comments_err,
                meta={'item': item, 'sort': 1, 'referer': Referer}
            )
        else:
            item['comments_essence'] = data
            yield item

    def parse_comments_err(self, failure):
        """评论请求失败（如 451 限流）兜底：缺失部分置空，仍保证正文落盘。"""
        meta = failure.request.meta
        item = meta['item']
        sort = meta['sort']
        empty = {'list': [], 'page': {'count': 0, 'more': False}}
        if sort == 0:
            item['comments'] = empty
            # 最新失败也继续尝试精选，尽量多存
            Referer = meta['referer']
            yield scrapy.Request(
                url=self.comment_url,
                method='POST',
                headers={'Referer': Referer},
                body=json.dumps({"aid": item['article_id'], "prev": 0, "sort": 1}),
                callback=self.parse_comments,
                errback=self.parse_comments_err,
                meta={'item': item, 'sort': 1, 'referer': Referer}
            )
        else:
            item['comments_essence'] = empty
            yield item

    def closed(self, reason):
        """爬虫结束时打印增量汇总，让你一眼确认「续上了」还是「全量重爬了」。"""
        mode = "强制全量重爬" if self.force else "增量（跳过已存）"
        self.logger.info(
            "【增量汇总】模式=%s | 本次新抓 %d 篇 | 跳过已存 %d 篇",
            mode, self._fetched_count, self._skipped_count,
        )

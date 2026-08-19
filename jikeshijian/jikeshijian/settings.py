# Scrapy settings for jikeshijian project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "jikeshijian"

SPIDER_MODULES = ["jikeshijian.spiders"]
NEWSPIDER_MODULE = "jikeshijian.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "jikeshijian (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "jikeshijian.middlewares.JikeshijianSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    "jikeshijian.middlewares.JikeshijianDownloaderMiddleware": 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    "jikeshijian.pipelines.JikeshijianPipeline": 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# # 在settings.py中配置中间件
DOWNLOADER_MIDDLEWARES = {
    'jikeshijian.middlewares.CustomHeadersMiddleware': 301,
}

MY_COOKIE = 'gksskpitn=c858b310-18ef-42d7-9205-8b9e5ad63358; Hm_lvt_022f847c4e3acd44d4a2481d9187f1e6=1786826889; HMACCOUNT=4725909138C90DBF; _ga=GA1.2.1150421742.1786826889; _gid=GA1.2.123835391.1786826889; LF_ID=f8542e3-32def4e-e87388d-beb71c0; GCID=4e942af-a9f470e-90062ac-a421894; Hm_lvt_59c4ff31a9ee6263811b23eb921a5083=1786903648; GRID=4e942af-a9f470e-90062ac-a421894; _tea_utm_cache_20000743={%22utm_source%22:%22geektime_search%22%2C%22utm_medium%22:%22geektime_search%22%2C%22utm_campaign%22:%22geektime_search%22%2C%22utm_term%22:%22geektime_search%22%2C%22utm_content%22:%22geektime_search%22}; gk_process_ev={%22count%22:1%2C%22utime%22:1786931419430%2C%22referrer%22:%22https://time.geekbang.org/resource?tab=lecture&c=0%22%2C%22target%22:%22page_geektime_login%22}; _ga_JW698SFNND=GS2.2.s1786931420$o3$g0$t1786931420$j60$l0$h0; GCESS=BgME4miCag0BAQQEAI0nAAEIbT4UAAAAAAAFBAAAAAACBOJogmoIAQMLAgYADAEBCgQAAAAABgRNlpYpBwTVxWWTCQEB; tfstk=gV0Z38_t1FLZSLpoab42Ulo14MzTWrJWgqwbijc01R2MXdeq3bMClo066ZJq3xrjCj4_mtynKRMsfj1tvYGl5VtTlZzTkrvWFUTS1fUYoMRGlyfT-SV4iENcow4TGgc5zXYS6fChk7c2rUt4DAB0I-D0jkf3MJbgixVGKBP0GOjcSxcHTJFRoGqgiXc3Z5z0nx4DTX2LirVinrAEtJFmK9HmBwyUjUcrrcGhkoqaEf2Fzb3Lsa22yRbcz2PZT8cMqZbm85rZR1fEW2ZsmbE-5VYVJPGrxyVS6F7UrfVrCJMkrwznOXDb2DpAPkHEuu3g4sA3KVkEWPD6makz7xroSk5clflEfyPnrIs8d2ysnVrHNarb-4ZuSDtpCoaaax0tQs7mEXGSWk32U92xf7U3NfLN8zcgig5NHWv0TqnNnirg9WyWTBukW7-e7Xrq3iIYYHFUFQdRmiXjxWyWTCIADkozT8OoR; _ga_03JGDGP9Y3=GS2.2.s1786934689$o5$g1$t1786936120$j60$l0$h0; Hm_lpvt_022f847c4e3acd44d4a2481d9187f1e6=1786937311; Hm_lpvt_59c4ff31a9ee6263811b23eb921a5083=1786937311; acw_tc=276ae9b017869397595096311ee0f9a14cd2c8e717f74da40cd425bbb12d34; __tea_cache_tokens_20000743={%22web_id%22:%227674692733558157324%22%2C%22user_unique_id%22:%221326701%22%2C%22timestamp%22:1786940842026%2C%22_type_%22:%22default%22}; SERVERID=1fa1f330efedec1559b3abbcb6e30f50|1786940844|1786931417'
MY_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
MY_REFERER = 'https://time.geekbang.org/'


# 获取我的课程的请求表单
MY_PRODUCT_DATA = {
    "desc": 'true',
    "expire": 1,  # 是否过期，1未过期，2过期
    "last_learn": 0,
    "learn_status": 0,  # 是否学完 0全部，1未，2学完
    "prev": 0,
    "size": 100,  # 数量
    "sort": 1,  # 排序方法
    "type": "c1",  # 课程类型：c1专栏，c3视频，d每日一课，p公开课，q大厂案例，其他x
    'with_learn_count': 1
}

# 指定课程模式（可选）：只爬这里列出的课程。课名解析改用离线索引
#   jikeshijian/jikeshijian/course_index.json（课名↔id 一一对应，无 EXTRA / 无双字段），
#   由第四种模式 `scrapy crawl jk -a rebuild_index=1` 重建（复用本文件 MY_COOKIE）。
#   爬虫运行时优先离线按名→id 匹配，不发网络查目录，稳且不触发限流。
# - 课程名必须和索引里的「规范标题」完全一致，否则匹配不到会被 WARNING+跳过；
#   匹配不到的课，把课程页 id 填到下面 MY_COURSE_IDS（或 -a course_ids="..."）最稳。
# - 索引里的课程目录会随时间变化：更新 MY_COOKIE 后执行
#   scrapy crawl jk -a rebuild_index=1 即可重建刷新。
# - 为空列表时，回退到命令行的 -a limit= / 全部 模式；也可用 -a courses="A,B" 临时指定。
# 优先级：-a courses  >  -a limit  >  MY_COURSES  >  全部。
MY_COURSES = ["Harness Agent 脚手架实战课", "AI Agent 系统设计面试现场", 
              "DeepSeek Harness 极简入门", "Claude Code 工程化实战",
              "生产级 Agent 排雷实战", "AI Agent智能体实战课", "MCP & A2A 前沿实战", 
              "Agent 设计模式之美", "Claude Code 企业级全链路开发实战", "RAG快速开发实战",
              "LangChain实战课","强化学习快速入门与实战"]

# 直接指定课程 id（绕过名称解析）。用于「VIP 可看但 product_list 目录翻不到」的
# 课程：从浏览器课程页 URL（.../column/intro/<id> 或 .../course/intro/<id>）拿到 id 填这里。
# 命令行也可用 -a course_ids="101069801,100617601" 或 -a course_ids='[101069801]' 临时指定。
MY_COURSE_IDS = []


# 获取课程所有文章的请求表单
COURSE_DATA = {
    "cid": "",
    "size": 250,
    "prev": 0,
    "order": "earliest",
    "sample": 'false',
}

#
ARTICLE_DATA = {
    "id": "",
    "include_neighbors": 'true',
    "is_freelyread": 'true'
}

DOWNLOAD_DELAY = 10  # 设置下载延迟为10秒（正文接口有限流，放慢避免触发 X-GEEK-WARN: rate limit）
CONCURRENT_REQUESTS = 1  # 设置同时只有一个请求
RANDOMIZE_DOWNLOAD_DELAY = True  # 启用随机下载延迟（实际间隔 5~15 秒）
AUTOTHROTTLE_ENABLED = True  # 根据服务器延迟自动调速，遇到限流更温和
AUTOTHROTTLE_START_DELAY = 10
AUTOTHROTTLE_MAX_DELAY = 60
# 设置日志级别
# LOG_LEVEL = 'DEBUG'

# 文件保存：统一落到项目根目录下的 resource/<BOT_NAME>（不再写死绝对路径）
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FILES_STORE = str(_REPO_ROOT / 'resource' / BOT_NAME)
ITEM_PIPELINES = {
    'jikeshijian.pipelines.CoursePipeline': 300,
    'jikeshijian.pipelines.ArticlePipeline': 301,
}

# MemoryUsage 扩展依赖 Unix 专属的 resource.getrusage()，Windows 上不可用会报错。
# 禁用后对爬取无任何影响（仅不再打印内存占用）。
MEMUSAGE_ENABLED = False

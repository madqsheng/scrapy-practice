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

MY_COOKIE = 'GCID=8ace22c-100e4df-fcdeff8-89487d0; GRID=8ace22c-100e4df-fcdeff8-89487d0; LF_ID=8ace22c-100e4df-fcdeff8-89487d0; _ga=GA1.2.2096348218.1695921922; _gid=GA1.2.1248043860.1695921922; Hm_lvt_59c4ff31a9ee6263811b23eb921a5083=1693581532,1695921922; Hm_lvt_022f847c4e3acd44d4a2481d9187f1e6=1693581532,1695921922; _ga_03JGDGP9Y3=GS1.2.1695921922.1.1.1695922447.0.0.0; _ga_JW698SFNND=GS1.2.1695921929.1.1.1695922447.0.0.0; gksskpitn=29864ff7-fea9-4c2e-8e84-4f24ebf605c5; gk_process_ev={%22count%22:2%2C%22utime%22:1695973067793%2C%22referrer%22:%22https://time.geekbang.org/%22%2C%22target%22:%22page_geektime_login%22%2C%22referrerTarget%22:%22page_geektime_login%22}; GCESS=Bg0BAQgBAwYEKBk1pwIEzn4WZQkBAQcEnFwyIAEIbT4UAAAAAAADBM5.FmULAgYABAQAjScACgQAAAAABQQAAAAADAEB; __tea_cache_tokens_20000743={%22web_id%22:%227282437231590009089%22%2C%22user_unique_id%22:%221326701%22%2C%22timestamp%22:1695976508792%2C%22_type_%22:%22default%22}; SERVERID=1fa1f330efedec1559b3abbcb6e30f50|1695976511|1695973060'
MY_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.43'
MY_REFERER = 'https://time.geekbang.org/dashboard/course'


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

DOWNLOAD_DELAY = 2  # 设置下载延迟为2秒
CONCURRENT_REQUESTS = 1  # 设置同时只有一个请求
RANDOMIZE_DOWNLOAD_DELAY = True  # 启用随机下载延迟
# 设置日志级别
# LOG_LEVEL = 'DEBUG'

#文件保存
FILES_STORE = 'E:\极客时间'
ITEM_PIPELINES = {
    'jikeshijian.pipelines.CoursePipeline': 300,
    'jikeshijian.pipelines.ArticlePipeline': 301,
}

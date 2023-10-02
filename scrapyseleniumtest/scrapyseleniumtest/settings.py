# Scrapy settings for scrapyseleniumtest project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'scrapyseleniumtest'

SPIDER_MODULES = ['scrapyseleniumtest.spiders']
NEWSPIDER_MODULE = 'scrapyseleniumtest.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'scrapyseleniumtest (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'scrapyseleniumtest.middlewares.ScrapyseleniumtestSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'scrapyseleniumtest.middlewares.ScrapyseleniumtestDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'scrapyseleniumtest.pipelines.ScrapyseleniumtestPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

KEYWORDS = ['iPad']
MAX_PAGE = 2
SELENIUM_TIMEOUT = 20

ITEM_PIPELINES = {'scrapyseleniumtest.pipelines.MongoPipeline': 300,}
MONGO_URI = 'localhost'
MONGO_DB = 'taobao'

MY_COOKIE_DICT = {
    'cna':'QkEKHVP1QwgBASQIglYFTWYq',
    'cookie2':'1f2237fa4c0a82ccb144cfb5bd2e546e',
    't':'fbd33a0ffd721e3963a12722991476f7',
    '_tb_token_':'fb33d3364b33b',
    '_m_h5_tk':'28d59832c71e97fdd5c61819394950da_1694798260700',
    '_m_h5_tk_enc':'6088a2e064456fb93ad3a024aa88f534',
    '_samesite_flag_':'true',
    'xlly_s':'1',
    'sgcookie':'E100iuGCnI5M%2FvZDlLw3%2FeGH4UN%2FyOt%2BS9UyFJ5jjbxR2TbHm9ixNWO5FvHIn0RjYGLk%2FeJ1BFIBQO%2FJnnOjdPptkp8S0KxEHx9PBQJ0%2FJfDA57%2FsKgjp1ZneTQn8TlnZsnf',
    'unb':'1833322767',
    'uc3':'vt3=F8dCsGSMOUyPrwMkLrE%3D&nk2=F5RHpCmJ3cHHp74%3D&lg2=WqG3DMC9VAQiUQ%3D%3D&id2=UonYss9%2BqFn%2Flw%3D%3D',
    'csg':'77acf28c',
    'lgc':'tb252715209',
    'cancelledSubSites':'empty',
    'cookie17':'UonYss9%2BqFn%2Flw%3D%3D',
    'dnk':'tb252715209',
    'skt':'592b9c44eade4b23',
    'existShop':'MTY5NDc5MTExMQ%3D%3D',
    'uc4':'id4=0%40UOEy1aPcASqNWVcXZfxQmz0ZOirQ&nk4=0%40FY4Mthd0r%2BPYagEtXE5eCzR9yg2KKw%3D%3D',
    'tracknick':'tb252715209',
    '_cc_':'Vq8l%2BKCLiw%3D%3D',
    '_l_g_':'Ug%3D%3D',
    'sg':'97d',
    '_nk_':'tb252715209',
    'cookie1':'UoZNTeizO0p4faZLm3ySOX1oih5um7Onme1sFL9axQE%3D',
    'mt':'ci=25_1',
    'thw':'cn',
    'uc1':'cookie16=W5iHLLyFPlMGbLDwA%2BdvAGZqLg%3D%3D&pas=0&cookie14=Uoe9aVdKbyBgqg%3D%3D&cookie21=WqG3DMC9Fb5mPLIQo9kR&cookie15=U%2BGCWk%2F75gdr5Q%3D%3D&existShop=false',
    'x5sec':'7b22617365727665723b32223a226336643031356530633864353462623565646530633038366532633564363861434e76726b616747454e3355674b66342f2f2f2f2f774561444445344d7a4d7a4d6a49334e6a63374e5444736c347a5441304144222c22733b32223a2233376564333937633338306334336366227d',
    'JSESSIONID':'4651C4E7662805AC1FEE5C4F282301D6',
    'l':'fBaX_KveNKdV2Cg9BOfwFurza77OsIRAguPzaNbMi9fP935p5UoCW1h8lyY9CnGVF62BR3-WjmOpBeYBqIccSQLy2j-la1Dmnm9SIEf..',
    'tfstk':'dUvBHBOF3y4IugssNkiwG5iSk1WSbeM4RusJm3eU29BdyCtDPwoot9R1PFL1JJont_QW-9CkTa7FPTtklcuq3x-HxTf-umkqSIthE60ZbPk2xHXuA3dVAxy5xnrlUbHa8DhM2VwgQ-0JcfYjG-evCG3lkH_PjGv1x6_A6N6a5-7brRF5og25fZosf7VoegsoC',
    'isg':'BFNThby-Mn7kP_8ZUZHySzNs4td9COfKOZIlVQVwv3KphHMmjdqNG6HWuvTqJD_C'
}
DOWNLOADER_MIDDLEWARES = {
    'scrapyseleniumtest.middlewares.MyCookieMiddleware': 543,  # 调整优先级根据需求
    'scrapyseleniumtest.middlewares.SeleniumMiddleware': 544,
}

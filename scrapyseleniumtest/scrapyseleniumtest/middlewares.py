# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class ScrapyseleniumtestSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyseleniumtestDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.http import HtmlResponse
from logging import getLogger 

class SeleniumMiddleware():
    def __init__(self, timeout=None, service_args=[]):
        self.logger = getLogger(__name__)
        self.timeout = timeout
        options=webdriver.chrome.options.Options()
        #禁用Chrome浏览器中的自动化检测功能
        options.add_argument("--disable-blink-features=AutomationControlled")  
        # # 创建一个 Chrome 浏览器实例，并设置为无头模式
        # options.add_argument("--headless")  # 启用无头模式
        # 设置User-Agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36======="
        options.add_argument(f"user-agent={user_agent}")

        self.browser = webdriver.Chrome(chrome_options=options)

        self.browser.set_window_size(1400, 700)
        self.browser.set_page_load_timeout(self.timeout)
        # 创建一个等待对象，使用这个对象执行等待操作,用于等待特定条件出现或超时的控制
        self.wait = WebDriverWait(self.browser, self.timeout)

    def __del__(self):
        self.browser.close()

    def process_request(self, request, spider):
        self.logger.debug('selenium is Starting')
        page = request.meta.get('page', 1)
        try:
            self.browser.get(request.url)
            for cookie_name, cookie_value in request.cookies.items():
                self.browser.add_cookie({'name': cookie_name, 'value': cookie_value})

            if page > 1:
                input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.next-input.next-medium.next-pagination-jump-input> input')))
                submit = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.next-pagination-jump-go> span')))
                input.clear()
                input.send_keys(page)
                submit.click()
            self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'span.next-pagination-display> em'), str(page)))
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.Content--contentInner--QVTcU0M a.Card--doubleCardWrapper--L2XFE73')))
            return HtmlResponse(url=request.url, body=self.browser.page_source, request=request, encoding='utf-8', status=200)
        except TimeoutException:
            return HtmlResponse(url=request.url, status=500, request=request)

    @classmethod
    def from_crawler(cls, crawler):
        # return cls(timeout=crawler.settings.get('SELENIUM_TIMEOUT'),
        #            service_args=crawler.settings.get('PHANTOMJS_SERVICE_ARGS'))
        return cls(timeout=crawler.settings.get('SELENIUM_TIMEOUT'))
    
class MyCookieMiddleware:
    def __init__(self, cookie_dict):
        self.cookie_dict = cookie_dict

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        settings = crawler.settings
        cookie_dict = settings.get('MY_COOKIE_DICT', {})
        return cls(cookie_dict)

    def process_request(self, request, spider):
        # 添加cookie到请求中
        # request.cookies.update(self.cookie_dict)
        request.cookies=self.cookie_dict
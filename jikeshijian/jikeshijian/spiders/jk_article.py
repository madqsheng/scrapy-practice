import scrapy
import json

from jikeshijian.items import ArticleItem, CourseItem


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

    def __init__(self, limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # limit：只爬「我的课程」列表里的前 N 门；不传则爬全部。
        # 实际课程数少于 limit 时不会报错，有多少爬多少。
        if limit is not None:
            try:
                self.limit = int(limit)
            except (TypeError, ValueError):
                self.logger.warning("limit 参数无效（%r），将爬取全部课程", limit)
                self.limit = None
        else:
            self.limit = None

    async def start(self):
        # Scrapy 2.13+ 用 async def start() 取代旧的 start_requests()
        yield scrapy.Request(
            url=self.product_url,  # 获取课程
            method='POST',
            headers={'Referer': 'https://time.geekbang.org/dashboard/course'},
            body=json.dumps(self.settings['MY_PRODUCT_DATA']),
            callback=self.parse_product
        )

    # 解析我的课程列表
    def parse_product(self, response):
        course_item = CourseItem()
        json_response = json.loads(response.text)  # 反序列化
        courses = json_response['data']['products']
        # 按 limit 截取前 N 门；实际课程数不足时切片自动截断，不报错
        if self.limit is not None:
            courses = courses[:self.limit]
        course_list=[]
        for course in courses:
            course_item['course_id'] = course['id']  # int
            course_item['course_name'] = course['title']
            course_item['course_description'] = course['intro_html']
            course_item['course_catalog_pic_url'] = course['column']['catalog_pic_url']
            course_list.append((course['id'],course['title']))
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
                    'course_name':course['title']
                    }
            )

        # for (course_id,course_name) in course_list:
        #     self.settings['COURSE_DATA']['cid'] = str(course_id)
        #     Referer = 'https://time.geekbang.org/column/intro/{}?tab=catalog'.format(
        #         course_id)
        #     yield scrapy.Request(
        #         url=self.articles_url,  # 获取课程里的文章
        #         method='POST',
        #         headers={'Referer': Referer},
        #         body=json.dumps(self.settings['COURSE_DATA']),
        #         callback=self.parse_course,
        #         meta={
        #             'course_id': course_id,
        #             'course_name':course_name
        #             }
        #     )

    # 解析课程里的文章列表
    def parse_course(self, response):
        json_response = json.loads(response.text)
        articles = json_response['data']['list']
        for article in articles:
            course_id = response.meta['course_id']
            course_name = response.meta['course_name']
            article_id = article['id']
            article_title = article['article_title']

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
        meta['article_content'] = article['article_content']
        meta['article_audio_url'] = article['audio_download_url']

        # 正文拿到后继续请求评论区，最后把评论和正文一起交给 pipeline
        comment_body = json.dumps({
            "aid": meta['article_id'],
            "prev": 0,
            "sort": 0
        })
        Referer = 'https://time.geekbang.org/column/article/{}'.format(
            meta['article_id'])
        yield scrapy.Request(
            url=self.comment_url,
            method='POST',
            headers={'Referer': Referer},
            body=comment_body,
            callback=self.parse_comments,
            meta=meta
        )

    def parse_comments(self, response):
        meta = response.meta
        article_item = ArticleItem()
        article_item['course_id'] = meta['course_id']
        article_item['course_name'] = meta['course_name']
        article_item['article_id'] = meta['article_id']
        article_item['article_title'] = meta['article_title']
        article_item['article_content'] = meta['article_content']
        article_item['article_audio_url'] = meta['article_audio_url']
        article_item['comments'] = json.loads(response.text)['data']
        yield article_item

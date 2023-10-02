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

    def start_requests(self):
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
        article_item = ArticleItem()
        article_item['course_id'] = response.meta['course_id']
        article_item['course_name'] = response.meta['course_name']
        article_item['article_id'] = response.meta['article_id']
        article_item['article_title'] = response.meta['article_title']
        article = json.loads(response.text)['data']
        article_item['article_content'] = article['article_content']
        article_item['article_audio_url'] = article['audio_download_url']
        yield article_item

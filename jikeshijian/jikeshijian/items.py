# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

# 课程数据结构
class CourseItem(scrapy.Item):
    course_id = scrapy.Field()                   # 课程id
    course_name = scrapy.Field()                 # 课程名称
    course_description = scrapy.Field()          # 课程简介
    course_catalog_pic_url = scrapy.Field()      # 目录图片链接

# 文章数据结构
class ArticleItem(scrapy.Item):
    article_id = scrapy.Field()  
    article_title = scrapy.Field()
    article_content = scrapy.Field()
    article_audio_url = scrapy.Field()
    course_id = scrapy.Field()
    course_name = scrapy.Field()

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
    comments = scrapy.Field()           # /serv/v4/comment/list 评论（最新，sort=0）
    comments_essence = scrapy.Field()   # 同一接口评论（精选，sort=1）
    article_video_id = scrapy.Field()   # 视频课文章的 video_id（文本/音频课为空）

# 视频数据结构：由 spider 调 video_play_auth + GetPlayInfo 取得播放地址后，
# 交给 ArticlePipeline 用真实播放器（Chrome）解密抓取并合并为 mp4（离线可看）。
class VideoItem(scrapy.Item):
    course_name = scrapy.Field()
    article_title = scrapy.Field()
    video_id = scrapy.Field()
    m3u8_url = scrapy.Field()           # GetPlayInfo 返回的 m3u8 播放地址（备用）
    play_auth = scrapy.Field()          # video_play_auth 返回的 play_auth（base64 JSON）
    plaintext = scrapy.Field()          # GetPlayInfo 返回的 Plaintext（保留备用）

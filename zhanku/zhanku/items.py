# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class ZhankuItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    collection = table = 'chahua'
    id = Field()
    title = Field()
    pageUrl = Field()
    tags = Field()
    sub_name = Field()
    createTime = Field()  #创建时间
    detail_image_url_list = Field()
    viewCount = Field() #阅读量
    year = Field()
    # updateTime = Field()  #更新时间
    # publishTime = Field() #首次审核时间

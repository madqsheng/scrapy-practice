import scrapy
from scrapy import Request, Spider
import json
import time

from zhanku.items import ZhankuItem

class Zhanku2016Spider(scrapy.Spider):
    '''
    字段：recommend_level=2，sort=9
    三个推荐：19，29，39分别对应不同推荐
    最新发布：00
    sub_cate：
        商业插画：2
        艺术插画：292
        创作习作:7
        新锐潮流插画：3

    '''
    name = "zhanku"
    allowed_domains = ["www.zcool.com.cn"]
    start_urls = ["https://www.zcool.com.cn/p1/discover/list?cate=1&sub_cate={}&recommend_level={}&sort={}&p={}&ps=100"]

    def __init__(self, year='2016', *args, **kwargs):
        super(Zhanku2016Spider, self).__init__(*args, **kwargs)
        self.year = int(year)  # 从命令行参数获取年份，默认为2016
    
    def start_requests(self):
        for sub_cate in self.settings.get('SUB_CATE_LIST'):
            for recommend_level in range(self.settings.get('MAX_RECOMMEND_LEVEL')+1):
                for sort in range(self.settings.get('MAX_SORT')+1):
                    for page in range(self.settings.get('MAX_PAGE')):
                        url = self.start_urls[0].format(sub_cate,recommend_level,sort,page)
                        yield Request(url=url, callback=self.parse, dont_filter=True)



    def parse(self, response):
        # print(response.meta.get('page', 1),response.meta.get('sub_name', '1'))
        json_data = json.loads(response.text)
        datas = json_data.get('datas', [])
        for data in datas:
            content = data['content']
            id = content['id']
            title = content['title']
            sub_name = content['subCateStr']
            pageUrl = content['pageUrl']
            tags = content['tags']
            createTime = content['createTime']
            viewCount = content['viewCount']

            create_year = int(time.strftime('%Y', time.localtime(createTime/ 1000)))
            if create_year >= self.year and create_year <= self.year+1:
                yield scrapy.Request(url=pageUrl, 
                                    callback=self.parse_page_detail,
                                    meta={'sub_name':sub_name,
                                            'id':id,
                                            'title':title,
                                            'pageUrl':pageUrl,
                                            'tags':tags,
                                            'createTime':createTime,
                                            'viewCount':viewCount
                                        }
                                    )

    def parse_page_detail(self,response):
        detail_image_url_list=[]
        sections = response.xpath('//section[@class="sc-jqn0up-2 dJEzIw workShowBox"]/section')
        for section in sections:
            detail_image_url = section.xpath('./div/div/img/@data-src').extract_first().split('?')[0]
            detail_image_url_list.append(detail_image_url)

        item = ZhankuItem()
        item['id'] = response.meta['id']
        item['title'] = response.meta['title']
        item['sub_name'] = response.meta['sub_name']
        item['pageUrl'] = response.meta['pageUrl']
        item['tags'] = response.meta['tags']
        item['createTime'] = response.meta['createTime']
        item['detail_image_url_list'] = detail_image_url_list
        item['viewCount'] = response.meta['viewCount']
        item['year'] = self.year
        yield item
        

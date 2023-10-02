# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import csv
import hashlib
import pymysql
import pymongo
from scrapy.exporters import CsvItemExporter
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy import Request
import os
from itemadapter import ItemAdapter


class ZhankuPipeline:
    def process_item(self, item, spider):
        return item


class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_uri=crawler.settings.get('MONGO_URI'),
                   mongo_db=crawler.settings.get('MONGO_DB')
                   )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        self.db[item.collection].insert(dict(item))
        return item

    def close_spider(self, spider):
        self.client.close()


class MysqlPipeline():
    def __init__(self, host, database, user, password, port):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port

    @classmethod
    def from_crawler(cls, crawler):
        return cls(host=crawler.settings.get('MYSQL_HOST'),
                   database=crawler.settings.get('MYSQL_DATABASE'),
                   user=crawler.settings.get('MYSQL_USER'),
                   password=crawler.settings.get('MYSQL_PASSWORD'),
                   port=crawler.settings.get('MYSQL_PORT'),
                   )

    def open_spider(self, spider):
        self.db = pymysql.connect(host=self.host, user=self.user, password=self.password,
                                  database=self.database, charset='utf8', port=self.port)
        self.cursor = self.db.cursor()

    def close_spider(self, spider):
        self.db.close()

    def process_item(self, item, spider):
        data = dict(item)
        keys = ', '.join(data.keys())
        values = ', '.join(['% s'] * len(data))
        sql = 'insert into % s (% s) values (% s)' % (item.table, keys, values)
        self.cursor.execute(sql, tuple(data.values()))
        self.db.commit()
        return item


# 保存图片
class ImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem('Image Downloaded Failed')
        return item

    def get_media_requests(self, item, info):
        for image_url in item['detail_image_url_list']:
            yield scrapy.Request(image_url, meta={'item': item})

    def file_path(self, request, response=None, info=None):
        item = request.meta['item']
        image_url = request.url
        # 获取URL中的文件扩展名
        _, extension = os.path.splitext(image_url)

        # 使用图片的URL的前8个字符的MD5哈希值作为文件名的一部分
        md5_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]

        # 文件夹分类：插画类型，阅读量
        view_count = item['viewCount']
        if view_count >= 100000:
            folder_name = "100000_"
        elif view_count >= 80000:
            folder_name = "80000_100000"
        elif view_count >= 50000:
            folder_name = "50000_80000"
        elif view_count >= 20000:
            folder_name = "20000_50000"
        elif view_count >= 10000:
            folder_name = "10000_20000"
        elif view_count >= 5000:
            folder_name = "5000_10000"
        elif view_count >= 1000:
            folder_name = "1000_5000"
        elif view_count >= 500:
            folder_name = "500_1000"
        else:
            folder_name = "0_500"

        image_name = f"{item['id']}_{md5_hash}{extension}"
        return os.path.join(f"{item['year']}年", item['sub_name'], folder_name, image_name)


# 保存csv
class CsvExportPipeline:
    def __init__(self, file_dir):
        self.file_dir = file_dir  # 设置输出的CSV文件名
        self.exporter = None

    # 创建里文件
    def open_spider(self, spider):
        # 获取Spider中设置的文件名
        year = str(spider.year)
        self.file = open(os.path.join(self.file_dir, year+'.csv'), 'wb')
        self.exporter = CsvItemExporter(self.file, include_headers_line=True)
        self.exporter.start_exporting()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(file_dir=crawler.settings.get('IMAGES_STORE'))

    # 解析item里的内容，保存到item
    def process_item(self, item, spider):
        # 选择要保存的字段
        fields_to_export = ['id', 'pageUrl', 'sub_name',
                            'title', 'viewCount', 'tags']  # 自定义你需要保存的字段列表

        # 创建一个新的字典，只包含要保存的字段
        selected_data = {field: item[field]
                         for field in fields_to_export if field in item}

        # 输出到CSV文件
        self.exporter.export_item(selected_data)
        return item

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

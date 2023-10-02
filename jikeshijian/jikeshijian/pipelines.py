# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import scrapy
from scrapy.exporters import JsonItemExporter
from jikeshijian.items import ArticleItem, CourseItem
import markdown
import requests

#这个库对于代码块的支持不完美
# import html2text
# handler = html2text.HTML2Text()
# handler.body_width = 0              #超过长度自动换行，0：不自动换行
# handler.skip_internal_links = False #html文档内部跳转是否忽略
# handler.mark_code=True

#html转markdown
from markdownify import markdownify as md
# 参考：https://github.com/matthewwithanm/python-markdownify
#处理
def code_language_callback(el):
    '''
    当 HTML 代码包含以某种方式提供代码语言（例如类）的 pre 标记时，此回调可用于从标记中提取语言并将其作为转换后的 pre
    el:<class 'bs4.element.Tag'>对象
    return：返回代码块的编程语言类型
    '''
    code_tag = el.find('code')
    if code_tag.has_attr('class'):
        code_language = code_tag['class'][0].split('-')[-1]
    else:
        code_language =''
    return code_language


class CoursePipeline:
    def __init__(self, file_dir):
        self.file_dir = file_dir 

    @classmethod
    def from_crawler(cls, crawler):
        return cls(file_dir=crawler.settings.get('FILES_STORE'))

    # 解析item里的内容
    def process_item(self, item, spider):
        #判断数据结构
        if isinstance(item, CourseItem):
            # 创建文件夹以存储课程相关文件
            folder_name = item['course_name'].replace(':','：').replace('|','丨').replace('?','？')
            folder_path = os.path.join(self.file_dir,folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # 创建简介.md文件并写入课程简介
            catalog =f"\n<h3>课程目录</h3>\n![目录]({item['course_catalog_pic_url']})"
            course_description_text = '\n<h3>课程介绍</h3>\n'+item['course_description'] + catalog
            # course_description_text = handler.handle(course_description_text)
            course_description_text = md(course_description_text,code_language_callback=code_language_callback)

            intro_file_name = os.path.join(folder_path, '课程介绍.md')
            with open(intro_file_name, 'w+', encoding='utf-8') as intro_file:
                intro_file.write(course_description_text)
            
            # return item #错误
        return item

class ArticlePipeline:
    def __init__(self, file_dir):
        self.file_dir = file_dir 

    @classmethod
    def from_crawler(cls, crawler):
        return cls(file_dir=crawler.settings.get('FILES_STORE'))

    # 解析item里的内容
    def process_item(self, item, spider):
        #判断数据结构
        if isinstance(item, ArticleItem):
            # 保存文章
            course_name = item['course_name'].replace(':','：').replace('|','丨').replace('?','？')
            article_title= item['article_title'].replace(':','：').replace('|','丨').replace('?','？')
            # article_content = handler.handle(item['article_content'])
            article_content = md(item['article_content'],code_language_callback=code_language_callback)
            #保存文本
            file_path = os.path.join(self.file_dir,course_name,f'{article_title}.md')
            with open(file_path, 'w+', encoding='utf-8') as intro_file:
                intro_file.write(article_content)

            #保存音频
            if item['article_audio_url']:
                audio_dir = os.path.join(self.file_dir,course_name,'音频')
                if not os.path.exists(audio_dir):
                    os.makedirs(audio_dir)
                extension = item['article_audio_url'].split('.')[-1]
                audio_file = os.path.join(audio_dir,f'{article_title}.{extension}')
                #下载
                response = requests.get(item['article_audio_url'])
                if response.status_code == 200:
                    with open(audio_file, 'wb') as audio_file_obj:
                        audio_file_obj.write(response.content)
                else:
                    self.logger.error(f"Failed to download audio from {audio_url}")
                    
                # return item #错误
        return item


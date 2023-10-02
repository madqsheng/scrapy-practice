from bs4 import BeautifulSoup
import markdown

# 你的HTML文本
html_text = """
<p>近期 ChatGPT 非常火爆，点燃了大家对人工智能的热情，Python作为人工智能的主开发语言，备受各行业热捧。</p>
<p>Python的功能非常强大，除了应用在AI技术领域，在数据采集、数据分析、大数据应用、自动化测试、自动化办公、Web项目开发、大数
据等领域都能发挥巨大的作用，因此市场对Python相关的人才需求非常大。</p>
<p>然而，单纯学习语言无法快速提高技术实力。在项目开发工程师的求职面试过程中，企业尤其会关注面试者的项目经验和技术开发能力 
。针对这两方面痛点，本课程给出了体系化解决方案，手把手带你开发一个类似B站的在线视频直播平台，带你高效掌握前后端主流技术， 
迅速提升核心竞争力。</p>
<p><img src="https://static001.geekbang.org/resource/image/bd/c6/bdcf94b3799f88322c76f65b535c08c6.jpg" alt="" /></p>      
<p>本课程主要有三大亮点。</p>
<p>1.<strong>项目新颖，实战有代表性。</strong>精选在线视频平台作为实践项目，平台中还包含直播功能开发，紧随行业热点需求，手
把手带你综合应用前后端开发技术，快速提升核心竞争力，让面试官眼前一亮。更新完结后，还能一键解锁项目配套源码。代码链接：<a href="https://gitee.com/Barry_Python_web/python_web_code/tree/master">https://gitee.com/Barry_Python_web/python_web_code/tree/master</a></p>
<p>2.<strong>从 0 到 1 的体系化学习。</strong>从 0 搭建，轻松上手，覆盖语言基础学习、进阶应用、框架搭建及全模块功能开发。 
从项目需要分析到研发落地，帮你全面强化技术体系，扎实技术研发能力。</p>
<p>3.<strong>面试导向。</strong>技术研发总监的独家面试与项目经验指导，精准锁定面试热门核心技术点，带你锻炼硬技能和软技能，
轻松应对面试挑战，向企业展示自己更优秀的一面。</p>
<p><img src="https://static001.geekbang.org/resource/image/e1/76/e1f6d018f9e42bcf07107f545e7e0a76.jpg" alt="" /></p>      
<h2>技术框架版本</h2>
<p>Vue 2.7（大部分企业应用中的稳定版本）、Python 3.8、Flask 1.1.2、Node 10.13、NPM 6.4.1、Element 2.8.2、Echarts 4.9.0</p><h2>课程设计</h2>
<p>课程分为五个核心模块，将技术与业务功能需求充分结合，让开发者实现对技术的充分掌握。</p>
<p><strong>赛前热身</strong><br />
巩固 Python 和 Vue 的基础知识，构建基础技能体系，为后续的实战开发做热身准备，跟随老师体系化完成项目需求分析，强化你的项目 
搭建能力。</p>
<p><strong>前端实战篇</strong><br />
从项目需求到研发落地全流程体验，培养你熟练应用前端框架、快速实现前端功能模块以及灵活应用第三方组件库的能力。让你高效提升开
发效率和技术能力，独立完成前端项目的设计与开发。</p>
<p><strong>后端实战篇</strong><br />
覆盖后端主流框架应用能力，从代码设计到具体功能的模块接口开发，带你深度体验独立平台搭建和后端开发的完整链路。核心知识点包括
 Flask 项目搭建、正则匹配路由、异常捕获、Flask-RESTful 开发实践、Flask 认证机制，还有数据库的应用。</p>
<p><strong>直播模块篇</strong><br />
紧随行业热点需求，带你拓展技术领域，实现直播应用。该应用涵盖平台直播系统后台搭建、HLS 协议直播、推拉流、串流码与控制器以及
直播功能的完整实现。</p>
<p><strong>总结篇</strong><br />
整个项目开发完成的整体总结回顾，帮你沉淀经验。同时老师还会提供全栈工程师职业发展的路线和进阶建议，强化你的职业发展路径。</p>
"""

# 使用BeautifulSoup解析HTML文本
soup = BeautifulSoup(html_text, 'html.parser')

# 获取解析后的文本
text_content = soup.get_text()
parsed_html = soup.prettify()

url='https://static001.geekbang.org/resource/image/53/58/53efdf90471aeb0a6d32704b4c541158.jpg'
pic=f'\n\n![目录]({url})'

parsed_html=parsed_html+pic
text_content=text_content+pic

# 使用Markdown库将文本转换为Markdown格式
markdown_text = markdown.markdown(text_content)
with open('text.md', 'w', encoding='utf-8') as file:
    file.write(markdown_text)

print("Markdown文件已保存为 'output.md'")

markdown_text = markdown.markdown(parsed_html)
with open('parsed.md', 'w', encoding='utf-8') as file:
    file.write(markdown_text)

with open('parsed_origin.md', 'w', encoding='utf-8') as file:
    file.write(parsed_html)

with open('text_origin.md', 'w', encoding='utf-8') as file:
    file.write(text_content)


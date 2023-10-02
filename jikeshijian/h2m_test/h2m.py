import html2text
import markdown
#参考：https://github.com/aaronsw/html2text，注意html2text.html2text()和html2text.HTML2Text()有区别

# 你的HTML文本
html_text = """
<p><strong>「极客时间 AIGC 未来教育系列课程」</strong></p>\n<p>2022 年 12 月 ChatGPT 发布，随后迅速火爆全球，相信你已经 get 到它与过往 AI 聊天机器人的不同之处，只要你善于提问，写代码、写邮件、写论文、创作视频脚本、绘画、翻译等几十项任务均不在话下。</p>\n<p>OpenAI 的创始人 Sam Altman 说，“通用人工智能（AGI）已经离我们不远了”。徐文浩老师在使用 ChatGPT 完成各种各样的任务，并尝试过 OpenAI 提供的各种 API 之后，也在感叹，“强人工智能已经来了”。</p>\n<p>这一次人工智能领域的进展，完全不同于 80 年代的学习理论，也远远超越了 2012 年的深度神经网络的意义，它会变成一场席卷全世界的风暴。AI 应用也不再是算法工程师和机器学习研究人员的专利，而是变成了每个工程师都可以快速学习并参与开发的领域。</p>\n<p>这门课程就是要把新一代 AI 应用开发的方法和机会分享给你。无论你是产品经理还是工程师，乃至于 IT 行业之外的业务人员，都值得学一学看一看。通过实践，高效利用新一代 AI 强大的能力，去解决真实场景下的问题。</p>\n<h3>课程设计</h3>\n<p>课程共分为 3 个模块。</p>\n<ul>\n<li><strong>基础知识篇。</strong>带你探究大型语言模型的基本能力。通过提示语（Prompt）和嵌入式表示（Embedding）这两个核心功能，看看大模型能帮我们解决哪些常见的任务。通过这一部分，你会熟悉 OpenAI 的 API，以及常见的分类、聚类、文本摘要、聊天机器人等功能，能够怎么实现。</li>\n<li><strong>实战提高篇。</strong>开始进入真实的应用场景。要让 AI 有用，不是它能简单和我们闲聊几句就可以的。我们希望能够把自己系统里面的信息，和 AI 系统结合到一起去，以解决和优化实际的业务问题。比如优化传统的搜索、推荐；或者进一步让 AI 辅助我们读书读文章；乃至于让 AI 自动根据我们的代码撰写单元测试；最后，我们还能够让 AI 去决策应用调用什么样的外部系统，来帮助客户解决问题。</li>\n<li><strong>语音与视觉篇。</strong>光有文本对话的能力是不够的，这部分会进一步让你体验语音识别、语音合成，以及唇形能够配合语音内容的数字人。还会教会你如何利用现在最流行的 Stable Diffusion 这样的开源模型，去生成你所需要的图片。并在最后，把聊天和画图结合到一起去，为你提供一个“美工助理”。</li>\n</ul>\n
"""

text = html2text.html2text(html_text)
# config = html2text.HTML2Text()
# config.parser_class = 'lxml'  # 指定使用HTML解析器
# text = config.handle(html_text)
print(text)

# url='https://static001.geekbang.org/resource/image/53/58/53efdf90471aeb0a6d32704b4c541158.jpg'
# pic=f'\n\n![目录]({url})'

# text=text+pic

# # 使用Markdown库将文本转换为Markdown格式
# markdown_text = markdown.markdown(text)
# # 保存Markdown文本到文件
# with open('h2m.md', 'w', encoding='utf-8') as file:
#     file.write(markdown_text)

# with open('h2m_origin.md', 'w', encoding='utf-8') as file:
#     file.write(text)
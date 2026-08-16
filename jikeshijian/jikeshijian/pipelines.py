# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import os
import re
import logging
import html
from datetime import datetime

import requests
import scrapy

from jikeshijian.items import ArticleItem, CourseItem

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTML 渲染：把极客时间返回的富文本 HTML 直接包进一个排版干净的阅读页。
# 用 __XXX__ 占位符 + replace()，避免 CSS 里的 { } 与 str.format() 冲突。
#
# 阅读体验增强（通过 CDN 引入，需联网，与图片外链同一前提）：
#   - MathJax 渲染 $...$ / $$...$$ 公式
#   - highlight.js 代码高亮 + 行号 + 一键复制
#   - 图片点击放大灯箱（lightbox）+ 图注
# ---------------------------------------------------------------------------
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github.min.css" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css" media="(prefers-color-scheme: dark)">
<style>
  :root{
    --bg:#ffffff; --text:#1f2328; --muted:#57606a; --code-bg:#f6f8fa;
    --border:#d0d7de; --accent:#0969da;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0d1117; --text:#e6edf3; --muted:#8b949e; --code-bg:#161b22;
      --border:#30363d; --accent:#58a6ff;
    }
  }
  *{box-sizing:border-box;}
  body{
    margin:0; background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
      "Hiragino Sans GB","Microsoft YaHei",sans-serif;
    font-size:17px; line-height:1.85;
  }
  .article{max-width:820px; margin:0 auto; padding:48px 24px 96px;}
  .article-header{border-bottom:1px solid var(--border); margin-bottom:28px; padding-bottom:20px;}
  .course{color:var(--muted); font-size:14px; letter-spacing:.04em;}
  h1.title{font-size:27px; line-height:1.4; margin:.5em 0 0;}
  .content h2{font-size:21px; margin:1.8em 0 .8em; padding-left:12px; border-left:4px solid var(--accent);}
  .content h3{font-size:18px; margin:1.6em 0 .7em;}
  .content p{margin:1em 0;}
  .content img{max-width:100%; height:auto; display:block; margin:24px auto;
    border:1px solid var(--border); border-radius:6px; cursor:zoom-in;}
  .content pre{background:var(--code-bg); border:1px solid var(--border);
    border-radius:8px; padding:16px; overflow-x:auto; font-size:14px; line-height:1.6;}
  .content code{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;}
  .content pre code{background:none; border:none; padding:0;}
  .content :not(pre) > code{background:var(--code-bg); border:1px solid var(--border);
    border-radius:4px; padding:.15em .4em; font-size:.9em;}
  .content blockquote{margin:1.2em 0; padding:.2em 1em; color:var(--muted);
    border-left:4px solid var(--border);}
  .content a{color:var(--accent); text-decoration:none;}
  .content a:hover{text-decoration:underline;}
  .content table{border-collapse:collapse; width:100%; margin:1.2em 0;}
  .content th,.content td{border:1px solid var(--border); padding:8px 12px;}
  .content ul,.content ol{padding-left:1.6em;}
  /* 音频条（放在顶部） */
  .audio{margin:0 0 28px; padding:14px 0; border-bottom:1px solid var(--border);}
  .audio h3{font-size:14px; color:var(--muted); margin:0 0 10px; font-weight:600;}
  .audio audio{width:100%;}
  /* 代码块增强：容器 + 头部栏（语言 + 复制） */
  .codebox{border:1px solid var(--border); border-radius:8px; overflow:hidden; margin:1.5em 0; background:var(--code-bg);}
  .codebar{display:flex; justify-content:space-between; align-items:center; padding:6px 12px;
    background:var(--code-bg); border-bottom:1px solid var(--border); font-size:12px; color:var(--muted);}
  .codelang{text-transform:uppercase; letter-spacing:.05em;}
  .copybtn{font-size:12px; padding:3px 12px; border:1px solid var(--border); border-radius:4px;
    background:var(--bg); color:var(--text); cursor:pointer;}
  .copybtn:hover{border-color:var(--accent); color:var(--accent);}
  .codebox pre{border:none; border-radius:0; margin:0; background:transparent; padding:12px 14px; line-height:1.55;}
  .codebox pre code{display:block;}
  .ln{display:block;}
  .ln-n{display:inline-block; width:2.8em; text-align:right; margin-right:1em;
    color:var(--text); font-size:.82em; font-weight:700; opacity:.55; user-select:none;}
  /* 图片图注 + 灯箱 */
  .content figure.fig{margin:1.6em 0; text-align:center;}
  .content figure.fig img{margin:0 auto;}
  .content figcaption{margin-top:8px; font-size:13px; color:var(--muted); line-height:1.5;}
  .lightbox{position:fixed; inset:0; background:rgba(0,0,0,.45); display:flex;
    align-items:center; justify-content:center; z-index:9999; cursor:zoom-out;
    -webkit-backdrop-filter:blur(3px); backdrop-filter:blur(3px);}
  .lightbox img{max-width:92vw; max-height:92vh; border-radius:6px; box-shadow:0 8px 40px rgba(0,0,0,.5); background:var(--bg); padding:4px;}
  .lightbox .lb-close{position:absolute; top:18px; right:26px; color:#fff; font-size:34px; line-height:1;}
  /* 评论区 */
  .comments-section{margin-top:56px; padding-top:28px; border-top:1px solid var(--border);}
  .comments-header{display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;}
  .comments-title{font-size:18px; font-weight:600; color:var(--text);}
  .comments-tabs{display:flex; gap:8px;}
  .comments-tabs .tab{font-size:13px; padding:4px 12px; border-radius:14px;
    background:var(--code-bg); color:var(--muted); border:1px solid var(--border); cursor:pointer;}
  .comments-tabs .tab.active{background:var(--accent); color:#fff; border-color:var(--accent);}
  .comment-list{}
  .comment-item{display:flex; gap:14px; padding:18px 0; border-bottom:1px solid var(--border);}
  .comment-item:first-child{padding-top:0;}
  .comment-avatar{width:40px; height:40px; border-radius:50%; object-fit:cover; flex-shrink:0;
    border:1px solid var(--border); background:var(--code-bg);}
  .comment-body{flex:1; min-width:0;}
  .comment-author{font-size:15px; font-weight:600; color:var(--text); margin-bottom:6px;}
  .comment-text{font-size:15px; line-height:1.75; color:var(--text); word-break:break-word;}
  .comment-text br{line-height:1.6;}
  .comment-reply{margin-top:12px; padding:12px 14px; border-radius:8px; background:var(--code-bg);
    border:1px solid var(--border); font-size:14px; line-height:1.7; color:var(--text);}
  .comment-reply-label{color:var(--accent); font-weight:600; margin-right:4px;}
  .comment-meta{display:flex; align-items:center; gap:16px; margin-top:12px; font-size:13px; color:var(--muted);}
  .comment-meta .sep{color:var(--border);}
  .comment-actions{display:flex; align-items:center; gap:16px; margin-left:auto;}
  .comment-action{display:inline-flex; align-items:center; gap:4px; cursor:pointer;}
  .comment-action svg{width:16px; height:16px; fill:currentColor; opacity:.7;}
  .comment-empty{padding:24px 0; color:var(--muted); font-size:14px; text-align:center;}
</style>
<script>
window.MathJax = {
  tex: { inlineMath: [['$','$'],['\\(','\\)']], displayMath: [['$$','$$'],['\\[','\\]']] },
  svg: { fontCache: 'global' }
};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head>
<body>
<article class="article">
  <header class="article-header">
    <div class="course">__COURSE__</div>
    <h1 class="title">__TITLE__</h1>
  </header>
__AUDIO__
  <div class="content">
__BODY__
  </div>
__COMMENTS__
</article>
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
<script>
(function(){
  function enhanceCode(pre){
    var code = pre.querySelector('code');
    if(!code) return;
    if(window.hljs){ try{ window.hljs.highlightElement(code); }catch(e){} }
    var html = code.innerHTML;
    var lines = html.split(String.fromCharCode(10));
    if(lines.length && lines[lines.length-1].trim()==='') lines.pop();
    code.innerHTML = lines.map(function(l,i){
      return '<span class="ln"><span class="ln-n">'+(i+1)+'</span><span class="ln-c">'+(l===''?'&nbsp;':l)+'</span></span>';
    }).join('');
    var box = document.createElement('div'); box.className='codebox';
    pre.parentNode.insertBefore(box, pre); box.appendChild(pre);
    var bar=document.createElement('div'); bar.className='codebar';
    var m=(code.className||'').match(/language-([\\w+#-]+)/);
    var lang=m?m[1]:'text';
    var ls=document.createElement('span'); ls.className='codelang'; ls.textContent=lang;
    var btn=document.createElement('button'); btn.className='copybtn'; btn.type='button'; btn.textContent='复制';
    btn.addEventListener('click', function(){
      navigator.clipboard.writeText(code.textContent).then(function(){
        btn.textContent='已复制'; setTimeout(function(){btn.textContent='复制';},1500);
      }, function(){ btn.textContent='复制失败'; setTimeout(function(){btn.textContent='复制';},1500); });
    });
    bar.appendChild(ls); bar.appendChild(btn); box.insertBefore(bar, pre);
  }
  function openLightbox(src, alt){
    var ov=document.createElement('div'); ov.className='lightbox';
    var im=document.createElement('img'); im.src=src; im.alt=alt;
    var c=document.createElement('div'); c.className='lb-close'; c.textContent='×';
    ov.appendChild(im); ov.appendChild(c);
    ov.addEventListener('click', function(){ if(ov.parentNode) ov.parentNode.removeChild(ov); });
    document.body.appendChild(ov);
  }
  function enhanceImg(img){
    var fig=document.createElement('figure'); fig.className='fig';
    img.parentNode.insertBefore(fig, img); fig.appendChild(img);
    var cap=img.getAttribute('title')||img.getAttribute('alt')||'';
    if(cap){
      var fc=document.createElement('figcaption');
      // 极客图注里用 <br> 分隔多行，这里转成真实换行显示
      fc.textContent = cap.replace(/<br\\s*\\/?>/gi, '\n');
      fc.style.whiteSpace = 'pre-line';
      fig.appendChild(fc);
    }
    img.addEventListener('click', function(){ openLightbox(img.getAttribute('src'), img.getAttribute('alt')||''); });
  }
  var pres=document.querySelectorAll('.content pre');
  for(var i=0;i<pres.length;i++) enhanceCode(pres[i]);
  var imgs=document.querySelectorAll('.content img');
  for(var j=0;j<imgs.length;j++) enhanceImg(imgs[j]);
  // 评论区「最新 / 精选」切换
  var cmtTabs = document.querySelectorAll('.comments-tabs .tab');
  for(var t=0; t<cmtTabs.length; t++){
    cmtTabs[t].addEventListener('click', function(){
      for(var k=0; k<cmtTabs.length; k++) cmtTabs[k].classList.remove('active');
      this.classList.add('active');
      var which = this.getAttribute('data-tab');
      var latest = document.getElementById('cmt-latest');
      var essence = document.getElementById('cmt-essence');
      if(latest) latest.style.display = (which==='latest') ? '' : 'none';
      if(essence) essence.style.display = (which==='essence') ? '' : 'none';
    });
  }
})();
</script>
</body>
</html>
"""


def _safe_filename(name):
    """文件名里不能出现 Windows 非法字符，做最小替换；同时避免和原标题符号撞车。"""
    return name.replace(':', '：').replace('|', '丨').replace('?', '？')


_ICON_COMMENT = '<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
_ICON_LIKE = '<svg viewBox="0 0 24 24"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>'


def _ts_to_date(ts):
    """把秒级时间戳转成 YYYY-MM-DD。"""
    if not ts:
        return ''
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except (TypeError, ValueError, OSError):
        return ''


# 裸链接匹配：不含空白、< > 以及中文字符（URL 里的中文是 %XX 编码，不会是裸中文）
_URL_RE = re.compile(r'https?://[^\s<>\u4e00-\u9fff]+')


def _linkify(match):
    """把匹配到的裸 URL 包成可点击的 <a>，并剥离结尾常见中英文标点。"""
    url = match.group(0)
    trail = ''
    while url and url[-1] in '.,;:!?。，；：！？、）、】)':
        trail = url[-1] + trail
        url = url[:-1]
    return '<a href="{}" target="_blank" rel="noopener">{}</a>{}'.format(url, url, trail)


def _comment_text_to_html(text):
    """评论内容转 HTML。

    极客返回的评论内容里，/ ' " 等字符已被 HTML 实体化（如 &#47; &#39;），
    若直接 html.escape() 会二次转义成 &amp;#47; 导致链接乱码。
    因此先 unescape 还原真实字符，再 escape 防 XSS，最后换行转 <br>，
    并顺手把裸链接转成可点击 <a>（贴近原网页评论区体验）。
    """
    if text is None:
        return ''
    text = html.unescape(str(text))   # &#47; -> / ， &#39; -> ' ， &quot; -> "
    text = html.escape(text)          # 重新转义防注入（/ 不需要转义，保持不变）
    text = _URL_RE.sub(_linkify, text)
    # 极客接口里换行就是字面 \n（JSON 字符串），直接用换行符切分
    return '<br>'.join(text.splitlines())


def _render_comments(comments_data, comments_essence=None):
    """把 /serv/v4/comment/list 的 data 渲染成评论区 HTML（含「最新/精选」切换）。"""

    def _list_html(data, empty_hint):
        if not data:
            return '<div class="comment-empty">{}</div>'.format(empty_hint)
        comment_list = data if isinstance(data, list) else data.get('list', [])
        if not comment_list:
            return '<div class="comment-empty">{}</div>'.format(empty_hint)

        items = []
        for c in comment_list:
            author = html.escape(c.get('user_name', '') or '')
            avatar = html.escape(c.get('user_header', '') or '')
            content = _comment_text_to_html(c.get('comment_content', ''))
            date_str = _ts_to_date(c.get('comment_ctime'))
            ip = html.escape(c.get('ip_address', '') or '')
            likes = c.get('like_count', 0) or 0
            discussions = c.get('discussion_count', 0) or 0

            # 作者回复（replies 里可能有多条，全部显示）
            replies = c.get('replies') or []
            reply_html = ''
            for reply in replies:
                reply_user = html.escape(reply.get('user_name', '作者回复'))
                reply_content = _comment_text_to_html(reply.get('content', ''))
                reply_html += (
                    '<div class="comment-reply">'
                    '<span class="comment-reply-label">{}:</span>'
                    '{}'
                    '</div>'
                ).format(reply_user, reply_content)

            item_html = (
                '<div class="comment-item">'
                '  <img class="comment-avatar" src="{}" alt="{}" loading="lazy">'
                '  <div class="comment-body">'
                '    <div class="comment-author">{}</div>'
                '    <div class="comment-text">{}</div>'
                '    {}'
                '    <div class="comment-meta">'
                '      <span>{}</span>'
                '      {}'
                '      <span class="comment-actions">'
                '        <span class="comment-action">{}{}</span>'
                '        <span class="comment-action">{}{}</span>'
                '      </span>'
                '    </div>'
                '  </div>'
                '</div>'
            ).format(
                avatar, author, author, content, reply_html, date_str,
                '<span class="sep">|</span><span>归属地：{}</span>'.format(ip) if ip else '',
                _ICON_COMMENT, discussions, _ICON_LIKE, likes
            )
            items.append(item_html)
        return '\n'.join(items)

    latest_html = _list_html(comments_data, '暂无评论')
    essence_html = _list_html(comments_essence, '暂无精选评论')

    # 总数用「最新」列表的 count（找不到就用列表长度兜底）
    page = comments_data.get('page', {}) if isinstance(comments_data, dict) else {}
    total = page.get('count', 0)
    if not total:
        latest_list = (comments_data if isinstance(comments_data, list)
                       else (comments_data or {}).get('list', []))
        total = len(latest_list)

    return (
        '<section class="comments-section">'
        '  <div class="comments-header">'
        '    <div class="comments-title">全部留言({})</div>'
        '    <div class="comments-tabs">'
        '      <span class="tab active" data-tab="latest">最新</span>'
        '      <span class="tab" data-tab="essence">精选</span>'
        '    </div>'
        '  </div>'
        '  <div class="comment-list" id="cmt-latest">'
        + latest_html +
        '  </div>'
        '  <div class="comment-list" id="cmt-essence" style="display:none;">'
        + essence_html +
        '  </div>'
        '</section>'
    ).format(total)


def _render_html(course_name, title, body_html, audio_rel_path=None, comments_html=''):
    audio_block = ""
    if audio_rel_path:
        audio_block = (
            '<div class="audio">\n'
            '  <h3>音频</h3>\n'
            f'  <audio controls preload="none" src="{audio_rel_path}"></audio>\n'
            '</div>'
        )
    return (_HTML_TEMPLATE
            .replace("__COURSE__", course_name or "")
            .replace("__TITLE__", title or "")
            .replace("__BODY__", body_html or "")
            .replace("__AUDIO__", audio_block)
            .replace("__COMMENTS__", comments_html))


class CoursePipeline:
    def __init__(self, file_dir):
        self.file_dir = file_dir

    @classmethod
    def from_crawler(cls, crawler):
        return cls(file_dir=crawler.settings.get('FILES_STORE'))

    # 解析item里的内容
    def process_item(self, item):
        # 判断数据结构
        if isinstance(item, CourseItem):
            # 创建文件夹以存储课程相关文件
            folder_name = _safe_filename(item['course_name'])
            folder_path = os.path.join(self.file_dir, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # 课程简介 + 课程目录图，本身就是 HTML，直接拼接后包成阅读页
            body = (
                '<h3>课程介绍</h3>'
                + item['course_description']
                + '<h3>课程目录</h3>'
                + f'<img src="{item["course_catalog_pic_url"]}" alt="课程目录">'
            )
            html = _render_html(item['course_name'], item['course_name'], body)
            file_path = os.path.join(folder_path, '课程介绍.html')
            with open(file_path, 'w+', encoding='utf-8') as f:
                f.write(html)
        return item


class ArticlePipeline:
    def __init__(self, file_dir):
        self.file_dir = file_dir

    @classmethod
    def from_crawler(cls, crawler):
        return cls(file_dir=crawler.settings.get('FILES_STORE'))

    # 解析item里的内容
    def process_item(self, item):
        # 判断数据结构
        if isinstance(item, ArticleItem):
            course_name = _safe_filename(item['course_name'])
            article_title = _safe_filename(item['article_title'])

            # 先下载音频；成功后拿到相对路径，稍后一起写进网页做成可播放音频条
            audio_rel = None
            if item['article_audio_url']:
                audio_dir = os.path.join(self.file_dir, course_name, '音频')
                if not os.path.exists(audio_dir):
                    os.makedirs(audio_dir)
                extension = item['article_audio_url'].split('.')[-1]
                audio_file = os.path.join(audio_dir, f'{article_title}.{extension}')
                try:
                    response = requests.get(item['article_audio_url'], timeout=30)
                    if response.status_code == 200:
                        with open(audio_file, 'wb') as af:
                            af.write(response.content)
                        audio_rel = f'音频/{article_title}.{extension}'
                    else:
                        logger.error(
                            "Failed to download audio from %s (status %s)",
                            item['article_audio_url'], response.status_code)
                except Exception as exc:  # noqa: BLE001 - 下载失败不应中断整条爬虫
                    logger.error("Failed to download audio from %s: %s",
                                 item['article_audio_url'], exc)

            # 文章正文本身就是富文本 HTML，直接包成阅读页（保留原网页的图片/代码排版）
            comments_html = _render_comments(item.get('comments'), item.get('comments_essence'))
            file_path = os.path.join(self.file_dir, course_name, f'{article_title}.html')
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            html = _render_html(item['course_name'], item['article_title'],
                                item['article_content'], audio_rel_path=audio_rel,
                                comments_html=comments_html)
            with open(file_path, 'w+', encoding='utf-8') as f:
                f.write(html)
        return item

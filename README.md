# scrapy-practice

> Scrapy 爬虫练习仓库。当年练手用的 5 个独立爬虫，分别针对不同网站练习不同的技术点：
> 静态接口爬取、登录态层层钻取、Selenium 绕过 JS 反爬、图片/文件批量下载、多存储后端（Mongo / MySQL / CSV / 本地文件）。
>
> 各模块彼此互不相干，可以单独阅读、单独运行、单独学习。

---

## 这是什么

一个用来**练习 Scrapy 框架**的仓库，不是某个单一产品。里面是 4 个标准 Scrapy 工程 + 1 个独立 Selenium 脚本，每个瞄准一个真实网站，练一种典型爬虫套路。

一句话定位：**「同一个 Scrapy 骨架的 4 套房子 + 1 间平房（d2l 脚本）」，每套房子针对不同网站装修（spider 抓取逻辑 + settings 配置）。**

---

## 目录结构

```
scrapy-practice/
├── d2l_download.py              # 独立脚本：下载《动手学深度学习》课程 PDF（不用 Scrapy）
├── images360/                   # Scrapy 工程：爬 360 图片搜索
│   ├── scrapy.cfg
│   └── images360/
│       ├── spiders/images.py    #   spider：images
│       ├── items.py / pipelines.py / settings.py / middlewares.py
├── jikeshijian/                 # Scrapy 工程：备份极客时间课程文章
│   ├── jikeshijian/
│   │   ├── spiders/jk_article.py #   spider：jk
│   │   ├── ...
│   └── h2m_test/                #   配套：把爬到的 HTML 正文转 Markdown 的小脚本
├── scrapyseleniumtest/          # Scrapy 工程：爬淘宝搜索结果（用 Selenium 绕反爬）
│   └── scrapyseleniumtest/
│       ├── spiders/taobao.py    #   spider：taobao
│       └── middlewares.py       #   Selenium 下载中间件
├── zhanku/                      # Scrapy 工程：批量采集站酷设计/插画作品
│   ├── zhanku/
│   │   ├── spiders/zhanku.py    #   spider：zhanku
│   │   └── 用法.txt             #   运行示例
│   └── 用法.txt
├── resource/                   # 爬取结果统一落盘目录（运行时自动创建，已被 .gitignore 忽略）
│   ├── jikeshijian/            #   极客时间备份
│   ├── image360/               #   360 图片
│   ├── zhanku/                 #   站酷图片 + CSV
│   └── d2l/                    #   动手学深度学习 PDF
└── README.md
```

---

## 各模块说明

| 模块 | 类型 | 目标网站 | 练习的技术点 | 数据落点 |
|------|------|----------|--------------|----------|
| `d2l_download.py` | 独立脚本（非 Scrapy） | courses.d2l.ai 课程页 | Selenium 无头浏览器 + requests 下载 | `resource/d2l` 本地文件夹 |
| `images360` | Scrapy 工程 | image.so.com（360 图片） | 列表 JSON 接口翻页爬取 | 本地图片(`resource/image360`) + MongoDB + MySQL（三选/全开） |
| `jikeshijian` | Scrapy 工程 | time.geekbang.org（极客时间） | 登录 Cookie + 三层 API 钻取（课程→文章列表→正文） | `resource/jikeshijian` 本地文件夹（正文为富文本 HTML，直接生成带排版的 HTML 阅读页 + 可选音频） |
| `scrapyseleniumtest` | Scrapy 工程 | s.taobao.com（淘宝） | Selenium 下载中间件绕过 JS 渲染反爬 | MongoDB（仅解析，未落地文件） |
| `zhanku` | Scrapy 工程 | zcool.com.cn（站酷） | 列表 JSON + 年份过滤 + 图片批量下载 | `resource/zhanku` 本地图片（按年/分类/阅读量分目录）+ CSV |

---

## 环境依赖

- **Python 3.6+/3.11**（历史 .pyc 显示在两版本都跑过）
- **Scrapy**
- **Selenium** + 对应浏览器驱动
  - `d2l_download.py` 用 **Firefox + geckodriver**
  - `scrapyseleniumtest` 用 **Chrome + chromedriver**
- 可选的存储后端（部分模块才用）
  - **MongoDB**（images360 / scrapyseleniumtest / zhanku）
  - **MySQL**（images360 / zhanku）

> 安装示例：`pip install scrapy selenium pymongo pymysql`

---

## 怎么运行

每个 Scrapy 工程都要先 `cd` 进工程目录，再用 `scrapy crawl <spider名>` 跑。

### 1. d2l_download.py（独立脚本）
```bash
python d2l_download.py
```
- 需 Firefox + geckodriver 可用。
- 下载目录由脚本里的 `root_dir` 自动推算到项目根目录 `resource/d2l`（运行时自动创建），不再写死绝对路径。

### 2. images360 —— 爬 360 图片
```bash
cd images360
scrapy crawl images
```
- `settings.py` 里 `ITEM_PIPELINES` **同时开了** 本地图片、MongoDB、MySQL 三个管道。
- 如果本机没起 MongoDB / MySQL，会因连不上而报错——按需把用不到的管道注释掉，或先启动对应数据库。
- 图片默认保存到项目根目录 `resource/image360`（运行时自动创建，不再相对运行目录）。

### 3. jikeshijian —— 备份极客时间
```bash
cd jikeshijian
scrapy crawl jk                  # 爬「我的课程」里的全部课程
scrapy crawl jk -a limit=10      # 只爬列表里的前 10 门（实际不足 10 门也不报错）
```
- 需要登录态：把 `settings.py` 里的 `MY_COOKIE` 换成你自己的（**代码里的是 2023 年的，已过期**）。
- 文件统一保存到项目根目录 `resource/jikeshijian`（相对路径，已不再写死绝对路径 `E:\极客时间`）。

### 4. scrapyseleniumtest —— 爬淘宝
```bash
cd scrapyseleniumtest
scrapy crawl taobao
```
- 靠 `middlewares.py` 里的 **Selenium 中间件**用真实 Chrome 加载页面、翻页，再交给 spider 用 XPath 解析。
- 需要本机装好 Chrome + chromedriver，并确认 `settings.py` 的 `SELENIUM_TIMEOUT`。
- `MY_COOKIE_DICT` 里的淘宝 Cookie **已过期**，需重新抓包替换；搜索关键词 `KEYWORDS`、页数 `MAX_PAGE` 也在 settings 里改。

### 5. zhanku —— 爬站酷（按年份）
```bash
cd zhanku
scrapy crawl zhanku            # 默认爬 2016 年
scrapy crawl zhanku -a year=2014   # 也可指定年份
```
- 图片默认保存到项目根目录 `resource/zhanku`（运行时自动创建，已不再写死旧电脑绝对路径），CSV 也落在同一目录。
- 抓取的分类 `SUB_CATE_LIST`、推荐等级、排序、页数都在 `settings.py` 里调。

---

## 已知问题 / 上手前必看（重要）

这个仓库几年没维护，直接 `scrapy crawl` 大概率启动即崩或零产出。主要坑：

1. **Selenium 老 API**：`find_elements_by_xpath`、中间件里的 `webdriver.Chrome(chrome_options=...)` 都是 Selenium 3 的写法，Selenium 4 已删除 / 改名，需要在代码里改成新版（`find_elements(By.XPATH, ...)`、`options=...`）。
2. **硬编码路径（已修复）**：原本 `d2l`、`zhanku` 写死旧电脑绝对路径（`Desktop/动手学习深度学习`、`D:/卢艳/站酷爬虫图片`），现已统一改为项目内 `resource/` 相对目录（基于 `Path(__file__)` 自动推算根目录），换机器无需改路径。
3. **硬编码 Cookie**：极客时间、淘宝的登录 Cookie 是 2023 年抓的，早已失效，需要重新登录抓包替换。
4. **目标站点改版 / 升级反爬**：d2l 的旧版页面、极客时间 / 淘宝 / 站酷的接口和风控这几年都变过，原有的 XPath 和接口参数很可能已失效。
5. **过时数据库写法**：`pipelines.py` 里 MongoDB 用 `db.insert(...)`（已废弃，应 `insert_one(...)`）。
6. **极客时间正文接口有账号级限流**：`serv/v1/article`（文章正文）会按账号/IP 限额，触发时返回 `451` + 空 body + 响应头 `X-GEEK-WARN: rate limit`；而 `product` / `column/articles`（列表）接口不受影响。表现为「列表能拉、正文全挂」。这是服务端策略，**不是代码 / Cookie 问题**。缓解：`DOWNLOAD_DELAY` 调大 + 开启 `AUTOTHROTTLE`；触发后**先停手等冷却**（滚动窗口几十分钟~几小时，或当日额度次日重置），别连续轰，爬的时候也别在浏览器同时刷极客时间（共享额度）。

---

## 技术栈

- 爬虫框架：**Scrapy**
- 浏览器自动化：**Selenium**（Firefox / Chrome）
- 存储后端：**MongoDB** / **MySQL** / **CSV** / 本地文件系统
- HTTP 客户端：Scrapy 内置 + `requests`（d2l 脚本）

---

## 建议的复习顺序

如果想回忆 / 改造，建议从简单到复杂看：

1. `images360` —— 最标准的「列表 JSON 接口 + 多存储」模板，适合先看 Scrapy 骨架。
2. `d2l_download.py` —— 不用 Scrapy，纯 Selenium + requests，理解「什么时候其实不需要框架」。
3. `zhanku` —— 在 images360 基础上加了年份过滤和图片按维度分目录，逻辑最完整。
4. `jikeshijian` —— 登录态 + 三层 API 钻取，理解「带认证的爬虫」。
5. `scrapyseleniumtest` —— Selenium 中间件绕 JS 反爬，最硬核也最易过时。

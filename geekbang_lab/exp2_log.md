# 实验2 记录

## 目的
控制变量 `pvip`，验证 `pvip = 0 / 1 / 2` 各自返回的课程集合是否不同，确认是否需要对 `pvip` 取并集。

## 接口
主接口（唯一使用）：`https://time.geekbang.org/serv/v4/pvip/product_list`
不使用 `serv/v3/learn/product`（已弃用，不备份）。

## 唯一变量
`pvip`：0、1、2（即三个请求）

## 固定参数（其余不变）
- `product_type`: 0
- `with_articles`: false（响应体 articles 字段太长无用，去掉）
- `size`: 50
- `tag_ids`: []
- `product_form`: 0
- `sort`: 8
- `prev`: 0

## 三个请求定义
1. `pvip=0`, `product_type=0`, `with_articles=false`, `size=50`, `prev=0`
2. `pvip=1`, `product_type=0`, `with_articles=false`, `size=50`, `prev=0`
3. `pvip=2`, `product_type=0`, `with_articles=false`, `size=50`, `prev=0`

## 执行方式
- 前台执行（非后台），边执行边保存
- 每请求间隔 4 秒，控节奏防 cookie 限额
- 走代理 `127.0.0.1:7897`
- 使用新 cookie（`geekbang_lab/.cookie.txt`）
- 每个请求完成立即写入 `exp2_raw.json`，不写任何结论

## 产物
- `exp2_raw.json`：3 个请求的 URL + 负载 + 完整响应（`data.products`），原始数据，无结论
- 本文件：仅记录实验设计 / 过程

## 原始计数（非结论，集合是否相同请自行看 exp2_raw.json）
- pvip=0 → HTTP 200，返回 50 门
- pvip=1 → HTTP 200，返回 51 门
- pvip=2 → HTTP 200，返回 51 门

## 用户推断（基于实验2，待验证，非已证实结论）
- `pvip = 0 / 1 / 2` 都是需要的（三者返回集合不同，需全部取并集，不能只取其一）。
- 猜测：`pvip=0` 时集合最大（0 可能覆盖最广，是 1、2 的超集或包含最多）。
- 待验证：需用**完整集合**（翻页到底）对比 pvip=0/1/2 的 id 集合，确认三者关系与是否需全部并集。
  - 注：首页计数 `0=50`、`1=51`、`2=51` 表面与「0 最大」的猜测矛盾，可能源于仅取了 `prev=0` 一页（size=50）；必须用完整集合对比，不能直接拿首页计数下结论。

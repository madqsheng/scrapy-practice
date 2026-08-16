# 实验1 记录

## 目的
控制变量 `product_type`，验证 `product_type = 0 / 1 / 2` 各自返回的课程集合是否不同，为后续「必须遍历 product_type」做前提验证。

## 接口
主接口（唯一使用）：`https://time.geekbang.org/serv/v4/pvip/product_list`
不使用 `serv/v3/learn/product`（已弃用，不备份）。

## 唯一变量
`product_type`：0、1、2（即三个请求）

## 固定参数（其余不变）
- `pvip`: 0
- `with_articles`: false（响应体 articles 字段太长无用，去掉）
- `size`: 50
- `tag_ids`: []
- `product_form`: 0
- `sort`: 8
- `prev`: 0

## 三个请求定义
1. `product_type=0`, `pvip=0`, `with_articles=false`, `size=50`, `prev=0`
2. `product_type=1`, `pvip=0`, `with_articles=false`, `size=50`, `prev=0`
3. `product_type=2`, `pvip=0`, `with_articles=false`, `size=50`, `prev=0`

## 执行方式
- 前台执行（非后台），边执行边保存
- 每请求间隔 4 秒，控节奏防 cookie 限额
- 走代理 `127.0.0.1:7897`
- 使用新 cookie（`geekbang_lab/.cookie.txt`）
- 每个请求完成立即写入 `exp1_raw.json`，不写任何结论

## 产物
- `exp1_raw.json`：3 个请求的 URL + 负载 + 完整响应（`data.products`），原始数据，无结论
- 本文件：仅记录实验设计 / 过程

## 原始计数（非结论，集合是否相同请自行看 exp1_raw.json）
- product_type=0 → HTTP 200，返回 50 门
- product_type=1 → HTTP 200，返回 51 门
- product_type=2 → HTTP 200，返回 52 门

## 用户推断（基于实验1，待验证，非已证实结论）
- `product_type` 控制课程类型。
- `product_type=2` 基本不是我们需要的课程，可忽略不计。
- `product_type=0` 和 `product_type=1` 是我们需要的。
- 猜测：`product_type=1` 的课程一定出现在 `product_type=0` 里，但 `0` 里的课程不一定都在 `1` 里 → 非常大概率 `0` 包含 `1`（0 是 1 的超集）。
- 待验证：需用**完整集合**（翻页到底）对比 0 与 1 的 id 集合，确认包含关系。
  - 注：第一页计数 `0=50`、`1=51` 表面与「1 是 0 子集」的猜测矛盾，可能源于仅取了 `prev=0` 一页（size=50）或类型内分页；必须用完整集合对比，不能直接拿首页计数下结论。

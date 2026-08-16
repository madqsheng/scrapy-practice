# 获取 VIP 用户「全面且准确」的课程名↔id 映射表的方法

> 配套脚本：`geekbang_lab/product_list_lab.py`
> 接口：`POST https://time.geekbang.org/serv/v4/pvip/product_list`
> 状态：**方法已设计完成，最终"5 门目标课是否真的在结果里"待 exp6 实跑确认（当前账号 452 限流中）。**

---

## 一、为什么会"查不全"——根因

之前离线索引 `course_index.json` 用 `with_articles:false` 翻 `product_list`，导致 5 门新课（Claude Code Skill / RAG前沿 / AI Agent入门第一课 / Harness / Claude Code 企业级）被认为"不在 product_list 里"。

控制变量实验（exp2）要验证的核心假设是：**`with_articles` 不只是控制是否带文章列表，它很可能同时改变返回的课程集合**。浏览器真实请求用的是 `with_articles:true`，而我们之前用的是 `false`——这才是"查不到"的真凶，不是课程真的不在接口里。

> 这一点必须由 exp2 / exp6 的实跑结论坐实；本文件的方法是据此设计的"最稳妥取法"。

---

## 二、最终传参方法（推荐）

要拿到 VIP 用户下**最全面**的 `课程名 → id` 映射，按以下稳定参数调用：

```text
URL : https://time.geekbang.org/serv/v4/pvip/product_list
METHOD: POST
Body:
{
  "tag_ids": [],          // 不过滤标签（要全量）
  "product_type": <0..N>, // 类目，必须遍历所有值
  "product_form": 0,
  "pvip": <0 和 1 各来一遍>,  // 两者集合不同，取并集才是全集
  "prev": <偏移游标>,      // 第1页=0，之后 = 上一页 prev + 上一页实际返回条数
  "size": 20,             // 与浏览器一致；即使服务端忽略，也按"实际返回条数"推进 prev
  "sort": 8,
  "with_articles": true   // ★ 关键：用 true，不要 false
}
```

### 翻页规则（exp5 验证）
- 每页响应里 `data.page.more == true` 表示还有下一页。
- `prev` 不是"页码"，是**偏移量**：下一页 `prev = 本页 prev + 本页 products 实际长度`。
- 直到 `more == false` 停止。

### 全集 = 双重遍历取并集（exp3 / exp6 验证）
```
for pvip in [0, 1]:
    for product_type in [0, 1, 2, ..., 直到某类型返回空]:
        while page.more:
            拉一页 → 把 {id: title} 并入全局 map
            prev += 本页长度
全集 = 所有 (pvip, product_type) 下来的 {id: title} 并集
```
- `pvip=0` 与 `pvip=1` 返回的是**不同集合**（非包含），VIP 全集必须两者并集。
- `product_type` 实际有效范围需由 exp6 的 `per_type` 输出确认（预计 0..~7，可能到 12）。

---

## 三、落地为 course_index.json 的步骤

1. **等账号冷却**（452 解除）后，跑全扫：
   ```bash
   cd geekbang_lab
   python product_list_lab.py --exp exp6        # 或逐个 --type 分批跑，避开限流
   ```
2. 脚本会输出 `total_unique_courses` 与 `target_id_hits`。
3. **核对 `target_id_hits`**：5 门目标课是否全部命中。
   - 若全部命中 → 假设成立，"之前查不到"确为 `with_articles=false` 之过，方法确认。
   - 若仍有缺失 → 说明这少数课属于 product_list 完全不返回的另类目，只能走 `MY_COURSE_IDS` 直接指定 id（与之前一致）。
4. 把并集 `map` 写入爬虫用的 `jikeshijian/course_index.json`（结构：`{"updated_at":..., "by_title": {title: id, ...}}`）。
5. 爬虫 `jk_article.py` 离线读 `by_title` 解析 `MY_COURSES` 里的课名 → id，无需运行时查目录、不触发限流。

---

## 四、关键注意事项

- **452 限流是按 cookie/账号计**，本机代理（127.0.0.1:7897）绕不过；限流期间任何请求都 452。冷却后再跑。
- **不要无脑猛刷**：exp6 全扫请求量较大，建议用 `--type N` 分批、或拉开时间间隔，避免反复触发 452。
- `size` 可能被服务端忽略（exp4 验证）。翻页**以"实际返回条数"推进 `prev`**，不要死守 20。
- `learn/product`（我的课程）可作为**补充源**（覆盖已购/在学），但与 product_list 去重合并即可，不是全集主力。

---

## 五、待 exp6 确认后回填的结论

| 项目 | 当前状态 |
|---|---|
| 最优传参（with_articles=true + pvip 并集 + 全 type 扫） | ✅ 方法已定 |
| 5 门目标课是否真在 product_list 全集里 | ⏳ 待 exp6 实跑 |
| 全集课程总数（VIP 下） | ⏳ 待 exp6 实跑 |
| 最终是否仍需 `MY_COURSE_IDS` 兜底极少数课 | ⏳ 待 exp6 实跑 |

> exp6 跑完把 `lab_results.json` 里的 `exp6.output` 回填到 `experiments_log.md` 与本文件的第五节即可定稿。

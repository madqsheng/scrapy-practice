# product_list 接口实验记录

> 实验台脚本：`product_list_lab.py`（独立于 scrapy 框架，仅复用 `settings.py` 的 cookie）
> 目标接口：`POST https://time.geekbang.org/serv/v4/pvip/product_list`
> 浏览器真实请求体（基线）：
> `{"tag_ids":[],"product_type":0,"product_form":0,"pvip":0,"prev":0,"size":20,"sort":8,"with_articles":true}`

## 重要状态说明（2026-08-17）

- **账号当前处于 452 限流**（按 cookie 计，走本机代理 127.0.0.1:7897 也绕不过）。
- exp1 的**响应结构**来自限流前一次成功的 200 响应（已确认，参数无关，结构恒定）。
- **exp2–exp6 的实跑结论为 PENDING**——需等账号冷却后运行脚本：`python product_list_lab.py` 会自动把每个实验的真实 输入/输出/结论 写入 `lab_results.json` 并打印，届时把结果回填到本文件。
- 推荐冷却后**分批**跑，避免再次触发 452：`python product_list_lab.py --exp exp6 --type 0`、`--type 1` … 逐个 product_type 扫。

---

## exp1 — 基线：真实请求体第 1 页结构（✅ 结构已确认）

- **目的**：看清响应字段与分页结构，作为后续所有对照的基准。
- **输入（控制变量）**：`bp()` = 浏览器真实请求体（with_articles=true, size=20, prev=0, product_type=0, pvip=0）。
- **输出（来自限流前成功响应，结构恒定）**：
  - `code`: 0
  - `data` 顶层键：`categories`(null) / `page`(含 `more`,`total`) / `list`(列表) / `products`(列表，与 list 同内容) / `articles`(null)
  - 第 1 页返回课程数（size=20 理论值 20；实测服务端可能自定，见脚本输出）
  - 单个 product 字段（共 50+）：`id`, `title`, `type`, `is_column`, `is_video`, `is_opencourse`, `in_pvip`, `is_join_cvip`, `column`, `author`, `cover`, `price`, `is_finish` … 等
  - 样例：`product[0]` = `{id:101181501, title:"DeepSeek Harness 极简入门", type:"p29"}`
- **结论**：响应以 `data.products`（或 `data.list`）返回课程数组，`data.page.more` 控制是否还有下一页，`prev` 为偏移游标。结构稳定，与具体参数无关。

---

## exp2 — 控制变量：with_articles（PENDING 实跑）

- **目的**：验证 `with_articles=true` vs `false` 是否改变**返回的课程集合**（核心假设：之前用 false 才漏掉那 5 门）。
- **输入**：
  - `bp(with_articles=True)`
  - `bp(with_articles=False)`
  - （其余固定：product_type=0, pvip=0, size=20, prev=0）
- **输出（待填）**：`count_true` / `count_false` / `ids_only_in_true` / `ids_only_in_false` / `sets_equal`
- **预期/假设**：若 `sets_equal=False` 且 `ids_only_in_true` 非空，说明 `with_articles=true` 才返回完整课程集——这正是之前"查不到"的根因。
- **结论**：（待脚本实跑后填写）

---

## exp3 — 控制变量：pvip（PENDING 实跑）

- **目的**：验证 `pvip=0` vs `pvip=1` 是否返回不同课程集合；确定 VIP 全集是否需要两者取并集。
- **输入**：
  - `bp(pvip=0)`
  - `bp(pvip=1)`
  - （with_articles=True, product_type=0, size=20, prev=0）
- **输出（待填）**：`count_pvip0` / `count_pvip1` / `ids_only_in_pvip0` / `ids_only_in_pvip1` / `sets_equal`
- **预期/假设**：两者集合大概率不同（非包含关系），VIP 全集 = pvip=0 ∪ pvip=1。
- **结论**：（待脚本实跑后填写）

---

## exp4 — 控制变量：size（PENDING 实跑）

- **目的**：确认 `size` 是否被服务端遵守，决定翻页步长。
- **输入**：`bp(size=20)` / `bp(size=50)` / `bp(size=100)`（product_type=0, prev=0）
- **输出（待填）**：`returned_count_per_size = {20:?, 50:?, 100:?}`
- **预期/假设**：服务端可能忽略 size 或封顶（此前 size=100 仍只回 ~15 条）。若被忽略，翻页需按"实际返回条数"推进 `prev`，而非死用 20。
- **结论**：（待脚本实跑后填写）

---

## exp5 — 控制变量：prev 游标（PENDING 实跑）

- **目的**：验证 `prev` 作为偏移游标：prev=0/20/40 是否互不重叠且可累积翻完。
- **输入**：`bp(prev=0)` / `bp(prev=20)` / `bp(prev=40)`（product_type=0）
- **输出（待填）**：每页 `count`、相对前一页的 `new_ids`、三页累计 `cumulative_ids`
- **预期/假设**：各页 id 基本不重叠，按 `prev += 本页返回条数` 推进即可不重不漏。
- **结论**：（待脚本实跑后填写）

---

## exp6 — 全类型 × pvip 全集扫描 + 目标检索（PENDING 实跑，核心实验）

- **目的**：用"最优参数"扫全 `product_type`(0..12) × `pvip`(0,1)，并集后检索那 5 门"之前被认为不在 product_list 里"的课，确定最终映射方法。
- **输入**：
  - 遍历 `product_type ∈ 0..12`，每类型再遍历 `pvip ∈ {0,1}`
  - 每页 `bp(product_type=pt, pvip=pv, prev=逐步+size)`，直到 `page.more=false`
  - 默认 `with_articles=true, size=20, sort=8`
- **输出（待填）**：
  - `total_unique_courses`：并集去重后的课程总数
  - `per_type`：每个 (pt,pvip) 的课程数 / 页数 / total
  - `target_id_hits`：5 门目标课的 id 是否命中及对应 title
  - `target_name_hits`：按课名子串命中的结果
- **目标 5 门**：
  | id | 课名 |
  |---|---|
  | 101119601 | Claude Code Skill入门实战课 |
  | 100799801 | RAG前沿入门课 |
  | 101069801 | AI Agent入门第一课：零基础玩转智能体 |
  | 101170001 | Harness Agent 脚手架实战课 |
  | 101128701 | Claude Code 企业级全链路开发实战 |
- **预期/假设**：若用 `with_articles=true` 且 `pvip` 取 0∪1 全扫，这 5 门应全部命中——从而证明它们**本来就在 product_list 里**，之前的"查不到"纯粹是参数（with_articles=false）之过。
- **结论**：（待脚本实跑后填写，将直接决定 course_index_method.md 的最终方法）

---

## 运行方式（冷却后）

```bash
cd geekbang_lab
# 全部实验（轻量 exp1-5 先跑，exp6 全扫较重，建议分批）
python product_list_lab.py

# 或只跑某个
python product_list_lab.py --exp exp2
python product_list_lab.py --exp exp6 --type 3      # 只扫 product_type=3

# 走本机代理（复刻浏览器出口，但 452 按 cookie 计，代理无效）
python product_list_lab.py --proxy http://127.0.0.1:7897
```

每个实验的 输入/输出/结论 会实时打印，并汇总到 `lab_results.json`。

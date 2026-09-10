---
type: note
tags: [数据库] [性能测试] [PostgreSQL]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# PostgreSQL 性能调优

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 中间件章-PostgreSQL 小节（性能调优）

## **1\.1 性能调优**

### **📈 核心参数配置**

|参数分类|参数名|推荐配置/公式|核心作用与说明|
|---|---|---|---|
|内存|`shared_buffers`<br>|物理内存的 25%<br>\(如 16GB 内存 → 4GB\) |最关键参数。数据库缓存池，用于缓存数据页。`wal_buffers` 通常设为 `shared_buffers` 的 1/32 即可 。|
||`effective_cache_size`<br>|物理内存的 50%\-75%<br>\(如 16GB 内存 → 12GB\) |优化器参数。告诉 PostgreSQL 操作系统有多少可用缓存，影响优化器选择索引扫描还是全表扫描。|
||`work_mem`<br>|4MB \- 16MB<br>\(复杂分析场景可到 64MB\-256MB\) |排序/哈希操作内存。注意这是每个操作的内存，设置过高会导致高并发下内存溢出。|
|写入|`wal_buffers`|16MB \- 64MB |WAL 日志缓冲区大小。写入频繁时可适当增加。|
||`synchronous_commit`|`OFF` \(高性能/允许丢数据\)<br>`ON` \(金融级/强一致性\) |权衡性能与持久性。设为 `OFF` 能大幅提升写入性能，但数据库崩溃可能丢失最近事务。|
||`checkpoint_completion_target`|`0.9` |平滑检查点。让检查点分散完成，避免一次性写入大量数据造成 IO 尖峰。|
||`max_wal_size` / `min_wal_size`|`max_wal_size = 2GB`<br>`min_wal_size = 1GB` |控制 WAL 日志总量和检查点频率。|
|并发<br>|`max_connections`|100 \- 500<br>建议配合连接池使用 |最大连接数。设置过高会增加上下文切换开销，每个连接都会消耗 `work_mem` 内存。|
||`max_worker_processes`|CPU 核心数<br>\(如 8 核 → 8\) |系统能支持的最大后台进程数。|
||`max_parallel_workers_per_gather`|2 \- 4<br>\(如 4\) |每个查询最多能使用的并行工作进程数。影响并行查询效果。|
|查询|`effective_io_concurrency`|`200` \(SSD\)<br>`2` \(传统 HDD\)|预读的并发 IO 请求数。SSD 可以设高，HDD 设低。|
||`random_page_cost`|`1.1` \(SSD\)<br>`4` \(传统 HDD\) |随机访问磁盘页的成本。SSD 下设为 1\.1 可以鼓励优化器使用索引。|
|维护|`autovacuum`<br>|`ON` \(强烈建议开启\) <br>|自动清理过期元组，防止表膨胀，是 PostgreSQL 稳定运行的关键。|
||`autovacuum_vacuum_scale_factor`|`0.05 - 0.1` \(大表\) |触发 VACUUM 的表变更比例。对于大表，建议调小更积极地触发清理。|

> **一个常用的内存估算安全公式为：**
> **`shared_buffers + (work_mem × max_connections × 并发复杂操作数) + 操作系统及其他应用预留内存 ≤ 总物理内存`**
> 
> 

### **🍔 索引优化**

### **🍟 执行计划分析**

**🔧 系统化排查五步法**

当面对一条需要分析的SQL时，遵循以下标准化流程，避免遗漏和误判：

#### 第一步：获取真实执行计划（而非猜测）

```Plain Text
*-- 基础版：预估执行计划（所有版本通用）*
EXPLAIN SELECT ...;

*-- 进阶版：JSON格式，包含成本估算与详细路径（5.7+）*
EXPLAIN FORMAT=JSON SELECT ...;

*-- 终极版：真实执行统计（8.0.18+，强烈推荐）*
EXPLAIN ANALYZE SELECT ...;
```

- 优先使用 `EXPLAIN ANALYZE`：它返回的是实际执行时间、实际扫描行数、实际循环次数，彻底消除统计信息不准导致的误判

- 注意：`EXPLAIN ANALYZE` 会真正执行SQL，生产环境务必确认SQL安全（无UPDATE/DELETE副作用），或加 `LIMIT` 限制

#### **第二步：建立基线对比**

孤立看一次执行计划意义有限，必须有参照物：

- 历史基线：该SQL上周/上月的执行计划是什么？`rows`、`type`、`key` 是否有突变？

- 同类SQL基线：相同模式的其他查询表现如何？是个例还是系统性问题？

- 预期基线：根据索引设计和数据分布，理论上应该走什么计划？实际与理论的差距在哪？

#### **第三步：逐层诊断（由粗到细）**

```Plain Text
┌─────────────────────────────────┐
│  Level 1: type + rows                                 │ ← 定性：全扫 vs 索引扫？量级合理吗？
├─────────────────────────────────┤
│  Level 2: key + possible_keys                         │ ← 定位：走了对的索引吗？为什么没用上？
├─────────────────────────────────┤
│  Level 3: Extra                                       │ ← 排雷：filesort? temporary? BNL?
├─────────────────────────────────┤
│  Level 4: filtered + cost                             │ ← 量化：索引区分度够吗？优化器成本计算合理吗？
├─────────────────────────────────┤
│  Level 5: EXPLAIN ANALYZE 实测                         │ ← 验证：预估vs实际偏差多大？瓶颈在哪个算子？
└─────────────────────────────────┘
```

#### **第四步：根因归类与处置**

将诊断结果归入以下类别，匹配对应解决方案：

|根因类别|典型表现|处置动作|
|---|---|---|
|索引缺失/设计不当|key=NULL, type=ALL, 缺少联合索引|创建/调整索引；遵循最左前缀与覆盖索引原则|
|SQL写法问题|函数包裹列、隐式转换、LIKE '%x'、OR|改写SQL；将运算移至等号右侧；拆分UNION ALL|
|统计信息失真|possible\_keys有值但key=NULL，rows严重偏离|ANALYZE TABLE 更新统计信息；检查采样率|
|优化器误判|走了次优索引，cost计算不合理|Force Index临时止血；调整 optimizer\_switch；反馈Bug|
|数据倾斜/热点|filtered极低，特定参数值导致计划劣化|绑定执行计划\(Plan Binding\)；分区/分表；应用层缓存|
|资源瓶颈|执行计划正确但依然慢|检查IO/CPU/锁等待；调大buffer；硬件扩容|

#### 第五步：验证与回归

- 修改后重新EXPLAIN确认计划符合预期

- 压测验证：单次执行快不代表并发下稳定，需模拟真实负载

- 监控埋点：为该SQL添加慢日志标记或APM追踪，持续观察7天以上

---

#### 💡 高频陷阱与避坑指南

1. "EXPLAIN显示走了索引，但还是慢"

    - 检查 `rows`：走了索引但扫描100万行 ≈ 全扫

    - 检查 `Extra`：`Using index condition` \+ 大量回表 = IO瓶颈

    - 检查锁：执行计划没问题，但在等锁（结合 `SHOW ENGINE INNODB STATUS`）

2. "测试环境快，生产环境慢"

    - 数据量级不同导致执行计划不同 → 用生产数据量级做EXPLAIN

    - 缓冲池状态不同 → 冷数据首次加载必然慢

    - 并发竞争 → 单线程EXPLAIN无法反映锁争用

3. "加了索引反而更慢了"

    - 写入性能下降：索引越多，INSERT/UPDATE越慢

    - 优化器选了错误索引：新索引区分度低，被误选 → 删除冗余索引或Force Index

    - 回表代价高于全扫：小表全扫可能比大索引\+回表更快

4. 过度依赖 Force Index

    - Force Index 是临时止血手段，不是长期方案

    - 数据分布变化后，强制索引可能变成新的瓶颈

    - 根本解法是优化索引设计或SQL写法

---

#### 📋 执行计划分析Checklist

* [ ] `type` ≥ `range`，非 `ALL` / `index`

* [ ] `key` 命中预期索引，非 `NULL`

* [ ] `rows` 预估扫描行数 \< 总行数 10%（或绝对值 \< 10万）

* [ ] `Extra` 无 `Using filesort` / `Using temporary` / `Block Nested Loop`

* [ ] `filtered` \> 50%（高区分度）

* [ ] 关联查询被驱动表关联字段有索引

* [ ] `EXPLAIN ANALYZE` 实际耗时 \< SLA阈值

* [ ] 已考虑数据量增长后的计划稳定性

---

#### 📊 核心指标及优化方案

|指标字段|🚨 危险/警告信号|✅ 健康/理想信号|核心解读与优化方向|
|---|---|---|---|
|type \(访问类型\)|`ALL` \> `index`|`const` \> `eq_ref` \> `ref` \> `range`|最重要的性能指标。`ALL`为全表扫描，`index`为全索引扫描。至少应优化到 `range` 级别；单行查询应为 `const`/`eq_ref`|
|key \(实际索引\)|`NULL`|命中预期的联合索引名称|`NULL` 表示未使用任何索引。若命中的不是预期索引，需检查统计信息或调整索引设计|
|rows \(预估行数\)|接近表总行数 / 百万级|个位数 \~ 千级别|优化器预估需要扫描的行数。注意：这是估算值，但趋势准确。数值越大，IO/CPU 消耗越高|
|Extra \(附加信息\)|`Using filesort`<br>`Using temporary`<br>`Using index condition` \(ICU回表多\)|`Using index`<br>`Using where`|🔴 filesort/temporary: 产生额外排序或临时表，必须优化<br>🟢 Using index: 覆盖索引，无需回表，最优状态|
|filtered \(过滤率\)|`< 10%`|`> 80%` \~ `100%`|表示按条件过滤后剩余行的百分比。值越低说明索引区分度越差，扫描了大量无效数据|
|possible\_keys|有值但 `key=NULL`|与 `key` 一致|表示"可以用"但"没用上"。通常因统计信息过期、成本计算过高或隐式转换导致，可尝试 `ANALYZE TABLE`|
|partitions|匹配多个分区 / `NULL`\(未分区大表\)|仅匹配目标分区|分区表必看。未命中分区裁剪会导致跨分区扫描，性能急剧下降|
|table|`(derived)` / `(subquery)`|具体表名|出现派生表/子查询意味着创建了内存临时表。应尽量改写为 JOIN 或 CTE|

---

#### 💡 实战分析四步法

1. 看 type \+ rows：快速定性，判断是全扫还是索引扫描，扫描量级是否合理

2. 看 key \+ possible\_keys：确认是否走了正确的索引，是否存在"能用不用"的情况

3. 看 Extra：排查隐藏的性能杀手（filesort、temporary、BNL）

4. 看 filtered：验证索引有效性，低过滤率 = 索引区分度不足 = 需要重建索引或改写SQL

---

#### ⚠️ 注意事项

- EXPLAIN 是预估，不是实测：`rows` 基于统计信息，可能与实际偏差较大。MySQL 8\.0\+ 可使用 `EXPLAIN ANALYZE` 获取真实执行时间和行数

- 缓存干扰：首次执行与缓存命中后的执行计划可能不同，分析时建议关闭查询缓存或使用 `SQL_NO_CACHE`

- 绑定变量窥探：参数化查询的执行计划可能因首次传入的参数值而被"带偏"，需关注执行计划稳定性

- 版本差异：MySQL 5\.7 与 8\.0 的优化器行为有显著差异（如 8\.0 默认关闭 BNL、引入 Hash Join），升级后需重新验证关键SQL

### **🍕 慢查询排查**

### **📌 shared\_buffers**

1\.PostgreSQL 中用于设置共享内存缓冲区大小的核心参数。它决定了数据库用于缓存数据（如表和索引）的内存量，直接影响数据库的读取性能。

2\.简单来说，数据库在读取数据时，会优先到这里查找。较大的 shared\_buffers 可以提高热点数据的访问速度，但并非越大越好。

3\.PostgreSQL 采用“双缓存”架构设计，这是容易忽略但对性能影响深远的特点。与 MySQL 等倾向于“独占”大部分内存的数据库不同，PostgreSQL 的设计哲学是与操作系统（OS）协作，而非竞争。官方文档明确指出，PostgreSQL“也依赖操作系统缓存”，这意味着数据库性能的优化需要同时关注 shared\_buffers 和 OS Page Cache 两个层面。

- **核心作用**

你可以将 `shared_buffers` 理解为数据库在内存中开辟的一个“高速仓库”。当数据库需要读取数据时，会优先在这个仓库中查找（即缓存命中），如果找到则直接从内存返回数据，从而避免耗时的磁盘 I/O 操作；如果没有找到，才会去磁盘读取并将数据加载到该仓库中供下次使用。

- **配置建议与“双缓存”机制**

虽然增大 `shared_buffers` 能提升查询速度，但并非越大越好。PostgreSQL 依赖操作系统缓存（OS Page Cache）来管理 WAL（预写式日志）和临时文件等，因此系统存在“双缓存”机制。如果将 `shared_buffers` 设置过大，不仅会挤占 OS Cache 和其他进程的内存，还可能引发内存竞争导致系统使用交换分区（swap），反而严重拖累整体性能。

**🧠 理解“双缓存”协作模型**

在讨论具体的配置前，先要理解 PostgreSQL 的数据流路径：磁盘 → OS Page Cache → PostgreSQL `shared_buffers` → 客户端。

- **为何不只用 OS 缓存？** 如果 PostgreSQL 完全依赖 OS 缓存，那么读数据时，数据会先从磁盘进入 OS 缓存，再拷贝到数据库进程的内存空间。而 `shared_buffers` 作为数据库专用的缓存，可以让“热”数据（高频访问的数据）以更高效的数据库内部格式“黏”在缓冲区中，减少了与 OS 之间的数据拷贝和转换开销，从而提升 CPU 效率。

- **为何不设置过大的 ****`shared_buffers`****？ **这是许多用户的直觉，但在 PostgreSQL 中并非如此。如果 `shared_buffers` 设置得过大（比如超过物理内存的 40%），会直接挤压 OS Page Cache 的空间。但 OS Page Cache 对于处理顺序扫描（全表扫描） 和降低文件系统 I/O 延迟至关重要。因此，一个偏小的 `shared_buffers`（如总内存的 15%\-25%）配合一个足够大的 OS Page Cache，往往能带来更好的整体性能。

- **为什么不是越大越好？**

很多人误以为 shared\_buffers 越大越好，这是错的。原因：

1. PostgreSQL 使用双重缓存：

    - `shared_buffers`：PostgreSQL 自己的缓存（按 8KB 页管理）

    - 操作系统页缓存：文件系统层面的缓存

    - 设置过大 = 让 PostgreSQL 和 OS 抢内存，且两边的缓存内容可能重复

2. 管理开销：`shared_buffers` 太大时，PostgreSQL 维护缓存描述符（descriptor）的开销会显著增加，扫描整个缓存池的时间变长。

3. 典型的最佳实践（来自 PostgreSQL 社区经验）：

    - 小内存（≤8GB）：25% 总内存

    - 中内存（16GB\-64GB）：20% 总内存

    - 大内存（≥128GB）：10%\-15% 总内存，且通常不超过 64GB

### **📌 work\_mem**

- 含义：控制单个查询操作（如排序 `ORDER BY`、哈希连接 `Hash Join`、哈希聚合等）在写入磁盘临时文件之前可以使用的最大内存量。

- 配置建议：

    - 推荐大小：默认值通常为 4MB，对于复杂查询偏小。OLTP（事务型）场景建议设为 4\~16MB；OLAP（复杂分析型）场景可设为 64\~256MB。

    - 风险提示：`work_mem` 是每个操作的内存上限，一个复杂查询可能包含多个排序或哈希操作，且高并发下每个连接都可能消耗多个 `work_mem`。如果设置过高，极易导致服务器内存耗尽（OOM）。

    - 精细调优：建议不要盲目调高全局 `work_mem`，可以通过 `EXPLAIN ANALYZE` 观察是否产生了磁盘临时文件（`external merge disk`），或者针对特定用户/会话动态调整（如 `SET work_mem = '256MB';`）。

    - 生效方式：动态参数，重载配置或会话级 `SET` 即可生效。

### **📌 max\_connections**

- 含义：限制数据库允许的最大并发连接数。PostgreSQL 采用基于进程的连接模型，每个连接都会消耗一定的内存和系统资源。

- 配置建议：

    - 推荐大小：小型应用 50\~100；中大型应用配合连接池设为 200\~500；超高并发场景也建议控制在 1000 以内，以避免过高的上下文切换开销。

    - 内存消耗：每个连接大约消耗 5\~10MB 的基础内存开销。

    - 最佳实践：不要直接通过提高 `max_connections` 来应对高并发。正确的做法是保持合理的数据库连接数，并在应用层或数据库前置连接池（如 PgBouncer）来复用连接，这能显著降低数据库的连接延迟和内存压力。

    - 生效方式：修改此参数后必须重启数据库服务才能生效。

### **📌 effective\_cache\_size**

虽然 effective\_cache\_size 本身不实际分配内存，但它会直接影响 PostgreSQL 优化器的决策逻辑。设置过大会导致优化器低估随机 I/O 的成本，从而选择不合适的执行计划，最终让某些查询变慢数千倍。它告诉规划器系统（包括 shared\_buffers 和操作系统缓存）总共有多少内存可用于磁盘数据缓存。

**⚙️ 原理：它是如何影响优化器的？**

简单来说，优化器在决定“走索引”还是“全表扫描”时，会计算一个“成本分数”。`effective_cache_size` 是其中关键的修正因子。

- 设置过小：优化器认为“缓存很小，随机读大概率要碰磁盘”，会倾向于选择成本更稳定的全表扫描（顺序读）。

- 设置过大（问题所在）：优化器认为“数据几乎都在缓存里”，从而严重低估索引扫描的成本。这会导致它在应该走全表扫描（比如需要读取表中大量数据）的时候，错误地选择了索引扫描。

- 配置建议：

    - 推荐大小：建议设置为服务器物理内存的 50% \~ 75%。

    - 作用机制：如果设置较大，规划器会乐观地认为数据大概率在缓存中，从而更倾向于选择索引扫描；如果设置过小，规划器会悲观地认为随机读取会导致大量物理 I/O，从而更倾向于选择全表扫描。

    - 生效方式：修改后无需重启，执行 `SELECT pg_reload_conf();` 重载配置即可生效。

## 1\.2 常用语法

### **1\.2\.1 连接查询**

- **内连接（INNER JOIN）**

内连接是最常用的连接类型，它仅返回两个表中满足连接条件的交集数据。如果某行在另一个表中没有匹配的行，则该行不会出现在结果集中。

语法格式：

```SQL
SELECT 字段列表 
FROM 表1 [INNER] JOIN 表2 ON 连接条件;
```

隐式内连接（不推荐，容易混淆）：

```SQL
SELECT 字段列表 FROM 表1, 表2 WHERE 连接条件;
```

示例：查询每个员工的姓名及其所属的部门名称

```SQL
SELECT e.name, d.name 
FROM emp e INNER JOIN dept d ON e.dept_id = d.id;
```

- **外连接（OUTER JOIN）**

外连接不仅返回满足连接条件的交集数据，还会保留指定表中的所有数据。对于未匹配上的行，结果集中的对应列会用 `NULL` 值填充。外连接分为三种：

- **左外连接（LEFT JOIN）：**

以左表为基准，返回左表的所有数据及右表中匹配的数据。常用于“查询所有员工及其部门信息（即使该员工尚未分配部门）”的场景。

```SQL
SELECT 字段列表 FROM 表1 LEFT [OUTER] JOIN 表2 ON 连接条件;

-- 查询每个学生的姓名、班级名、班级人数
SELECT 
    s.name,
    c.class_name,
    COUNT(*) OVER(PARTITION BY c.cid) AS class_count
FROM students s
LEFT JOIN classes c ON s.class_id = c.cid;
```

- **右外连接（RIGHT JOIN）：**

与左外连接相反，以右表为基准，返回右表的所有数据及左表中匹配的数据。

```SQL
SELECT 字段列表 FROM 表1 RIGHT [OUTER] JOIN 表2 ON 连接条件;
```

- **全外连接（FULL JOIN）：**

返回左表和右表中的所有行。当某行在另一个表中没有匹配时，对应部分填充 `NULL`。（注：MySQL 原生不支持此语法，通常需用 `UNION` 拼接左右连接来实现）

```SQL
-- MySQL写法
SELECT s.name, c.class_name
FROM students s
LEFT JOIN classes c ON s.class_id = c.cid
UNION
SELECT s.name, c.class_name
FROM students s
RIGHT JOIN classes c ON s.class_id = c.cid;

-- PostgreSQL 完全支持 FULL JOIN（MySQL 不支持）
SELECT s.name, c.class_name
FROM students s
FULL JOIN classes c ON s.class_id = c.cid;
```

- **自连接：**

自连接是指一张表与自身进行连接查询。它在逻辑上等同于将同一张表视为两张不同的表，因此必须为表定义别名来区分。

应用场景：处理具有层级或递归关系的数据

例如查询员工的姓名及其直接上级的姓名：

```SQL
SELECT e1.name AS '员工', e2.name AS '领导'
FROM emp e1 JOIN emp e2 ON e1.manager_id = e2.id;
```

- **多表连接：**

```SQL
-- 学生 → 班级 → 班主任
SELECT s.name, c.class_name, t.teacher_name
FROM students s
JOIN classes c ON s.class_id = c.cid
JOIN teachers t ON c.teacher_id = t.tid;
```

**💡 进阶使用技巧与避坑指南**

- 避免 NULL 值过滤陷阱：在使用 `LEFT JOIN` 时，如果对右表的字段进行 `WHERE` 条件过滤，会导致左外连接失效（退化为内连接）。正确的做法是将右表的过滤条件写在 `ON` 子句中。

- 性能优化建议：在进行多表连接时，应尽量遵循“小表驱动大表”的原则，让数据量较小（或过滤后结果集较小）的表作为外层循环，去匹配数据量较大的表，比如左连接的左表就是驱动表；同时，可以通过先过滤再连接（子查询替代）的方式减少参与连接的数据量，从而提升查询效率。

```SQL
-- 基础连接模板
SELECT 列名
FROM 左表
[连接类型] JOIN 右表 ON 连接条件
[WHERE 过滤条件]
[GROUP BY 分组列]
[HAVING 分组后过滤]
[ORDER BY 排序列];
```

|注意点|说明|
|---|---|
|优先使用 INNER JOIN|比 LEFT JOIN 效率高|
|小表驱动大表|连接顺序影响性能|
|连接字段建索引|在 ON 条件的列上创建索引|
|\*\*避免 SELECT \*\*\*|只取需要的列|
|控制连接表数量|一般不超过 3\-5 张表|

---

### **1\.2\.2 差集查询**

- **使用 EXCEPT 或 MINUS 操作符**

最直观的集合差集操作。如果数据库支持该操作符，可以直接使用：

`EXCEPT`：适用于 MySQL 8\.0\+、PostgreSQL、SQL Server 等。

`MINUS`：适用于 Oracle 等数据库。

**示例**：

```SQL
-- 查找在 table1 中存在但在 table2 中不存在的记录
*SELECT id, data FROM table1
EXCEPT
**SELECT id, data FROM table2;*
```

- **使用 ****`LEFT JOIN`**** \+ ****`IS NULL`**

这是一种兼容性极强的方法，适用于几乎所有关系型数据库（包括不支持 `EXCEPT` 的旧版 MySQL）。通过左连接保留左表的所有数据，然后过滤掉右表中能匹配上的数据（即右表关联字段为 NULL 的记录）。

**示例**：

```SQL
*SELECT t1.*
FROM table1 t1
LEFT JOIN table2 t2 ON t1.id = t2.id
**WHERE t2.id IS NULL;*
```

- **使用子查询 \(****`NOT IN`**** 或 ****`NOT EXISTS`****\)**

这是一种兼容性极强的方法，适用于几乎所有关系型数据库（包括不支持 `EXCEPT` 的旧版 MySQL）。通过左连接保留左表的所有数据，然后过滤掉右表中能匹配上的数据（即右表关联字段为 NULL 的记录）。

**示例 NOT IN **：

```SQL
*SELECT id, data 
FROM table1 
**WHERE id NOT IN (SELECT id FROM table2);*
```

**示例 NOT EXISTS（通常在大数据量下性能更优）**：

```SQL
*SELECT t1.*
FROM table1 t1
WHERE NOT EXISTS (
    SELECT 1 
    FROM table2 t2 
    WHERE t1.id = t2.id
**);*
```

**💡 补充提示：如何同时找出两张表的“双向差异**

如果您想一次性查出两张表中互不相同的数据，可以将上述查询用 `UNION ALL` 拼接起来。例如使用 `LEFT JOIN` 的双向差异查询：

```SQL
*-- 找出 table1 有但 table2 没有的数据
SELECT t1.*, '仅在table1' as source FROM table1 t1 LEFT JOIN table2 t2 ON t1.id = t2.id WHERE t2.id IS NULL
UNION ALL
-- 找出 table2 有但 table1 没有的数据
**SELECT t2.*, '仅在table2' as source FROM table2 t2 LEFT JOIN table1 t1 ON t2.id = t1.id WHERE t1.id IS NULL;*
```

---

### **1\.2\.3 分组 group by**

- `GROUP BY`：核心是“分组汇总”，将数据按一个或多个列的值进行分组，然后对每个组应用聚合函数（如 `COUNT`、`SUM`、`AVG`）进行汇总计算。

- 基本语法：

```SQL
-- 统计每个部门有多少员工
SELECT department, COUNT(*) AS employee_count
FROM employees
GROUP BY department;
```

- 多列分组

```SQL
-- 统计每个部门中，每个薪资水平的人数
SELECT department, salary, COUNT(*) AS employee_count
FROM employees
GROUP BY department, salary;
-- 统计出 Sales 部门中拿 5000 的人有几个，拿 6000 的又有几个。
```

- 如果在 `SELECT` 列表中包含了非聚合列，那么这些列必须同时出现在 `GROUP BY` 子句中。否则，数据库不知道应该从组里选择哪个值来显示。

```SQL
-- 错误示例：'name' 既不在 GROUP BY 中，也不是聚合函数
-- SELECT department, name, COUNT(*)
-- FROM employees
-- GROUP BY department;

-- 正确写法：要么把 'name' 加到 GROUP BY 里
SELECT department, name, COUNT(*)
FROM employees
GROUP BY department, name;
```

**核心特点:**

- 将数据按指定列分组，相同值的行会被合并为一组。

- `SELECT` 子句中出现的非聚合列，必须出现在 `GROUP BY` 中（否则报错或产生不确定结果）。

- 必须配合聚合函数（`COUNT()`, `SUM()`, `MAX()`, `MIN()`, `AVG()`）才有实际意义。

- 可以使用 `HAVING` 对分组后的结果进行过滤（`WHERE` 是对分组前的原始行过滤）。

---

### **1\.2\.4 去重 distinct**

- `DISTINCT`：专注于去重，用于从结果集中去除重复行，它直接作用于 `SELECT` 语句中指定的所有列，返回唯一值。

- 基本语法：

```SQL
-- 查询所有不重复的部门名称
SELECT DISTINCT department
FROM employees;

SELECT DISTINCT column1, column2, ...
FROM table_name;
```

- 多列去重

当对多个列使用 `DISTINCT` 时，它会返回这些列所有值的唯一组合。

```SQL
-- 查询每个部门中，所有不重复的薪资水平
SELECT DISTINCT department, salary
FROM employees;
```

**核心特点**

- 作用于 `SELECT` 后面的所有列。只有当这些列的组合完全相同时，才会被去重。

- 不能直接用于 `WHERE` 子句中（但可以在子查询中使用）。

- 通常用于只需要知道“有哪些不重复的值”的场景，不需要做统计计算。

---

### **1\.2\.5 诊断工具 explain**

- **基本用法**

    只需在需要分析的 SQL 语句前加上 `EXPLAIN` 关键字即可。它适用于 `SELECT`、`DELETE`、`INSERT`、`REPLACE` 和 `UPDATE` 等语句。

    ```SQL
    EXPLAIN SELECT * FROM users WHERE age > 30;
    
    -- JSON 格式，适合复杂查询的深度分析
    EXPLAIN FORMAT=JSON SELECT * FROM orders WHERE user_id = 100;
    
    -- TREE 格式（MySQL 8.0.16+）
    EXPLAIN FORMAT=TREE SELECT * FROM orders WHERE user_id = 100;
    ```

- **输出的核心字段解析**

    **1\. ****`id`****（查询标识符）**

    表示查询中每个子查询或表的执行顺序。通常 `id` 值越大，执行的优先级越高；如果 `id` 相同，则表示它们处于同一层级（可能并行执行）。

    **2\. ****`select_type`****（查询类型）**

    描述查询中每个 `SELECT` 子句的性质。常见值包括：

    - SIMPLE：简单查询，不包含子查询或联合查询。

    - PRIMARY：最外层的主查询。

    - SUBQUERY：出现在 `SELECT` 或 `WHERE` 子句中的子查询。

    - UNION：联合查询（UNION）的一部分。

    - DERIVED：派生表，即子查询生成的临时表。

    **3\. ****`table`****（访问的表）**

    显示当前行记录对应的表名或别名。如果涉及多表 JOIN，它会显示表的连接顺序。

    **4\. ****`type`****（访问类型 / 连接类型）⭐️**

    这是衡量查询效率的最重要指标，表示 MySQL 在表中找到所需行的方式。性能从好到坏依次为：

    - system / const：通过主键或唯一索引直接定位到一行，性能最好。

    - eq\_ref：使用唯一索引进行关联查询，对每个前驱记录只读取一条匹配记录。

    - ref：使用非唯一索引进行查找，可能会找到多条匹配的行。

    - range：索引范围扫描，常见于 `BETWEEN`、`IN`、`>`、`<` 等操作。

    - index：全索引扫描，虽然避免了全表扫描，但仍需遍历整个索引树。

    - ALL：全表扫描，性能最差，通常需要立即优化（如添加索引）。

    **5\. ****`possible_keys`**** 与 ****`key`****（索引使用情况）**

    - possible\_keys：查询中*可能*使用到的索引。如果为 NULL，表示没有可用的索引。

    - key：MySQL *实际决定*使用的索引。如果这一列为 NULL，表示查询未使用任何索引，这是一个需要高度关注的“红旗信号”。

    **6\. ****`rows`****（预估扫描行数）**

    表示 MySQL 估计需要扫描的行数。这个值越小越好。如果 `rows` 的值远大于实际返回的行数，通常意味着索引选择不当或缺失。

    **7\. ****`Extra`****（额外执行信息）**

    提供查询执行时的额外细节，常见的关键信息包括：

    - Using index：查询使用了覆盖索引，无需回表查询数据行，性能较好。

    - Using where：表示 MySQL 在存储引擎检索行后再进行条件过滤。

    - Using temporary：表示查询需要创建临时表，常见于排序或分组（GROUP BY）操作，通常需要优化。

    - Using filesort：表示 MySQL 无法利用索引进行排序，需要额外的排序步骤，会消耗较多资源。

- **实战案例：识别全表扫描与索引问题**

    假设有一张订单表 `orders`，包含字段 `order_id`（主键）、`user_id`、`amount`。现在需要查询 `user_id = 1000` 的所有订单：

    ```SQL
    EXPLAIN SELECT * FROM orders WHERE user_id = 1000;
    ```

    **诊断与优化：**
    如果 `EXPLAIN` 输出中 `type` 为 `ALL`，`key` 为 `NULL`，且 `rows` 为 10000（假设表中有 1 万行），这意味着 MySQL 正在执行全表扫描。原因是 `user_id` 字段上没有索引。

    **解决方案： 为该字段添加索引：**

    ```SQL
    CREATE INDEX idx_user_id ON orders(user_id);
    ```

    再次执行 `EXPLAIN`，你会发现 `type` 变成了 `ref`，`key` 显示为 `idx_user_id`，且 `rows` 大幅减少（例如变成 10 行），查询性能将得到显著提升。

- **注意事项与进阶建议**

1. 执行计划并非一成不变：`EXPLAIN` 展示的是优化器在某个时刻基于统计信息作出的决策。数据分布、索引状态、系统负载的变化都可能影响执行计划，因此分析必须结合实际情况动态进行。

2. 索引失效陷阱：即使有索引，某些写法也会导致索引失效。例如在 `WHERE` 子句中对列使用函数（如 `YEAR(birth_date) = 1990`）、使用 `OR` 连接非索引列、或者 `LIKE` 以通配符开头（如 `'%abc%'`），都会导致 `EXPLAIN` 显示全表扫描。

3. 更新统计信息：如果你发现索引存在但未被使用，可以运行 `ANALYZE TABLE` 来更新表的统计信息，这可能会影响并纠正优化器的选择。

4. 实际执行分析：在 MySQL 8\.0\.18 及以上版本，可以使用 `EXPLAIN ANALYZE`。它不仅显示执行计划，还会真正运行语句，并提供每个迭代器的实际耗时和返回行数，帮助你对比“优化器的期望”与“实际执行”的差异。

- **总结与最佳实践**

1. `EXPLAIN` 是起点：遇到慢查询，先用 `EXPLAIN` 看执行计划。

2. 抓重点：重点关注 `type`、`key`、`rows`、`Extra` 四列。

3. 警惕“坏”迹象：看到 `ALL` \(全表扫描\)、`Using filesort`、`Using temporary`，基本就是优化的信号。

4. 验证假设：通过建立索引、修改查询等方式优化后，再次用 `EXPLAIN` 验证效果，形成优化闭环。

5. 更新统计信息：如果发现索引没有被正确使用，运行 `ANALYZE TABLE` 来更新表的统计信息，这有助于优化器做出更准确的判断。

---

### **1\.2\.6 备份数据表**

备份数据库表通常有两种：一种是只备份表结构和数据（生成一个新的表），另一种是导出为 SQL 文件（用于迁移或灾难恢复）

- **MySQL / MariaDB**

在数据库内部执行（创建副本表）：

```SQL
-- 备份表结构和数据（最常用）
CREATE TABLE your_table_backup AS SELECT * FROM your_table;

-- 仅备份表结构（不包含数据）
CREATE TABLE your_table_backup LIKE your_table;
```

> *💡 提示：这种方式适合在同一个库内做临时备份，但不会保留原表的主键、索引、外键、约束、触发器以及注释等元数据。如果需要完整保留约束，建议先 SHOW CREATE TABLE your\_table; 获取建表语句，修改表名后再执行。*
> 
> 

如果您在备份时必须保留索引和约束，建议改用以下更稳妥的方案：

```SQL
-- 第一步：完整复制表结构（包含主键、索引、NOT NULL 等约束）
CREATE TABLE your_table_backup LIKE your_table;

-- 第二步：将数据插入到新表中
INSERT INTO your_table_backup SELECT * FROM your_table;
```

命令行执行（导出为 SQL 文件）：

```SQL
mysqldump -u 用户名 -p 数据库名 your_table > your_table_backup.sql
```

- **PostgreSQL**

在数据库内部执行（创建副本表）：

```SQL
-- 备份表结构和数据,不会保留原表的主键、索引、外键、约束、触发器以及注释等元数据
CREATE TABLE your_table_backup AS TABLE your_table;

-- 仅备份表结构
CREATE TABLE your_table_backup (LIKE your_table INCLUDING ALL);
-- 注：INCLUDING ALL 会同时复制约束、索引、默认值等
```

如果您在备份时必须保留索引和约束，建议改用以下更稳妥的方案：

```SQL
-- 仅备份表结构（包含索引、约束、默认值等）
CREATE TABLE your_table_backup (LIKE your_table INCLUDING ALL);

-- 随后手动插入数据
INSERT INTO your_table_backup SELECT * FROM your_table;
```

命令行执行（导出为 SQL 文件）：

```SQL
pg_dump -U 用户名 -d 数据库名 -t your_table -f your_table_backup.sql
```

### **1\.2\.7 存储过程**

存储过程（Stored Procedure） 是一组为了完成特定功能的 SQL 语句集，经编译后存储在数据库中。用户通过指定存储过程的名字并给出参数（如果有）来执行它。

可以把它理解成 数据库里的“函数”或“脚本”——你把一段复杂的业务逻辑写好后保存在数据库服务器上，以后随时调用，就像调用一个函数那样简单。

#### 1\.2\.7\.1 核心优势

1. 提高性能与减少网络传输：存储过程在创建时即在服务器上进行编译，执行速度快。同时，客户端无需将大量 SQL 语句通过网络发送给服务器，减少了网络传输量和 IO 交互次数。

2. 代码封装与复用：将复杂的业务逻辑（如关联修改多张表的数据）封装在存储过程中，简化了应用程序的开发，提高了 SQL 语句的重用性。

3. 安全性高：减少了 SQL 语句暴露在网上的风险。即使对于没有直接执行存储过程中底层语句权限的用户，也可授予他们执行该存储过程的权限。

#### 1\.2\.7\.2 参数类型

存储过程可以接收参数并返回数据，常见的参数类型包括：

- IN（输入参数）：用于向存储过程传入值。

- OUT（输出参数）：用于在执行完成后，将值返回给调用程序。

- INOUT（输入/输出参数）：既可以作为输入参数，也可以作为输出参数。

#### 1\.2\.7\.3 基础语法示例

在 MySQL 中创建存储过程时，由于默认的语句结束符为分号 `;`，为了避免与存储过程内部的 SQL 语句结束符冲突，通常需要使用 `DELIMITER` 关键字临时更改结束符。

1. **创建存储过程（MYSQL）**

以下示例创建了一个带有输入参数和输出参数的存储过程，用于查询指定员工的薪资并返回： 

```SQL
-- 创建存储过程的示例模板
DELIMITER //

CREATE PROCEDURE 过程名 ( [参数列表] )
BEGIN
    -- SQL语句集合
END //

DELIMITER ;


DELIMITER //
CREATE PROCEDURE get_employee_salary(
    IN emp_name VARCHAR(50), 
    OUT emp_salary DECIMAL(10,2)
)
BEGIN
    SELECT salary INTO emp_salary 
    FROM employees 
    WHERE name = emp_name;
END //
DELIMITER ;
```

```SQL
-- PostgreSQL 的标准语法
CREATE OR REPLACE PROCEDURE 过程名 ( [参数列表] )
LANGUAGE plpgsql  -- 指定使用 PL/pgSQL 语言
AS $$
BEGIN
    -- SQL语句集合
END;
$$;

-- 不需要//，使用 $$ 包裹函数体
-- PostgreSQL 11 及以上版本才支持的语法
-- 在 PostgreSQL 11 之前，所有的存储过程逻辑都必须写在 函数 (FUNCTION) 中。
```

- `DELIMITER //` 和 `DELIMITER ;` 是临时改变语句结束符，因为过程体内有多条 SQL，需要用 `//` 来表示整个过程结束。**注意结尾的 DELIMITER 和 ; 之间必须有空格。**

- 参数有三种模式：

    - `IN` ：输入参数（默认）

    - `OUT` ：输出参数（返回结果）

    - `INOUT` ：既输入又输出

2. **调用存储过程**

```SQL
CALL 过程名(参数值);

CALL get_employee_salary('张三', @salary);
SELECT @salary; -- 查看输出的薪资结果
```

3. **删除存储过程**

```SQL
DROP PROCEDURE IF EXISTS 过程名;

DROP PROCEDURE IF EXISTS get_employee_salary;
```

4. **查看存储过程定义**

```SQL
SHOW CREATE PROCEDURE 过程名;

SHOW CREATE PROCEDURE get_employee_salary;
```

#### 1\.2\.7\.4 优缺点

**优点**

1. **性能高**
存储过程在创建时就被编译和优化，并保存在数据库缓存中，执行时省去了每次编译的步骤，速度更快。

2. **减少网络流量**
你只需要发送 `CALL procedure_name(args)` 这一条短命令，而不是发送成百上千条的 SQL 语句，极大减少了网络传输量。

3. **安全性好**
可以控制用户对存储过程的执行权限，而不必授予用户对底层表的直接操作权限，防止数据被随意篡改。

4. **业务逻辑封装**
将复杂的业务规则封装在数据库层，便于维护和复用。如果规则变了，只需修改存储过程，应用层无需改动。

5. **事务管理方便**
可在存储过程内统一控制事务的提交与回滚，保证数据一致性。

**缺点**

1. **可移植性差**
不同数据库（MySQL、SQL Server、Oracle）的存储过程语法差异较大，换数据库时迁移成本高。

2. **调试困难**
相比应用代码，存储过程的调试工具较少，错误定位相对麻烦。

3. **版本管理不便**
不像应用代码那样方便地使用 Git 等工具做版本控制。

4. **过度使用可能导致业务逻辑分散**
如果所有逻辑都放在存储过程里，会让数据库负担过重，且逻辑难以追踪。

#### 1\.2\.7\.5 批量造测试数据

**方案 1：存储过程批量生成（MySQL 示例）**

```SQL
DELIMITER //
CREATE PROCEDURE generate_test_data(IN row_count INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE first_names VARCHAR(200) DEFAULT '张,王,李,刘,陈,杨,赵,黄,周,吴,徐,孙,马,朱,胡,郭,林,何,高,郑';
    DECLARE last_names VARCHAR(200) DEFAULT '伟,芳,娜,秀英,敏,静,丽,强,磊,洋,勇,艳,杰,娟,涛,明,超,秀兰,霞,平';
    DECLARE cities VARCHAR(200) DEFAULT '北京,上海,广州,深圳,杭州,成都,武汉,南京,西安,重庆';
    
    -- 关闭自动提交，提升性能
    SET autocommit = 0;
    
    WHILE i < row_count DO
        INSERT INTO users (
            name,
            age,
            city,
            email,
            created_at
        ) VALUES (
            CONCAT(
                SUBSTRING_INDEX(SUBSTRING_INDEX(first_names, ',', 1 + FLOOR(RAND()*20)), ',', -1),
                SUBSTRING_INDEX(SUBSTRING_INDEX(last_names, ',', 1 + FLOOR(RAND()*20)), ',', -1)
            ),
            18 + FLOOR(RAND()*50),  -- 年龄 18-67
            SUBSTRING_INDEX(SUBSTRING_INDEX(cities, ',', 1 + FLOOR(RAND()*10)), ',', -1),
            CONCAT('user', i, '@test.com'),
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND()*365) DAY)  -- 过去一年内
        );
        
        SET i = i + 1;
        
        -- 每1000条提交一次，防止事务过大
        IF i % 1000 = 0 THEN
            COMMIT;
        END IF;
    END WHILE;
    
    COMMIT;
    SET autocommit = 1;
END //
DELIMITER ;

-- 执行：生成10万条测试数据
CALL generate_test_data(100000);
```

**方案 2：更高效的方式 \- 利用现有表笛卡尔积**

如果你需要生成极大量数据，循环插入效率不高，可以用内存表 \+ 笛卡尔积的方式：

```SQL
-- 利用现有的任意一张表（如information_schema.tables）做笛卡尔积
INSERT INTO users (name, age, created_at)
SELECT 
    CONCAT('User', SEQ),
    20 + FLOOR(RAND()*40),
    NOW() - INTERVAL FLOOR(RAND()*1000) DAY
FROM (
    SELECT @rownum := @rownum + 1 AS SEQ
    FROM information_schema.tables t1,
         information_schema.tables t2,
         (SELECT @rownum := 0) r
    LIMIT 1000000  -- 生成100万条
) AS temp;
```

**🔧 推荐的测试数据工具**

- **Python Faker 库（最推荐）**

```Python
from faker import Faker
fake = Faker('zh_CN')
for _ in range(10000):
    print(f"INSERT INTO users VALUES ('{fake.name()}', {fake.random_int(18,65)}, '{fake.city()}');")
```

- **数据库自带工具**

    - MySQL：`mysqlsampledatabase` 或 `sysbench`

    - PostgreSQL：`pgbench`

- **GUI 工具**

    - Navicat 的数据生成功能

    - DBeaver 的 Mock Data

#### 1\.2\.7\.6 实战应用示例

- **示例：订单状态批量更新**

场景：电商系统中，每天凌晨需要将"已发货超过 7 天未确认收货"的订单自动更新为"已完成"。** **

```SQL
DELIMITER //

CREATE PROCEDURE auto_confirm_orders()
BEGIN
    DECLARE updated_count INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT '自动确认收货失败，已回滚' AS 执行结果;
    END;
    
    -- 开启事务
    START TRANSACTION;
    
    -- 更新订单状态
    UPDATE orders 
    SET order_status = '已完成',
        confirm_time = NOW(),
        update_time = NOW()
    WHERE order_status = '已发货'
      AND shipping_time <= DATE_SUB(NOW(), INTERVAL 7 DAY);
    
    -- 获取影响行数
    SET updated_count = ROW_COUNT();
    
    -- 记录操作日志
    INSERT INTO operation_log (
        operation_type,
        table_name,
        affected_rows,
        operator,
        create_time
    ) VALUES (
        '自动确认收货',
        'orders',
        updated_count,
        'SYSTEM',
        NOW()
    );
    
    -- 提交事务
    COMMIT;
    
    -- 返回执行结果
    SELECT CONCAT('自动确认收货完成，共更新 ', updated_count, ' 条订单') AS 执行结果;
END //

DELIMITER ;

-- 调用方式（通常由定时任务执行）
CALL auto_confirm_orders();
```

- **示例：数据归档与清理（运维必备）**

场景：将 3 个月前的日志数据迁移到归档表，并删除原表数据，释放主表空间。

```SQL
DELIMITER //

CREATE PROCEDURE archive_logs(IN archive_days INT)
BEGIN
    DECLARE archive_count INT DEFAULT 0;
    DECLARE delete_count INT DEFAULT 0;
    DECLARE batch_size INT DEFAULT 10000;  -- 每批次处理1万条
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT '日志归档失败，已回滚' AS 执行结果;
    END;
    
    START TRANSACTION;
    
    -- Step 1: 插入数据到归档表
    INSERT INTO logs_archive
    SELECT * FROM logs
    WHERE create_time < DATE_SUB(NOW(), INTERVAL archive_days DAY);
    
    SET archive_count = ROW_COUNT();
    
    -- Step 2: 分批删除原表数据（避免锁表时间过长）
    WHILE EXISTS (
        SELECT 1 FROM logs 
        WHERE create_time < DATE_SUB(NOW(), INTERVAL archive_days DAY)
        LIMIT 1
    ) DO
        DELETE FROM logs
        WHERE create_time < DATE_SUB(NOW(), INTERVAL archive_days DAY)
        LIMIT batch_size;
        
        SET delete_count = delete_count + ROW_COUNT();
        
        -- 每批次提交一次
        COMMIT;
        
        -- 简单休眠，给其他操作机会（MySQL没有SLEEP，可用DO SLEEP(1)）
        DO SLEEP(0.1);
    END WHILE;
    
    -- 记录归档日志
    INSERT INTO operation_log (
        operation_type,
        table_name,
        affected_rows,
        detail,
        create_time
    ) VALUES (
        '日志归档',
        'logs',
        archive_count,
        CONCAT('归档 ', archive_days, ' 天前的数据，共 ', archive_count, ' 条，原表已删除 ', delete_count, ' 条'),
        NOW()
    );
    
    COMMIT;
    
    SELECT CONCAT('归档完成：迁移 ', archive_count, ' 条，删除 ', delete_count, ' 条') AS 执行结果;
END //

DELIMITER ;

-- 调用：归档180天前的数据
CALL archive_logs(180);
```

- **示例：数据合规审计与删除（如：删除前归档）**

在金融或医疗等对数据追溯要求极高的行业，删除数据前必须先进行归档记录。

- 业务场景：删除某条客户记录，但必须先将该记录的完整信息存入审计日志表中。

- 实现逻辑：存储过程首先将目标记录 `INSERT` 到审计表中，然后再从主表中 `DELETE`。

```SQL
CREATE OR REPLACE PROCEDURE transfer_funds(
    from_account_id IN NUMBER, 
    to_account_id IN NUMBER, 
    amount IN NUMBER
) AS
    insufficient_funds EXCEPTION;
    balance NUMBER;
BEGIN
    -- 检查余额
    SELECT account_balance INTO balance FROM accounts WHERE account_id = from_account_id;
    
    IF balance < amount THEN
        RAISE insufficient_funds; -- 余额不足抛出异常
    ELSE
        -- 扣除转出金额
        UPDATE accounts SET account_balance = account_balance - amount WHERE account_id = from_account_id;
        -- 增加转入金额
        UPDATE accounts SET account_balance = account_balance + amount WHERE account_id = to_account_id;
    END IF;
    
    COMMIT; -- 提交事务
EXCEPTION
    WHEN insufficient_funds THEN
        DBMS_OUTPUT.PUT_LINE('Insufficient funds');
        ROLLBACK; -- 发生异常时回滚事务
END;
```

### **1\.2\.8 数据库函数**

数据库函数是用于执行特定计算和操作的代码块，它们可以接收输入参数并返回一个结果，从而简化复杂的查询、提高数据处理效率和代码的可维护性。SQL 查询中处理数据的核心工具，能帮你高效地完成数据转换、计算和分析。数据库中的函数主要分为系统内置函数和用户自定义函数（UDF）两大类。

#### 1\.2\.8\.1 聚合函数 \(Aggregate Functions\)

聚合函数面向一系列的值进行操作，通常与 `GROUP BY` 子句一起使用，用于对一组数据进行汇总计算并返回单一结果。

- AVG\(column\)：返回某列的平均值（NULL 值不包括在计算中）。

    - *示例*：计算订单表中的平均订单价格：`SELECT AVG(OrderPrice) AS OrderAverage FROM Orders;`

- SUM\(column\)：返回某列数值的总和，Null 值会被忽略 111。

    - *示例*：计算不同颜色产品的总列表价：`SELECT Color, SUM(ListPrice) FROM Production.Product GROUP BY Color;`

- \*\*COUNT\(column / \*\)\*\*：返回某列的行数（不包括 NULL 值）或返回被选中的总行数。

- MAX\(column\) / MIN\(column\)：返回某列的最高值或最低值。

|函数|功能说明|示例 \(MySQL\)|结果|
|---|---|---|---|
|COUNT\(\)|统计满足条件的行数。|`SELECT COUNT(*) FROM employees;`|员工总人数|
|SUM\(\)|计算某列的总和。|`SELECT SUM(salary) FROM employees;`|所有员工薪资总和|
|AVG\(\)|计算某列的平均值。|`SELECT AVG(salary) FROM employees;`|所有员工平均薪资|
|MAX\(\) / MIN\(\)|计算某列的最大值或最小值。|`SELECT MAX(salary), MIN(salary) FROM employees;`|最高和最低薪资|

#### 1\.2\.8\.2 字符串函数 \(String Functions\)

用于处理文本数据，包括查找、替换、截取、拼接、大小写转换等。

- CONCAT\(str1, str2\)：将多个字符串连接在一起。

- UPPER\(str\) / LOWER\(str\)：将字符串转换为大写或小写。

- LENGTH\(str\)：返回字符串的字符数。

- SUBSTRING / REPLACE：用于提取子字符串或替换字符串中的特定内容。

|函数|功能说明|示例 \(MySQL\)|结果|
|---|---|---|---|
|CONCAT\(\)|将多个字符串拼接成一个。|`SELECT CONCAT('Hello', ' ', 'World');`|`Hello World`|
|UPPER\(\) / LOWER\(\)|将字符串转换为全大写或全小写。|`SELECT UPPER('sql'), LOWER('FUN');`|`SQL`, `fun`|
|SUBSTRING\(\)|按起始位置和长度截取子字符串。|`SELECT SUBSTRING('Database', 1, 4);`|`Data`|
|TRIM\(\)|移除字符串首尾的空格或指定字符。|`SELECT TRIM(' SQL ');`|`SQL`|
|LENGTH\(\)|返回字符串的长度（在 MySQL 中按字节计）。|`SELECT LENGTH('Hello');`|`5`|

#### 1\.2\.8\.3 日期和时间函数 \(Date and Time Functions\)

用于处理日期和时间类型的数据，如格式化、计算时间差异等。

- NOW\(\) / CURDATE\(\)：返回当前的日期和时间，或仅返回当前日期。

- DATE\_FORMAT\(date, format\)：将日期格式化为指定的字符串格式。

    - *示例*：以 "YYYY\-MM\-DD" 格式显示当前日期：`SELECT FORMAT(Now(),'YYYY-MM-DD') as PerDate FROM Products;`

- DATEDIFF / DATE\_ADD：计算两个日期之间的差值，或在日期上进行加减运算。

|函数|功能说明|示例 \(MySQL\)|结果|
|---|---|---|---|
|NOW\(\)|返回当前的日期和时间。|`SELECT NOW();`|`2026-07-07 12:34:56`|
|CURDATE\(\)|返回当前的日期（不包含时间）。|`SELECT CURDATE();`|`2026-07-07`|
|YEAR\(\) / MONTH\(\) / DAY\(\)|从日期中提取年份、月份或日。|`SELECT YEAR('2026-07-07');`|`2026`|
|DATEDIFF\(\)|计算两个日期之间的天数差。|`SELECT DATEDIFF('2026-07-10', '2026-07-07');`|`3`|
|DATE\_ADD\(\)|在日期上加上一个指定的时间间隔。|`SELECT DATE_ADD('2026-07-07', INTERVAL 10 DAY);`|`2026-07-17`|

#### 1\.2\.8\.4 数学与数值函数 \(Mathematical Functions\)

用于执行各种数学运算，如取整、绝对值、四舍五入等。

- ABS\(x\)：返回数值 x 的绝对值。

- ROUND\(x, d\)：将数值 x 四舍五入到 d 位小数。

- CEILING\(x\) / FLOOR\(x\)：返回大于或等于 x 的最小整数 / 小于或等于 x 的最大整数。

|函数|功能说明|示例 \(MySQL\)|结果|
|---|---|---|---|
|ROUND\(\)|对数字进行四舍五入，可指定小数位数。|`SELECT ROUND(123.456, 2);`|`123.46`|
|CEIL\(\) / FLOOR\(\)|向上取整返回不小于参数的最小整数，或向下取整。|`SELECT CEIL(4.2), FLOOR(4.7);`|`5`, `4`|
|ABS\(\)|返回一个数的绝对值。|`SELECT ABS(-100);`|`100`|
|MOD\(\)|返回两个数相除的余数。|`SELECT MOD(10, 3);`|`1`|
|RAND\(\)|返回一个 0 到 1 之间的随机浮点数。|`SELECT RAND();`|例如 `0.5483`|

#### 1\.2\.8\.5 条件与转换函数 \(Conditional \& Conversion Functions\)

用于根据条件判断返回不同的值，或在不同数据类型之间进行转换。

- IF / CASE WHEN：条件判断函数。例如：`CASE WHEN condition1 THEN result1 WHEN condition2 THEN result2 ELSE result3 END`。

- COALESCE\(value1, value2, \.\.\.\)：返回参数列表中第一个非 NULL 的值，常用于处理空值。

- CAST / CONVERT：将一种数据类型转换为另一种数据类型（如将字符串转为数值）。

|函数|功能说明|示例 \(MySQL\)|结果|
|---|---|---|---|
|CASE WHEN|强大的多条件分支语句，用于返回不同值。|`SELECT score, CASE WHEN score >= 90 THEN 'A' WHEN score >= 80 THEN 'B' ELSE 'C' END AS grade FROM exam;`|根据分数返回等级|
|IF\(\)|简单的条件判断，类似于三元运算符。|`SELECT IF(1 > 2, 'True', 'False');`|`False`|
|IFNULL\(\)|如果第一个参数为 NULL，则返回第二个参数的值。|`SELECT IFNULL(NULL, 'default');`|`default`|

#### 1\.2\.8\.6 用户自定义函数 \(User\-Defined Functions, UDF\)

除了内置函数，用户还可以根据具体业务逻辑编写自定义函数，将其封装以便在多个查询中重复使用。

- **标量函数：**接受一个或多个参数，返回单个值。例如，定义一个根据商品成本和利润率计算最终价格的函数。

- **表值函数：**接受参数并返回一个结果集（表）。例如，定义一个根据客户 ID 查询该客户所有订单列表的函数，返回的结果可以直接像表一样被查询。

> 注：不同的数据库管理系统（如 SQL Server, MySQL, Oracle 等）提供的内置函数名称和语法可能会有所差异，在实际使用时建议查阅对应数据库的官方文档。
> 
> 

- **示例：创建一个计算员工奖金的自定义函数 **

```SQL
DELIMITER //

CREATE FUNCTION calculate_bonus(salary DECIMAL(10,2)) 
RETURNS DECIMAL(10,2)
BEGIN
    DECLARE bonus DECIMAL(10,2);
    SET bonus = salary * 0.10; -- 假设奖金是工资的10%
    RETURN bonus;
END //

DELIMITER ;
```

创建后，就可以像使用内置函数一样在查询中调用它：

```SQL
SELECT name, salary, calculate_bonus(salary) AS bonus FROM employees;
```

- **示例：身份证号提取信息 **

这个函数可以从身份证号中提取出生日期、性别和年龄，常用于用户信息校验。

```SQL
DELIMITER //

CREATE FUNCTION parse_id_card(
    id_card VARCHAR(18)  -- 支持15位和18位身份证
) 
RETURNS VARCHAR(100)
DETERMINISTIC  -- 相同输入总是返回相同结果，优化查询性能
BEGIN
    DECLARE birth_date VARCHAR(10);
    DECLARE gender VARCHAR(2);
    DECLARE age INT;
    DECLARE result VARCHAR(100);
    
    -- 校验身份证长度
    IF LENGTH(id_card) NOT IN (15, 18) THEN
        RETURN '无效身份证号';
    END IF;
    
    -- 提取出生日期（18位取第7-14位，15位取第7-12位）
    IF LENGTH(id_card) = 18 THEN
        SET birth_date = CONCAT(
            SUBSTRING(id_card, 7, 4), '-',
            SUBSTRING(id_card, 11, 2), '-',
            SUBSTRING(id_card, 13, 2)
        );
        -- 性别：第17位，奇数为男
        SET gender = IF(CAST(SUBSTRING(id_card, 17, 1) AS UNSIGNED) % 2 = 1, '男', '女');
    ELSE
        -- 15位身份证：第7-12位是年月日（YYMMDD），需要补全年份
        SET birth_date = CONCAT(
            '19', SUBSTRING(id_card, 7, 2), '-',
            SUBSTRING(id_card, 9, 2), '-',
            SUBSTRING(id_card, 11, 2)
        );
        SET gender = IF(CAST(SUBSTRING(id_card, 15, 1) AS UNSIGNED) % 2 = 1, '男', '女');
    END IF;
    
    -- 计算年龄（精确到岁）
    SET age = YEAR(CURDATE()) - YEAR(STR_TO_DATE(birth_date, '%Y-%m-%d'));
    -- 如果今年生日还没过，年龄减1
    IF DATE_FORMAT(CURDATE(), '%m-%d') < DATE_FORMAT(STR_TO_DATE(birth_date, '%Y-%m-%d'), '%m-%d') THEN
        SET age = age - 1;
    END IF;
    
    SET result = CONCAT('出生日期:', birth_date, ', 性别:', gender, ', 年龄:', age);
    RETURN result;
END //

DELIMITER ;

-- 使用示例
SELECT 
    id_card,
    parse_id_card(id_card) AS 身份信息
FROM users;
-- 结果示例：'110101199001011234' -> '出生日期:1990-01-01, 性别:男, 年龄:36'
```

- **示例：计算工作日天数 **

常用于计算请假天数、项目工期等场景，排除周末。

```SQL
DELIMITER //

CREATE FUNCTION workdays_between(
    start_date DATE,
    end_date DATE
) 
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total_days INT DEFAULT 0;
    DECLARE current_date DATE;
    DECLARE day_of_week INT;
    
    -- 如果开始日期晚于结束日期，交换
    IF start_date > end_date THEN
        SET current_date = start_date;
        SET start_date = end_date;
        SET end_date = current_date;
    END IF;
    
    SET current_date = start_date;
    
    -- 循环遍历每一天
    WHILE current_date <= end_date DO
        SET day_of_week = DAYOFWEEK(current_date); -- 1=周日, 7=周六
        -- 如果不是周六(7)或周日(1)，则计数
        IF day_of_week NOT IN (1, 7) THEN
            SET total_days = total_days + 1;
        END IF;
        SET current_date = DATE_ADD(current_date, INTERVAL 1 DAY);
    END WHILE;
    
    RETURN total_days;
END //

DELIMITER ;

-- 使用示例
SELECT 
    project_name,
    start_date,
    end_date,
    workdays_between(start_date, end_date) AS 工作日天数
FROM projects;
-- 结果：如果2026-07-01到2026-07-10，会排除两个周末共4天，返回6天
```

- **示例：生成订单编号 **

生成格式：`前缀 + 日期 + 8位随机数`，在高并发下也能保证唯一性。

```SQL
DELIMITER //

CREATE FUNCTION generate_order_no(
    prefix VARCHAR(10)
) 
RETURNS VARCHAR(30)
NOT DETERMINISTIC  -- 每次调用结果不同，不能缓存
BEGIN
    DECLARE order_no VARCHAR(30);
    DECLARE random_num VARCHAR(8);
    DECLARE retry_count INT DEFAULT 0;
    
    -- 生成8位随机数（含字母和数字）
    SET random_num = UPPER(SUBSTRING(MD5(RAND()), 1, 8));
    
    -- 组合：前缀 + 日期(YYMMDD) + 随机数
    SET order_no = CONCAT(
        prefix,
        DATE_FORMAT(NOW(), '%y%m%d'),
        random_num
    );
    
    -- 这里可以增加重试机制（实际使用时可配合唯一索引检查）
    -- 示例：如果order_no已存在，重新生成（最多重试5次）
    WHILE retry_count < 5 DO
        -- 假设有一个orders表，检查order_no是否已存在
        IF NOT EXISTS (SELECT 1 FROM orders WHERE order_no = order_no) THEN
            RETURN order_no;
        END IF;
        SET random_num = UPPER(SUBSTRING(MD5(RAND()), 1, 8));
        SET order_no = CONCAT(prefix, DATE_FORMAT(NOW(), '%y%m%d'), random_num);
        SET retry_count = retry_count + 1;
    END WHILE;
    
    -- 如果重试后仍有冲突，加上时间戳微秒确保唯一
    RETURN CONCAT(prefix, DATE_FORMAT(NOW(), '%y%m%d%H%i%s'), FLOOR(RAND()*100));
END //

DELIMITER ;

-- 使用示例
INSERT INTO orders (order_no, user_id, amount) 
VALUES (generate_order_no('ORD'), 1001, 299.00);
-- 结果示例：'ORD260707A3F5B29E'
```

**💡 实用建议**

1. 注意性能：避免在`WHERE`子句中对索引列使用函数，这可能导致索引失效，使查询变慢。例如，`WHERE YEAR(date_col) = 2026` 不如 `WHERE date_col BETWEEN '2026-01-01' AND '2026-12-31'` 高效。

2. 注意 NULL 值：大多数函数在参数为`NULL`时，结果也会是`NULL`，处理数据时要特别小心。可以使用`IFNULL`或`COALESCE`函数来处理可能的空值。

3. 数据库差异：不同数据库的函数名称和语法可能有差异（例如，SQL Server 中取子串用`SUBSTRING`，Oracle 中用`SUBSTR`）。迁移数据库时需要留意这些区别。

#### 1\.2\.8\.7 自定义函数 VS 存储过程

- **返回值与输出**

    **自定义函数：**必须返回一个值。它可以是单个标量值（如整数、字符串），也可以是一个表（表值函数）。不支持使用输出（OUTPUT）参数。

    **存储过程：**不强制要求返回值。它可以通过输出参数（OUTPUT）返回多个值，也可以返回一个或多个结果集（Recordset），或者仅返回一个状态码表示执行成功或失败。

- **调用方式与使用场景**

    **自定义函数：**可以直接嵌入到常规的 SQL 语句中，例如在 `SELECT`、`WHERE`、`JOIN` 子句或 CHECK 约束中直接调用，就像使用系统内置函数一样。

    **存储过程：**不能直接在 SQL 语句的表达式中调用。必须通过特定的执行语句（如 `EXEC` 或 `CALL`）来独立执行。

- **副作用与数据修改**

    **自定义函数：**不能有任何副作用。这意味着函数内部不能修改数据库的外部状态，例如不能执行 `INSERT`、`UPDATE`、`DELETE` 操作来修改数据库表，也不能发送邮件等。

    **存储过程：**没有副作用限制。它可以执行复杂的数据库操作，包括对数据库表进行增删改查，以及控制事务（如提交或回滚）。

- **性能与执行计划**

    **自定义函数：**在查询中使用时，通常只能在单线程上串行执行，这会阻止并行查询处理。如果在 `WHERE` 子句中对大型表使用标量函数，会导致性能显著下降，因为函数会对每一行都执行一次。

    **存储过程：**在首次执行时会进行编译并缓存执行计划，后续调用可直接复用，减少了重复编译的开销，在处理复杂逻辑和大量数据操作时性能通常更好。

    |    对比维度|    自定义函数 \(UDF\)|    存储过程 \(Stored Procedure\)|
    |---|---|---|
    |    核心目的|    计算并返回一个值，用于增强 SQL 的表达能力。|    执行一个完整的业务操作，可能包含复杂的流程和事务。|
    |    返回值|    必须返回，且只能是单一值（标量）或结果集（表值函数）。|    不必须返回，但可以通过`OUT`参数或结果集返回多个值。|
    |    调用方式|    像内置函数一样，嵌入在 SQL 语句中使用，如 `SELECT func()`。|    使用 `CALL` 语句独立执行，不能直接在`SELECT`等语句中调用。|
    |    事务处理|    不支持。函数内的操作是原子的，不能包含开启、提交或回滚事务的语句。|    支持。可以在内部开启事务，进行复杂的 ACID 操作。|
    |    副作用|    无副作用。原则上是“只读”的，不应修改数据库中的表数据（部分数据库严格禁止）。|    允许有副作用。可以修改表数据、执行 DDL 语句等，是数据库变更的主力。|

    ---

**📜 语法对比实例**

通过一个简单的“根据用户 ID 更新并返回新余额”的例子，能更直观地看到语法差异：

- **自定义函数 \(以 MySQL 为例\)**

```SQL
-- 函数职责单一：只负责计算，不能修改数据
DELIMITER //
CREATE FUNCTION get_discount(price DECIMAL(10,2)) 
RETURNS DECIMAL(10,2)  -- 明确声明返回类型
BEGIN
    DECLARE discount_price DECIMAL(10,2);
    -- 只能进行读操作和计算，不能有 INSERT/UPDATE/DELETE
    SET discount_price = price * 0.9; 
    RETURN discount_price; -- 必须返回
END //
DELIMITER ;

-- 调用：嵌入在SQL中
SELECT order_id, get_discount(amount) FROM orders;
```

- **自定义函数 \(以 PostgreSQL 为例\)**

```SQL
CREATE OR REPLACE FUNCTION del_report_commodity(
    IN p_province_id VARCHAR(10),      -- 输入：省份ID
    OUT p_deleted_count INTEGER        -- 输出：删除的行数
) AS $$
BEGIN
    DELETE FROM pcc_prov_report_commodity 
    WHERE report_province = p_province_id
      AND report_province IS NOT NULL
      AND p_province_id != '';

    -- 将受影响的行数赋值给 OUT 参数
    GET DIAGNOSTICS p_deleted_count = ROW_COUNT;
END;
$$ LANGUAGE plpgsql;
```

- **存储过程 \(以 MySQL 为例\)**

```SQL
-- 过程职责完整：处理更新余额的整个业务流程
DELIMITER //
CREATE PROCEDURE update_balance(IN user_id INT, IN amount DECIMAL(10,2), OUT new_balance DECIMAL(10,2))
BEGIN
    -- 支持复杂逻辑
    START TRANSACTION;
    UPDATE accounts SET balance = balance - amount WHERE id = user_id;
    -- 可以执行修改操作
    INSERT INTO transaction_log(user_id, amount) VALUES (user_id, amount);
    COMMIT;
    
    -- 通过OUT参数返回，也可以直接SELECT结果集
    SELECT balance INTO new_balance FROM accounts WHERE id = user_id;
END //
DELIMITER ;

-- 调用：独立执行，不能用在SELECT里
CALL update_balance(1, 100, @balance);
SELECT @balance; -- 查看OUT参数返回的值
```

- **存储过程 \(以 PostgreSQL 为例\)**

```SQL
CREATE OR REPLACE PROCEDURE del_report_commodity(
    IN province_id VARCHAR(10)
)
LANGUAGE plpgsql  -- 指定使用 PL/pgSQL 语言
AS $$
BEGIN
    DELETE FROM pcc_prov_report_commodity 
    WHERE report_province = province_id
      AND province_id IS NOT NULL;
END;
$$;
```

---

**🎯 实战选择建议**

在实际开发中，你可以按这个思路来做决定：

1. 优先考虑函数：如果你只是需要进行数据转换、计算或格式化（如把金额转为大写、计算年龄），且不修改数据，请使用函数。它能更好地复用，让 SQL 更简洁。

2. 必须使用存储过程：当你的业务逻辑涉及多个步骤、需要事务管理、或要执行数据变更（增删改）时，必须使用存储过程。它是处理复杂数据库操作的标准方式。

3. 性能考量：有些观点认为存储过程性能更好，因为它编译后存储在服务器端。但在现代数据库中，查询优化器对函数的处理已经非常出色，性能差距已不明显。网络传输开销有时才是更大的影响因素，存储过程能减少客户端与服务器的交互次数。

4. 现代架构趋势：在微服务和云原生架构中，业务逻辑越来越倾向于在应用层（如 Java、Go）实现，这使得数据库更专注于数据存储。因此，存储过程的使用在减少，而简单的函数仍广泛用于查询中的数据处理。

---

**⚠️ 常见误区提醒**

- **误区 1：函数能做的事情，存储过程都能做，所以函数没用。**

    - 正解：函数最大的价值在于无法被存储过程替代，那就是在 SQL 查询语句内部使用。你不能在`WHERE`或`SELECT`子句中调用一个存储过程，这赋予了函数独特的地位。

- **误区 2：存储过程比函数更安全，因为可以控制事务。**

    - 正解：安全性取决于权限控制，而非类型。你可以对函数授予`EXECUTE`权限，对存储过程授予`EXECUTE`权限。关键在于最小权限原则——只授予完成任务所需的最小权限。

> 总结成一句话：需要计算出一个结果、并且可以在 SQL 中随时调用，就用函数；需要协调多个操作、管理事务流程，就用存储过程。
> 
> 

---

**💡 总结建议**

- 函数可以生成单个测试值（如随机姓名、随机日期），但不能直接造数据

- 存储过程是更好的造数据工具，支持循环、事务和批量操作

- 真正的推荐：用 Python/Java 代码 \+ Faker 库来生成，灵活性最高，数据最真实

### **1\.2\.9 修改 json 数据**

json\_set（MySQL 风格）和 jsonb\_set（PostgreSQL 风格）都是用于局部更新 JSON 文档中指定路径键值的强大函数。它们的核心作用是只修改目标路径，保留其余结构，避免全量覆盖带来的风险。

#### 1\.2\.9\.1 json\_set

`json_set` 支持同时更新多个路径，且默认会自动创建缺失的中间层级。

```SQL
JSON_SET(json_doc, path, val[, path, val] ...)
```

**示例：更新单个键值**

将 `users` 表中 `id=1` 的 `info` 字段里的 `name` 更新为 `"n11"`。如果该路径不存在，会自动创建。

```SQL
UPDATE users 
SET info = JSON_SET(info, '$.name', 'n11') 
WHERE id = 1;
```

**示例：同时更新多个键值**

可以一次性传入多组路径和值：

```SQL
UPDATE users 
SET info = JSON_SET(info, '$.name', 'n11', '$.age', 30) 
WHERE id = 1;
```

**示例：更新多层嵌套的键值**

```SQL
-- json结构示例
{
  "user": {
    "profile": {
      "name": "张三",
      "age": 25
    }
  }
}

-- 将 $.user.profile.name 修改为 "李四"
UPDATE users 
SET data = JSON_SET(data, '$.user.profile.name', '李四') 
WHERE id = 1;

-- 在 $.user.profile 下新增 email 字段（如果 profile 层级不存在，会自动创建）：
UPDATE users 
SET data = JSON_SET(data, '$.user.profile.email', 'lisi@example.com') 
WHERE id = 1;

-- 同时修改第一层的 status 和第三层的 $.user.profile.age：
UPDATE users 
SET data = JSON_SET(
    data, 
    '$.status', 'active', 
    '$.user.profile.age', 26
) 
WHERE id = 1;
```

#### 1\.2\.9\.2 jsonb\_set

`jsonb_set` 每次只能更新一个路径，且对数据类型的要求非常严格。

```SQL
jsonb_set(target_jsonb, path_text[], new_value_jsonb, create_missing_boolean)
```

**示例：更新单个键值**

将 `users` 表中 `id=123` 的 `data` 字段里嵌套的 `settings.theme` 更新为 `"dark"`：

```SQL
UPDATE users
SET data = jsonb_set(
    data, 
    '{settings,theme}',      -- 1. 路径必须是 text[] 数组格式
    '"dark"'::jsonb,         -- 2. 新值必须是 jsonb 类型（字符串需双引号）
    true                     -- 3. 显式设为 true 才会自动创建缺失的父级路径
)
WHERE id = 123;
```

**示例：同时更新同一嵌套层级下的多个键**

由于 `jsonb_set` 只能处理单路径，批量更新嵌套对象时，更优雅的做法是提取子对象并用 `||` 合并：

```SQL
UPDATE users
SET data = jsonb_set(
    data,
    '{profile}',
    (data -> 'profile') || '{"first_name":"Alex","last_name":"Brown"}'::jsonb,
    true
)
WHERE id = 456;
```

**示例：更新多层嵌套的键值**

```SQL
-- json结构示例
{
  "user": {
    "profile": {
      "name": "张三",
      "age": 25
    }
  }
}

-- 将 {user,profile,name} 修改为 "李四"
UPDATE users
SET data = jsonb_set(
    data, 
    '{user,profile,name}',   -- 多层路径用逗号分隔
    '"李四"'::jsonb,         -- 字符串必须加双引号并转为 jsonb
    true                     -- 允许自动创建缺失的中间层级
)
WHERE id = 1;

-- 在 {user,profile} 下新增 email
UPDATE users
SET data = jsonb_set(
    data, 
    '{user,profile,email}', 
    '"lisi@example.com"'::jsonb, 
    true
)
WHERE id = 1;

-- 由于 jsonb_set 每次只能处理一个路径，如果要同时修改不同层级的键值，需要嵌套调用
UPDATE users
SET data = jsonb_set(
    jsonb_set(
        data, 
        '{status}', 
        '"active"'::jsonb, 
        true
    ), 
    '{user,profile,age}', 
    '26'::jsonb,             -- 注意：数字类型不需要加双引号，直接转 jsonb
    true
)
WHERE id = 1;

-- 如果第一层是数组，数组的索引（从0开始）直接作为路径数组中的一个元素
UPDATE users
SET data = jsonb_set(
    data, 
    '{users,0,profile,name}',  -- 0 代表数组的第一个元素
    '"王五"'::jsonb, 
    true
)
WHERE id = 1;
```

### **1\.2\.10 提取 json 数据**

在 PostgreSQL 中，`json` 和 `jsonb` 类型在查询时使用的提取操作符（如 `->` 和 `->>`）是通用的。但 `jsonb` 额外提供了强大的包含检查（`@>`）和键存在检查（`?`）等操作符，且支持 GIN 索引，性能更优。

**json 字段示例**

```SQL
-- json结构
{
  "name": "Smart Watch",
  "brand": "Apple",
  "price": 250,
  "colors": ["red", "black"],
  "specs": {
    "memory": "16GB",
    "resolution": "1080p"
  }
}
```

**方式 1：****`->`**** 操作符（返回带引号的字符串）**

```SQL
SELECT details->'$.specs.memory' FROM products;
-- 结果: "16GB"
```

**方式 2：****`->>`**** 操作符（返回去引号的纯文本，推荐）**

```SQL
SELECT details->>'$.specs.memory' FROM products;
-- 结果: 16GB
```

**方式 3：****`JSON_EXTRACT()`**** 函数**

```SQL
SELECT JSON_EXTRACT(details, '$.specs.memory') FROM products;
-- 结果: "16GB"

-- 去引号
SELECT JSON_UNQUOTE(JSON_EXTRACT(details, '$.specs.memory')) FROM products;
-- 结果: 16GB
```

**其他示例**

```SQL
-- json结构
{
  "name": "Smart Watch",
  "brand": "Apple",
  "price": 250,
  "colors": ["red", "black"],
  "specs": {
    "memory": "16GB",
    "resolution": "1080p"
  }
}

-- 提取品牌，返回文本 'Apple'
SELECT details->>'brand' AS brand FROM products;

-- 提取内存大小，返回文本 '16GB'
SELECT details->'specs'->>'memory' AS memory FROM products;
SELECT details->>'$.specs.memory' FROM products;  -- mysql

-- 按顶层属性值筛选
SELECT * FROM products WHERE details->>'brand' = 'Apple';

-- 按嵌套属性值筛选
SELECT * FROM products WHERE details#>>'{specs, memory}' = '16GB';

-- 使用 IN 运算符
SELECT * FROM products WHERE details->>'brand' IN ('Apple', 'Samsung');

-- 筛选出包含特定键值对的记录
SELECT * FROM products WHERE details @> '{"brand": "Apple"}';

-- 筛选出颜色数组中包含 'red' 的记录
SELECT * FROM products WHERE details->'colors' @> '["red"]';

-- 筛选出包含 'specs' 属性的记录
SELECT * FROM products WHERE details ? 'specs';
```

## 1\.3 数据库索引

**索引（Index）**是数据库中用于加速数据检索的一种数据结构。你可以把它想象成书籍的“目录”或者图书馆的“检索卡片”。

如果没有索引，数据库在查找数据时只能从头到尾逐行扫描（全表扫描）；有了索引，数据库就能像查字典一样，通过特定的算法（如 B\+ 树、哈希表等）快速定位到数据所在的物理位置，从而极大地减少查询时间。

### **1\.3\.1 索引结构**

- **MySQL**

```SQL
-- 查看某张表的所有索引
SHOW INDEX FROM 表名;

-- 或者使用 INFORMATION_SCHEMA 查询更详细的信息
SELECT * FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = '你的数据库名' AND TABLE_NAME = '表名';
```

- **PostgreSQL**

```SQL
-- 查看某张表的所有索引
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = '表名';

-- 查看索引的详细列信息
SELECT * FROM pg_index WHERE indrelid = '表名'::regclass;
```

- **Oracle**

```SQL
-- 查看某张表的所有索引
SELECT index_name, index_type, uniqueness 
FROM user_indexes 
WHERE table_name = '表名';

-- 查看索引包含的列
SELECT index_name, column_name, column_position 
FROM user_ind_columns 
WHERE table_name = '表名' 
ORDER BY index_name, column_position;
```

- **SQL Server**

```SQL
-- 查看某张表的所有索引
EXEC sp_helpindex '表名';

-- 或者使用系统视图
SELECT i.name AS index_name, i.type_desc, c.name AS column_name, ic.key_ordinal
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('表名')
ORDER BY i.name, ic.key_ordinal;
```

---

### **1\.3\.2 索引的核心目的**

1. **大幅提升查询速度（最核心作用）**

这是索引存在的最大意义。对于包含百万甚至上千万条数据的表，全表扫描可能需要几秒甚至几分钟，而通过合适的索引，查询时间可以缩短到几十毫秒。这也是解决我们刚才提到的“慢查询”最有效的手段之一。

2. **加速排序和分组操作**

当 SQL 语句中包含 **ORDER BY（排序）**或 **GROUP BY（分组）**时，如果排序或分组的字段上建有索引，数据库可以直接利用索引的有序性来获取结果，从而避免在内存或磁盘中进行代价高昂的排序操作。

3. **保证数据的唯一性**

通过创建“唯一索引”（Unique Index），数据库可以强制要求某列或某几列的值不能重复，从而在底层保证数据的完整性。

4. **加速表与表之间的连接（JOIN）**

在多表关联查询时，如果连接字段上建有索引，数据库可以更快地匹配到对应的数据行，显著提升 JOIN 操作的效率。

---

### 1\.3\.3 **索引失效场景及优化**

1. **违反最左前缀原则**

对于联合索引（复合索引），如果查询条件没有从索引的最左边列开始匹配，或者跳过了中间的列，索引将无法被有效利用。

2. **对索引列进行函数或运算操作**

如果在查询条件中对索引列使用了内部函数（如 `UPPER()`、`DATE()`、`SUBSTRING()` 等），或者参与了数学运算（如 `+`、`-`、`*`、`/`），数据库需要逐行计算，导致索引失效。

3. **数据类型不匹配（隐式类型转换）**

当查询条件中传入的值的数据类型与索引列的数据类型不一致时，数据库会进行隐式类型转换。例如，索引列是 `VARCHAR` 类型，但查询时传入了数字，这会导致索引失效。

4. **模糊查询（LIKE）使用不当**

正如我们之前讨论的，如果 `LIKE` 操作的通配符 `%` 出现在字符串的开头（如 `LIKE '%关键词'` 或 `LIKE '%关键词%'`），会破坏索引的有序性，导致索引失效。

5. **索引列的数据选择性过低（数据分布不均）**

如果索引列中包含大量重复值（例如“性别”字段只有“男”和“女”），数据库优化器会认为通过索引查找的成本高于全表扫描，从而主动放弃使用索引。

6. **使用了特定的逻辑操作符**

- OR 条件：如果 `OR` 连接的条件中，有任何一个字段没有索引，通常会导致整个查询放弃索引，进行全表扫描。

- 不等于操作符：使用 `!=` 或 `<>` 时，索引也可能失效。

7. **对索引列进行 NULL 值判断**

如果查询条件是对索引列进行 `IS NULL` 的判断，由于部分数据库索引不存储空值，这会导致索引失效（但 `IS NOT NULL` 通常可以走索引）。

8. **索引本身的设计或维护问题**

- 过度索引：表上创建了过多的索引，会增加写操作（INSERT/UPDATE/DELETE）的开销和维护成本，查询优化器也可能因此选择错误的执行计划。

- 索引碎片化：频繁的增删改操作会导致索引页物理分布不连续，产生碎片，降低查询效率，此时需要定期重建索引。

- 统计信息不准确：数据库依赖统计信息来制定执行计划，如果统计信息过时，可能会导致优化器做出错误判断，放弃使用索引。

|失效场景|典型错误示例|失效原因|✅ 优化方案|
|---|---|---|---|
|1\. 违反最左前缀法则|联合索引 `(a,b,c)`<br>❌ `WHERE b=1 AND c=2`|跳过了索引树的最左节点 `a`，无法定位 B\+ 树分支|查询条件必须从最左列开始连续匹配；或调整联合索引顺序以匹配高频查询|
|2\. 索引列上使用函数/计算|❌ `WHERE YEAR(create_time)=2024`<br>❌ `WHERE id+1=5`|对列进行运算后，破坏了索引的有序性，导致全表扫描|将计算移到等号右侧：<br>`WHERE create_time >= '2024-01-01' AND ...`<br>`WHERE id = 4`|
|3\. 隐式类型转换|字段 `phone` 为 VARCHAR<br>❌ `WHERE phone=13800000000`|字符串与数字比较时，MySQL 会对字符串列做隐式转换，等同于加了函数|保持类型一致：<br>`WHERE phone='13800000000'`|
|4\. LIKE 以通配符开头|❌ `WHERE name LIKE '%张'`<br>❌ `WHERE name LIKE '%张%'`|前缀不确定，无法利用 B\+ 树的排序特性进行范围查找|改为右模糊：`LIKE '张%'`<br>若必须全模糊，使用 全文索引\(FULLTEXT\) 或 ES|
|5\. OR / \!= / \<\> / NOT IN|❌ `WHERE a=1 OR b=2`<br>❌ `WHERE status != 0`|优化器评估后认为全表扫描成本更低，放弃索引|① OR 改写为 UNION ALL<br>② \!= 改为正向枚举 `IN (1,2,3)`<br>③ 确保区分度高的条件走索引|
|6\. IS NULL / IS NOT NULL|❌ `WHERE deleted_at IS NULL`|当 NULL 值占比过高时，优化器可能放弃索引|设置默认值\(如0\)代替NULL；或使用覆盖索引减少回表|
|7\. 字符集不匹配|关联表 A\(utf8\) JOIN B\(utf8mb4\)<br>❌ `ON A.col = B.col`|连接字段字符集不同，被驱动表会发生隐式转换|统一关联字段的字符集和排序规则\(Collation\)|
|8\. SELECT \* 导致回表过多|❌ `SELECT * FROM t WHERE a=1`|虽然走了索引，但需大量回表查非索引列，IO成本超过阈值时退化为全扫|使用覆盖索引：只 SELECT 索引中包含的字段|
|9\. ORDER BY / GROUP BY 未命中索引|❌ `ORDER BY b` \(仅有索引a\)|无法利用索引的天然有序性，产生 Filesort|让排序/分组字段包含在联合索引中，且遵循最左前缀|
|10\. 索引区分度过低|❌ `WHERE gender='男'` \(男女各50%\)|扫描行数接近全表，优化器主动放弃索引|该字段不适合单独建索引；应放入联合索引的非前导列位置|

---

### **1\.3\.4 索引的“双刃剑”效应**

索引不是越多越好！

- 每个索引都有写入成本（INSERT/UPDATE/DELETE 变慢）和空间成本

- 单表索引数量建议控制在 5\-6 个以内

- 优先使用联合索引替代多个单列索引（一个联合索引可覆盖多种查询模式）

- 定期审查并删除冗余索引和从未使用的索引

使用时需要注意它的代价：

- **占用存储空间**：索引本身需要占用额外的磁盘空间。

- **降低写入性能**：每次对表进行 INSERT、UPDATE 或 DELETE 操作时，数据库不仅要修改数据，还要同步更新相关的索引。如果索引建得太多，写入操作的开销会非常大。

> ***因此，在实际开发中，通常建议在经常作为查询条件、排序字段或连接字段的列上建立索引，并定期清理无用索引。***
> 
> 

## 1\.4 常见问题

### **1\.4\.1 虚拟字段**

JSON 字段创建索引（提升查询性能）

### **1\.4\.2 视图（View）**

### **1\.4\.3 数据库读写**

- SSD 的读取速度通常显著高于写入，原因：

|原因|说明|
|---|---|
|闪存物理特性|NAND 闪存读取只需检测电荷状态，写入需要改变电荷（编程），擦除需要清空整个块|
|擦除\-写入不对称|SSD 写入前若块已有数据，需先擦除（Erase）再写入，读取不需要|
|垃圾回收（GC）|写入会触发后台 GC，搬运有效数据、回收无效块，占用资源|
|写入放大（WA）|实际写入物理介质的数据量 \> 应用请求写入量|
|SLC Cache 耗尽|大量持续写入时，高速缓存区用完，落入低速 TLC/QLC 直写|

> **读取可以走缓存**
> 
> 

- 热点数据在 Buffer Pool（InnoDB）或 Page Cache（OS）中，内存读取纳秒级

- 写入最终必须落盘保证持久性，绕不开磁盘

> **写入的额外开销**
> 
> 

一次数据库写入实际包含：

```Plain Text
写 WAL/Redo Log（保证崩溃恢复）
→ 写数据页（内存中修改，标记为脏页）
→ 更新索引（B+树可能分裂、页重组）
→ 刷脏页到磁盘（Checkpoint）
→ 可能触发 Binlog 同步（主从复制）
→ 事务提交（fsync 磁盘）
```

而一次读取通常是：

```Plain Text
查缓存 → 命中则返回（纳秒级）
未命中 → 读磁盘页 → 返回（毫秒级）
```

> **锁与并发控制**
> 
> 

- 写入需要加锁（行锁、间隙锁）、维护 MVCC 版本链

- 读取在快照读下可以无锁，并发度更高

---

## 相关笔记
- [[08-环境搭建]]
- [[MongoDB操作指南]]
- [[Nginx配置详解]]

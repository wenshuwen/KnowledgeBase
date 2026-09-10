---
type: note
tags: [数据库] [ClickHouse] [OLAP]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# ClickHouse 使用指南

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 中间件章-Clickhouse 小节

## ClickHouse 简介

ClickHouse 是由俄罗斯 Yandex 公司于 2016 年开源的列式 OLAP 数据库管理系统，使用 C\+\+ 编写。它专为大规模数据分析设计，能够在数十亿行数据上实现亚秒级查询响应，是当前最流行的高性能分析型数据库之一。

---

## 安装部署指南

### 方式一：快速安装（推荐体验/开发环境）

官方提供了一键安装脚本，自动适配操作系统：

```Bash
*# 下载并安装 ClickHouse 可执行文件*
curl https://clickhouse.com/ | sh

*# 启动本地模式（临时数据，无需配置）*
./clickhouse local

*# 启动持久化服务端*
./clickhouse server

*# 新开终端，启动客户端连接*
./clickhouse client
```

### 方式二：Docker 安装（推荐快速体验）

```Bash
docker pull clickhouse/clickhouse-server
docker run -d --name clickhouse-server \
  -p 8123:8123 -p 9000:9000 \
  clickhouse/clickhouse-server
```

### 方式三：Linux 生产环境安装（以 Ubuntu/Debian 为例）

```Bash
sudo apt-get install -y apt-transport-https ca-certificates dirmngr
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 8919F6BD
echo "deb https://repo.clickhouse.com/deb/stable main/" | sudo tee /etc/apt/sources.list.d/clickhouse.list
sudo apt-get update
sudo apt-get install -y clickhouse-server clickhouse-client
```

### 方式四：RPM 离线安装（CentOS/RHEL）

环境准备：

1. 调整文件描述符限制（编辑 `/etc/security/limits.conf`）：

```Bash
* soft nofile 65536
* hard nofile 65536
* soft nproc 131072
* hard nproc 131072
```

2. 安装依赖：

```Bash
sudo yum install -y libtool unixODBC
```

3. 下载并安装 RPM 包（4 个核心包）：

```Bash
sudo rpm -ivh clickhouse-common-static-*.rpm \
             clickhouse-server-*.rpm \
             clickhouse-client-*.rpm \
             clickhouse-compressor-*.rpm
```

4. 修改配置（`/etc/clickhouse-server/config.xml`），允许远程访问：

```Bash
<listen_host>::</listen_host>
```

5. 启动服务：

```Bash
sudo systemctl start clickhouse-server
sudo systemctl status clickhouse-server
```

6. 连接测试：

```Bash
clickhouse-client -m
*# 执行测试查询*
SELECT 1;
```

> ⚠️ 生产环境注意事项：默认端口为 TCP `9000`、HTTP `8123`，需确保防火墙放行；数据目录默认在 `/var/lib/clickhouse/`，建议挂载大容量磁盘。
> 
> 

---

## 核心功能与特性

### 列式存储与高效压缩

数据按列独立存储，相同类型的数据连续存放，天然适合高效压缩。支持 LZ4、ZSTD、Delta、Gorilla 等多种压缩算法，压缩比通常可达 5\~10 倍，大幅降低 I/O 开销和存储成本。

### 向量化执行引擎

利用 CPU SIMD 指令集（如 SSE4\.2），以数据块（Block）为单位并行处理，充分利用多核 CPU 和缓存，实现极高的计算效率。

### 丰富的表引擎体系

以 MergeTree 系列为核心：

|引擎|用途|
|---|---|
|MergeTree|通用分析场景，支持分区、排序键、索引|
|ReplacingMergeTree|自动去重|
|SummingMergeTree|预聚合求和|
|AggregatingMergeTree|复杂预聚合|
|CollapsingMergeTree|行级变更（增删改模拟）|
|ReplicatedMergeTree|数据副本同步|
|Distributed|跨节点分布式查询|
|Kafka|从 Kafka 消费数据|

### 分布式架构

支持数据分片（Sharding）\+ 副本（Replication），采用 Multi\-Master 多主架构，节点角色对等，支持线性扩展和高可用。

### 索引机制

- 稀疏索引：按主键物理排序，索引体积小，可常驻内存

- 数据跳过索引：minmax、set、bloom\_filter 等，在数据块级别过滤无关数据

### 实时数据写入

支持高吞吐批量写入（单节点每秒百万级），写入时不加锁，后台异步 Merge 整理数据。

### SQL 与高级功能

- 兼容 ANSI SQL，支持 GROUP BY、ORDER BY、JOIN、窗口函数、子查询

- 内置近似计算函数（`uniqCombined`、`quantileTDigest`）

- 支持 `SAMPLE` 采样查询、`PREWHERE` 列裁剪优化

- 支持 TTL 自动过期删除、物化视图预计算

---

## 常用操作命令

### 连接命令

```Bash
*# 交互式连接（本地默认）*
clickhouse-client

*# 指定数据库*
clickhouse-client --host=192.168.1.100 --port=9000 --user=default --password=your_password --database=mydb

*# 启用 TLS 加密连接（生产环境推荐）*
clickhouse-client --host=192.168.1.100 --port=9440 --user=default --password=your_password --secure

*# 指定主机、端口、用户连接*
clickhouse-client --host=192.168.1.100 --port=9000 --user=default --password=xxx

*# 非交互式执行 SQL*
clickhouse-client --query="SELECT count() FROM system.tables"

*# 非交互式执行 SQL 脚本文件*
clickhouse-client --host=192.168.1.100 --port=9000 --user=default --password=xxx --database="default" --multiquery < /opt/aspire/product/pcc/clickhouse.sql

*# HTTP 接口查询*
echo "SELECT 1" | curl 'http://localhost:8123/' --data-binary @-

*# MySQL 协议连接（需 20.8+）*
mysql -h 127.0.0.1 -P 9004 -u default -p
```

---

|参数|说明|
|---|---|
|\-\-host|服务器地址|
|\-\-port|TCP 端口（默认 9000）|
|\-\-user|用户名（默认 default）|
|\-\-password|密码|
|\-\-database|指定默认数据库|
|\-\-multiquery|允许执行多条 SQL（非交互模式）|
|\-\-file|指定要执行的 SQL 文件路径|
|\-\-secure|启用 TLS 加密连接|
|\-\-format|指定输出格式（如 JSONEachRow、CSV）|
|\-\-time|显示查询执行耗时|

> **连接方式**
> 
> 

- 命令行：`clickhouse-client -h ``localhost`` -u default`

- HTTP 接口：`curl -X POST "``http://localhost:8123/?query=SELECT+1``"`

- JDBC/ODBC：通过标准驱动连接

- Grafana：安装 Altinity ClickHouse 数据源插件

---

> 💡 提示：生产环境中建议始终使用 `--secure` 启用加密连接，避免密码在命令行中明文暴露（可省略 `--password` 参数，系统会提示交互式输入）。
> 
> 

### 数据库与表操作

```SQL
*-- 创建数据库*
CREATE DATABASE IF NOT EXISTS analytics;

*-- 创建 MergeTree 表*
CREATE TABLE analytics.events (
    event_date  Date,
    event_time  DateTime,
    user_id     UInt64,
    event_type  String,
    page_url    String,
    device      String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_type, user_id)
TTL event_date + INTERVAL 90 DAY;

*-- 集群模式建表（所有节点同步执行）*
CREATE TABLE analytics.events ON CLUSTER my_cluster (...) ENGINE = MergeTree() ...;

*-- 插入数据*
INSERT INTO analytics.events VALUES
('2026-09-04', '2026-09-04 10:00:00', 1001, 'click', '/home', 'iOS');

*-- 查看表结构*
DESCRIBE analytics.events;

*-- 查看磁盘占用*
SELECT table, formatReadableSize(sum(bytes)) AS size
FROM system.parts WHERE active GROUP BY table;
```

### 查询命令

```SQL
*-- 聚合查询*
SELECT event_type, count() AS cnt, uniqExact(user_id) AS uv
FROM analytics.events
WHERE event_date >= '2026-09-01'
GROUP BY event_type
ORDER BY cnt DESC;

*-- 采样查询（约 10% 数据）*
SELECT * FROM analytics.events SAMPLE 0.1 LIMIT 100;

*-- PREWHERE 优化*
SELECT user_id, event_type
FROM analytics.events
PREWHERE event_type = 'click'
WHERE event_date = '2026-09-04';

*-- 远程查询*
SELECT * FROM remote('192.168.1.100', analytics, events) LIMIT 10;
```

### 维护命令

```SQL
*-- 手动触发合并*
OPTIMIZE TABLE analytics.events FINAL;

*-- 异步删除（mutation）*
ALTER TABLE analytics.events DELETE WHERE event_date < '2026-01-01';

*-- 异步更新*
ALTER TABLE analytics.events UPDATE device = 'Android' WHERE user_id = 1001;

*-- 设置查询内存上限*
SET max_memory_usage = 20000000000;  *-- 20GB*
```

---

## 实际应用场景示例

### 场景一：用户行为分析

构建用户事件大宽表，支持漏斗转化、留存分析、路径分析、用户分群等，亚秒级响应。

```SQL
*-- 漏斗分析示例：浏览→加购→下单→支付*
SELECT
    countIf(event_type = 'view')   AS step1_view,
    countIf(event_type = 'cart')   AS step2_cart,
    countIf(event_type = 'order')  AS step3_order,
    countIf(event_type = 'pay')    AS step4_pay
FROM analytics.events
WHERE event_date = '2026-09-04';
```

> 📌 典型案例：字节跳动使用 ClickHouse 处理 PB 级用户行为数据；B站基于预聚合模型实现流量与路径分析。
> 
> 

### 场景二：实时日志分析

替代 ELK 栈中的 Elasticsearch，处理海量日志数据，支持网络监控、APM 异常分析、安全审计。

```SQL
*-- 创建日志表*
CREATE TABLE logs.app_log (
    timestamp  DateTime,
    level      LowCardinality(String),
    service    LowCardinality(String),
    message    String,
    trace_id   String
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (service, timestamp);

*-- 查询最近 5 分钟的错误日志*
SELECT service, count() AS error_count
FROM logs.app_log
WHERE level = 'ERROR' AND timestamp > now() - INTERVAL 5 MINUTE
GROUP BY service;
```

> 📌 典型案例：Cloudflare 每秒处理 600 万\+ DNS 日志；Anthropic 和 OpenAI 均使用 ClickHouse 构建 AI 推理日志的可观测性平台。
> 
> 

### 场景三：实时 BI 报表与大屏

结合 Grafana、Superset 等 BI 工具，构建实时运营监控看板，分析订单、收入、GMV 等核心指标。

```SQL
*-- 实时 GMV 统计*
SELECT
    toStartOfHour(event_time) AS hour,
    sum(amount) AS gmv,
    uniqExact(user_id) AS buyer_count
FROM orders
WHERE event_date = today()
GROUP BY hour
ORDER BY hour;
```

### 场景四：IoT 时序数据

传感器数据的存储与分析，支持按时间范围高效查询和聚合。

```SQL
CREATE TABLE iot.sensor_data (
    device_id   String,
    timestamp   DateTime,
    temperature Float32,
    humidity    Float32,
    pressure    Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (device_id, timestamp);

*-- 查询某设备过去 1 小时的平均温度*
SELECT device_id, avg(temperature) AS avg_temp
FROM iot.sensor_data
WHERE timestamp > now() - INTERVAL 1 HOUR
GROUP BY device_id;
```

### 场景五：广告营销与用户画像

支持实时精准营销、人群圈选、广告投放效果评估（点击率、转化率、归因分析）。

---

## 适用与不适用场景总结

|✅ 适合|❌ 不适合|
|---|---|
|大规模 OLAP 分析查询|高并发 OLTP 事务处理|
|实时写入 \+ 实时查询|频繁 UPDATE/DELETE|
|日志/事件流分析|多表复杂 JOIN 查询|
|时序数据监控|强一致性要求场景|
|BI 报表与数据大屏|高频单行点查|
|用户画像与标签系统|小数据量简单查询|

---

> 💡 总结：ClickHouse 的核心优势在于"快"和"大"——对海量数据的聚合分析查询性能远超传统数据仓库，同时支持实时写入，非常适合需要低延迟、高吞吐的分析型场景。如果你的业务以追加写入为主、读多写少、数据量大，ClickHouse 是一个非常值得考虑的选择。
> 
> 

---

---

## 相关笔记
- [[08-环境搭建]]
- [[ElasticSearch使用指南]]
- [[PostgreSQL性能调优]]

---
type: note
tags: [数据库] [ElasticSearch] [检索]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# ElasticSearch 使用指南

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 中间件章-ElasticSearch 小节

## 什么是 Elasticsearch

Elasticsearch 是一个基于 Apache Lucene 构建的开源、分布式、RESTful 搜索与分析引擎。它能够近乎实时地存储、搜索和分析海量数据，数据以 JSON 文档形式存储，所有操作通过 HTTP REST 接口完成。

---

## 安装部署指南

### 安装方式选择

|场景|推荐方式|
|---|---|
|生产环境（Linux）|官方 tar\.gz / RPM / DEB 包|
|本地开发|Docker|
|快速测试|Docker / macOS Homebrew|

### Linux 安装（生产推荐）

1. 环境准备

- Java 17\+（Elasticsearch 8\.x 自带 JDK，无需额外安装）

- 创建非 root 用户运行

- 内存建议 ≥ 2GB

```Bash
*# 创建专用用户*
useradd -m elastic
passwd elastic
```

2. 下载并安装

```Bash
cd /usr/local
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.12.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.12.0-linux-x86_64.tar.gz
mv elasticsearch-8.12.0 elasticsearch
chown -R elastic:elastic elasticsearch
```

3. 启动

```Bash
su - elastic
cd /usr/local/elasticsearch
./bin/elasticsearch
```

首次启动会自动输出 HTTPS 访问地址、`elastic` 用户密码和 enrollment token。

4. 验证启动成功

```Bash
curl -k -u elastic https://localhost:9200
```

返回包含 `version` 和 `tagline` 的 JSON 即表示成功。

### Docker 安装（最简单）

```Bash
docker run -d \
  --name es \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  docker.elastic.co/elasticsearch/elasticsearch:8.12.0
```

访问测试：`curl ``http://localhost:9200`

### 重要配置（elasticsearch\.yml）

```YAML
cluster.name: my-es-cluster
node.name: node-1
path.data: /data/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
```

### 生产环境系统参数调整

bash

```Bash
*# 最大文件描述符*
ulimit -n 65535
*# 在 /etc/security/limits.conf 中永久设置：*
*# elastic soft nofile 65535*
*# elastic hard nofile 65535*

*# 虚拟内存*
sysctl -w vm.max_map_count=262144
*# 在 /etc/sysctl.conf 中永久生效：*
*# vm.max_map_count=262144*
```

### 设置开机自启动（systemd）

创建 `/etc/systemd/system/elasticsearch.service`：

```Plain Text
[Unit]
Description=Elasticsearch
After=network.target

[Service]
Type=simple
User=elastic
ExecStart=/usr/local/elasticsearch/bin/elasticsearch
Restart=always

[Install]
WantedBy=multi-user.target
```

```Bash
systemctl daemon-reload
systemctl enable elasticsearch
systemctl start elasticsearch
```

---

## 核心功能

### 全文搜索

基于倒排索引（Term Dictionary → Posting List）实现毫秒级检索，支持模糊搜索、语义搜索、向量搜索（ANN）、相关性评分（BM25）、自动补全、拼写检查及高亮显示。

### 数据分析与聚合

提供指标聚合、桶聚合、管道聚合、矩阵聚合等分析能力，支持实时统计、分组计算及 Transforms 数据透视转换。

### 分布式架构与高可用

采用分片（Shard）与副本（Replica）机制，支持水平扩展、自动节点恢复、自动数据再平衡、机架感知、跨集群搜索（CCS）及跨集群复制（CCR）。

### 索引生命周期管理（ILM）

自动管理索引从热（Hot）→ 温（Warm）→ 冷（Cold）→ 删除（Delete）的阶段，支持可搜索快照及数据汇总以优化存储成本。

### 地理空间搜索

支持地理距离查询、多边形及六边形空间分析，基于 BKD 树存储地理数据。

### 安全与权限控制

提供基于角色（RBAC）和属性（ABAC）的访问控制、字段级/文档级安全、加密通信、审计日志及单点登录（SSO）。

### AI 与推理服务

支持在数据所在地运行 AI 模型及 LLM，编排搜索、RAG 和智能体工作流，提供机器学习异常检测与时序预测。

---

## 常用操作命令

### 集群与索引管理

```Bash
*# 查看集群健康状态*
GET /_cluster/health

*# 查看所有索引*
GET _cat/indices?v

*# 查看节点信息*
GET _cat/nodes?v

*# 创建索引（指定分片和副本数）*
PUT /my_index
{
  "settings": {
    "index": {
      "number_of_shards": 3,
      "number_of_replicas": 1
    }
  },
  "mappings": {
    "properties": {
      "name": { "type": "text" },
      "status": { "type": "long" },
      "updatedTime": { "type": "long" }
    }
  }
}

*# 删除索引*
DELETE /my_index
```

### 文档 CRUD

```Bash
*# 新增文档（自动生成ID）*
POST /my_index/_doc
{ "name": "测试商品", "price": 99.9 }

*# 新增文档（指定ID）*
PUT /my_index/_doc/001
{ "name": "测试商品", "price": 99.9 }

*# 根据ID查询*
GET /my_index/_doc/001

*# 更新文档指定字段*
POST /my_index/_update/001
{ "doc": { "price": 129.9 } }

*# 删除文档*
DELETE /my_index/_doc/001
```

### 查询操作

```Bash
*# 查询所有*
GET /my_index/_search
{ "query": { "match_all": {} } }

*# 全文匹配*
GET /my_index/_search
{ "query": { "match": { "name": "测试" } } }

*# 精确查询*
GET /my_index/_search
{ "query": { "term": { "status": 1 } } }

*# 多条件查询（bool）*
GET /my_index/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "status": 1 } },
        { "match": { "name": "测试" } }
      ]
    }
  }
}

*# 范围查询*
GET /my_index/_search
{
  "query": {
    "range": {
      "price": { "gte": 50, "lte": 200 }
    }
  }
}

*# 分页 + 排序*
GET /my_index/_search
{
  "from": 0,
  "size": 10,
  "query": { "match_all": {} },
  "sort": [{ "price": { "order": "desc" } }]
}
```

### 批量操作

```Bash
*# 批量写入*
POST /my_index/_bulk
{ "index": { "_id": "001" } }
{ "name": "商品A", "price": 99 }
{ "index": { "_id": "002" } }
{ "name": "商品B", "price": 199 }

*# 按查询条件批量删除*
POST /my_index/_delete_by_query
{ "query": { "term": { "status": 0 } } }

*# 按查询条件批量更新*
POST /my_index/_update_by_query
{
  "script": {
    "source": "ctx._source.price = ctx._source.price * 0.9",
    "lang": "painless"
  },
  "query": { "term": { "status": 1 } }
}
```

### 分词器测试

```Bash
*# 使用 ik_smart 分词*
GET _analyze
{ "analyzer": "ik_smart", "text": "贝类酚氧化酶" }

*# 使用 ik_max_word 分词*
GET _analyze
{ "analyzer": "ik_max_word", "text": "多酚氧" }
```

---

## 实际应用场景示例

### 场景一：电商商品搜索

痛点：MySQL `LIKE '%关键词%'` 模糊查询响应慢（1\.6秒\+），高峰期 CPU 飙升至 90%\+，影响核心交易链路。

方案：

- 建立 ES 索引，使用 `ik_max_word` 分词 \+ 同义词扩展

- 关键词匹配 \+ 拼音补全 \+ 拼写纠错

- 结果排序融合销量、库存、评分等业务因子

- 通过 Kafka → Logstash → ES 实现准实时数据同步

效果：搜索响应从 1\.6秒降至 120ms，命中率提升 35%，MySQL 搜索请求下降 82%。

---

### 场景二：日志分析（ELK Stack）

痛点：日志散落在多台服务器，高峰期 200GB/小时日志量导致手工排查至少 2 小时。

方案：

- Filebeat → Logstash → Elasticsearch → Kibana 全链路

- 自定义索引模板保留关键字段（traceId、orderId 等）

- Kibana 建立近实时监控看板 \+ 告警联动

效果：排查周期从 2小时缩短到 5分钟，日志覆盖率从 60% 提升到 99%。

---

### 场景三：个性化推荐

痛点：全站热门商品一刀切推荐，用户点击率仅 3\.5%。

方案：

- 在 ES 建立用户向量与商品标签索引

- 使用 `dense_vector` \+ `script_score` 做余弦相似度计算

- 结合用户搜索历史构建个性化召回

效果：推荐 CTR 从 3\.5% 提升至 6\.8%，复购率提升 14%。

---

### 场景四：其他典型应用

- 基础设施监控：集中收集服务器、容器、IoT 设备的指标和日志，通过 Kibana 仪表盘实时可视化

- 安全分析（SIEM）：基于实时数据进行大规模网络威胁检测、调查与修复

- 地理位置搜索：查找附近门店、按距离排序（如"3公里内的餐厅"）

- 自动补全/搜索建议：用户输入时实时下拉提示

---

## 适用与不适用场景总结

|✅ 适合|❌ 不适合|
|---|---|
|全文搜索（商品、文章、日志）|事务处理（不支持 ACID）|
|日志分析与监控（ELK）|复杂多表关联查询|
|实时聚合分析|高频更新少量字段（如库存扣减）|
|地理位置搜索|海量数据批量离线分析（用 Spark）|
|自动补全/搜索建议||

> 💡 架构选型口诀：全文搜索找 ES，事务处理找 MySQL，海量存储找 HBase，消息队列找 Kafka，离线分析找 Spark。ES 与 MySQL 是互补关系，核心交易用 MySQL 保证一致性，搜索和日志用 ES 保证查询性能。
> 
> 

---

---

## 相关笔记
- [[08-环境搭建]]
- [[MongoDB操作指南]]
- [[ClickHouse使用指南]]

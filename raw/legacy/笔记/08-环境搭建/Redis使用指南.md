---
type: note
tags: [Redis] [缓存] [环境搭建]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Redis 使用指南

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 中间件章-Redis 小节

Redis 是基于内存的高性能键值存储数据库，兼具缓存、数据库与消息中间件能力，单节点 QPS 超 10 万；支持 String、Hash、List、Set、ZSet 等丰富数据结构，通过 RDB/AOF 实现持久化，并提供 Sentinel 与 Cluster 保障高可用与水平扩展，广泛应用于热点缓存、分布式锁、排行榜及消息队列等场景。

## 🚀 安装部署指南

### Linux 系统（生产环境推荐）

包管理器安装（快速上手）：

```Bash
*# Ubuntu/Debian*
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

*# CentOS/RHEL*
sudo yum install epel-release -y
sudo yum install redis -y
sudo systemctl start redis
sudo systemctl enable redis
```

源码编译安装（可定制优化）：

```Bash
wget http://download.redis.io/releases/redis-7.2.4.tar.gz
tar -zxvf redis-7.2.4.tar.gz && cd redis-7.2.4
make -j$(nproc) && sudo make install
sudo mkdir -p /etc/redis /var/redis/6379
sudo cp redis.conf /etc/redis/6379.conf
```

---

### Docker 快速部署

```Bash
docker run -d --name redis-server \
  -p 6379:6379 \
  -v /data/redis:/data \
  redis:7.2 redis-server --appendonly yes
```

---

### Windows / macOS

- macOS：`brew install redis` → `brew services start redis`

- Windows：推荐使用 WSL2 安装（`wsl --install` 后在 Ubuntu 中安装），或使用 Docker 方式

---

### 验证安装

```Bash
redis-cli ping
*# 返回 PONG 即表示服务正常*
```

---

### 关键配置（redis\.conf）

```Bash
bind 127.0.0.1          # 绑定地址（生产环境绑定内网IP）
port 6379               # 默认端口
requirepass your_password  # 设置密码认证
daemonize yes           # 后台运行
maxmemory 8gb           # 内存上限
maxmemory-policy allkeys-lru  # 淘汰策略
appendonly yes          # 开启AOF持久化
appendfsync everysec    # 每秒同步
```

---

## 🧩 核心功能

### 丰富的数据结构

|数据类型|说明|典型用途|
|---|---|---|
|String|字符串，最大512MB|缓存、计数器、分布式锁|
|Hash|键值对集合|存储对象（用户信息等）|
|List|有序链表|消息队列、时间线|
|Set|无序去重集合|标签、共同好友、抽奖|
|ZSet|带分数的有序集合|排行榜、延迟队列|
|Bitmap|位操作|签到、在线状态|
|HyperLogLog|基数统计|UV统计（极低内存）|
|Stream|消息流|持久化消息队列|
|Geo|地理位置|附近的人、距离计算|

---

### 持久化机制

- RDB（快照）：定时生成数据快照，恢复快，适合备份

- AOF（追加日志）：记录每条写命令，数据更安全

- 混合持久化（Redis 4\.0\+）：结合两者优势，推荐生产使用

---

### 高可用方案

- 主从复制：数据备份 \+ 读写分离

- Redis Sentinel：自动故障检测与转移

- Redis Cluster：16384个哈希槽分片，自动水平扩展

---

### 其他核心特性

- 单线程模型：避免锁竞争，命令执行原子性

- 事务支持：MULTI/EXEC 保证命令序列顺序执行

- Lua 脚本：原子执行复杂逻辑

- 发布/订阅：轻量级消息通知

- Pipeline：批量请求减少网络往返

---

## ⌨️ 常用操作命令

### 通用键操作

```Bash
SET key value EX 3600    *# 设置键值，3600秒后过期*
GET key                  *# 获取值*
DEL key                  *# 删除键*
EXISTS key               *# 判断键是否存在*
EXPIRE key 600           *# 设置过期时间（秒）*
TTL key                  *# 查看剩余过期时间*
KEYS pattern             *# 查找匹配的键（生产慎用，推荐SCAN）*
KEYS *name*              *# 模糊查询*
TYPE key                 *# 查看键的数据类型*
redis-cli -h IP -p 端口   *# 后台连接命令*
```

### String 操作

```Bash
SET user:name "Alice"    *# 设置*
GET user:name            *# 获取 → "Alice"*
INCR page:views          *# 原子自增（计数器）*
DECR stock:count         *# 原子自减*
SETNX lock:key 1 EX 30   *# 分布式锁（不存在时设置）*
MSET k1 v1 k2 v2        *# 批量设置*
MGET k1 k2              *# 批量获取*
```

### Hash 操作

```Bash
HSET user:1000 name "Alice" age 30   *# 设置字段*
HGET user:1000 name                  *# 获取字段 → "Alice"*
HGETALL user:1000                    *# 获取所有字段和值*
HINCRBY user:1000 age 1              *# 字段值自增*
HDEL user:1000 age                   *# 删除字段*
```

### List 操作

```Bash
LPUSH queue "task1"      *# 左侧插入*
RPUSH queue "task2"      *# 右侧插入*
LPOP queue               *# 左侧弹出*
RPOP queue               *# 右侧弹出*
LRANGE queue 0 -1        *# 获取全部元素*
LTRIM queue 0 99         *# 只保留前100条*
```

### Set 操作

```Bash
SADD tags "redis" "cache"  *# 添加成员*
SMEMBERS tags              *# 获取所有成员*
SISMEMBER tags "redis"     *# 判断是否存在*
SINTER set1 set2           *# 求交集*
SUNION set1 set2           *# 求并集*
```

### ZSet 操作

```Bash
ZADD leaderboard 100 "Alice" 200 "Bob"  *# 添加带分数成员*
ZREVRANGE leaderboard 0 9 WITHSCORES    *# 获取前10名（降序）*
ZRANK leaderboard "Alice"               *# 获取排名（升序）*
ZINCRBY leaderboard 50 "Alice"          *# 增加分数*
```

### 事务与发布订阅

```Bash
*# 事务*
MULTI
SET balance 500
DECRBY balance 100
EXEC

*# 发布/订阅*
PUBLISH news "Breaking News!"
SUBSCRIBE news
```

### 运维监控

```Bash
INFO server              *# 查看服务器信息*
SLOWLOG GET 10           *# 查看慢查询日志*
BGSAVE                   *# 异步生成RDB快照*
BGREWRITEAOF             *# 异步重写AOF文件*
CONFIG GET maxmemory     *# 查看配置*
```

---

## 💡 实际应用场景示例

### 场景一：热点数据缓存

电商商品详情页缓存，减轻数据库压力：

```Bash
*# 缓存商品信息，1小时过期*
SET product:1234:name "iPhone 16 Pro" EX 3600
SET product:1234:price "7999" EX 3600

*# 应用读取时先查Redis，未命中再查数据库并回写缓存*
GET product:1234:name
```

### 场景二：分布式锁（秒杀防超卖）

```Bash
*# 加锁（NX=不存在时设置，EX=30秒自动释放）*
SETNX lock:seckill:1001 "owner_id" EX 30

*# 业务逻辑执行完毕后释放锁*
DEL lock:seckill:1001
```

### 场景三：排行榜

游戏积分排行榜，实时更新：

```Bash
*# 玩家得分*
ZADD game:leaderboard 2500 "PlayerA"
ZADD game:leaderboard 3200 "PlayerB"
ZADD game:leaderboard 1800 "PlayerC"

*# 获取前3名（降序）*
ZREVRANGE game:leaderboard 0 2 WITHSCORES
*# 1) "PlayerB"  3200*
*# 2) "PlayerA"  2500*
*# 3) "PlayerC"  1800*
```

### 场景四：消息队列

异步任务处理（如订单通知）：

```Bash
*# 生产者：推送消息*
LPUSH order:queue '{"orderId":1001,"action":"ship"}'

*# 消费者：阻塞弹出（BRPOP，超时60秒）*
BRPOP order:queue 60
```

### 场景五：分布式 Session 共享

多台 Web 服务器共享用户会话：

```Bash
*# 用户登录后存储Session*
SET session:abc123 '{"userId":1000,"role":"admin"}' EX 1800

*# 任意服务器验证Session*
GET session:abc123
```

### 场景六：接口限流

基于滑动窗口实现 API 频率限制：

```Bash
*# 每次请求时原子自增计数器*
INCR rate:api:user:1000
EXPIRE rate:api:user:1000 60   *# 60秒窗口*

*# 判断是否超过阈值（如100次/分钟）*
GET rate:api:user:1000
```

### 场景七：用户签到（Bitmap）

```Bash
*# 用户第5天签到*
SETBIT sign:2026:09:user:1000 5 1

*# 统计本月签到天数*
BITCOUNT sign:2026:09:user:1000
```

### 场景八：UV 统计（HyperLogLog）

```Bash
*# 记录访问用户*
PFADD page:home:uv "user001" "user002" "user003"

*# 统计独立访客数（近似值，误差<0.81%）*
PFCOUNT page:home:uv
```

---

> 📌 生产环境最佳实践：设置 `requirepass` 密码认证；使用 `rename-command` 禁用危险命令（如 FLUSHALL）；合理配置 `maxmemory` 和淘汰策略；开启 AOF \+ RDB 混合持久化；使用 SCAN 替代 KEYS 避免阻塞；避免大 Key（String 超过 10KB 需拆分）。
> 
> 

## 🔍 功能验证测试

### 缓存读写验证

以电商商品详情页缓存为例：

- 写入验证：首次访问接口后，通过 `redis-cli` 执行 `GET product:1234:name`，确认 Key 已成功写入，且 Key 命名规范、数据结构正确（该用 Hash 的不能用 String）

- 读取验证：第二次访问同一接口，观察响应时间是否明显变快，同时查看数据库日志确认未产生新的查询操作

- 过期验证：等待 TTL 到期（或手动 `DEL` 删除 Key），再次访问接口，确认系统重新从数据库加载并回写缓存

```Bash
*# 验证写入*
GET product:1234:name
*# 验证过期时间*
TTL product:1234:name
*# 验证数据类型*
TYPE product:1234:name
```

### 排行榜功能验证

```Bash
*# 初始化积分数据*
ZADD user:score 1000 "user1001" 850 "user1002" 900 "user1003"
*# 验证排名（降序）*
ZREVRANGE user:score 0 9 WITHSCORES
*# 更新积分后验证排名变化*
ZINCRBY user:score 50 "user1002"
ZREVRANK user:score "user1002"
```

### 分布式锁验证

```Bash
*# 验证加锁成功（NX 不存在时设置）*
SETNX lock:order:1001 "owner_A" EX 30
*# 验证重复加锁失败（返回 nil）*
SETNX lock:order:1001 "owner_B" EX 30
*# 验证锁过期后自动释放（等待30秒后重试加锁应成功）*
```

### Session 共享验证

- 用户登录后，通过 `GET session:abc123` 确认 Session 已写入 Redis

- 模拟请求打到另一台 Web 服务器，验证登录状态仍然保持

---

## ⚡ 性能压测测试

### redis\-benchmark 官方工具

```Bash
*# 单节点 SET/GET 压测（100并发，100万请求）*
redis-benchmark -h 127.0.0.1 -p 6379 -a your_password \
  -c 100 -n 1000000 -t set,get -d 256 -q

*# Pipeline 批量请求压测*
redis-benchmark -h 127.0.0.1 -p 6379 -a your_password \
  -c 100 -n 1000000 -t set,get -P 16 -q

*# 集群模式压测（需 Redis 6.0+，必须加 --cluster 参数）*
redis-benchmark -h 192.168.1.100 -p 8001 -a your_password \
  --cluster -c 100 -n 1000000 -t get,set -q
```

### memtier\_benchmark 工具（支持自定义读写比）

```Bash
*# 读写比 7:3 的真实流量模拟*
memtier_benchmark -s 127.0.0.1 -p 6379 \
  -c 100 -t 4 -n 1000000 --ratio=7:3

*# 纯读测试*
memtier_benchmark -s 127.0.0.1 -p 6379 \
  -c 100 -t 4 -n 1000000 --ratio=0:10
```

### 关键性能指标

|指标|说明|参考基准|
|---|---|---|
|QPS|每秒处理请求数|单节点通常 \>10万|
|P99 延迟|99%请求的响应时间|\<1ms 为佳|
|缓存命中率|hits/\(hits\+misses\)|核心业务 ≥95%|
|内存碎片率|used\_memory\_rss/used\_memory|接近 1\.0 为佳|

### 缓存命中率验证

```Bash
*# 查看命中/未命中统计*
redis-cli INFO stats | grep keyspace
*# keyspace_hits:123456*
*# keyspace_misses:5000*
*# 命中率 = 123456 / (123456 + 5000) ≈ 96.1%*
```

---

## 🚨 异常容灾测试

### 缓存穿透测试

> 查询数据库中根本不存在的数据，请求全部穿透缓存打到数据库
> 
> 

```Bash
*# 模拟：连续请求不存在的 Key*
for i in $(seq 1 1000); do
  redis-cli GET product:-1
done
*# 验证：观察数据库连接数是否飙升*
*# 预期：应有空值缓存或布隆过滤器拦截*
```

### 缓存雪崩测试

> 大量 Key 同时过期，请求瞬间全部打到数据库
> 
> 

```Bash
*# 模拟：手动清空所有缓存*
FLUSHDB
*# 然后用 JMeter 模拟 1000 并发请求*
*# 验证：系统是否有降级策略（如限流、熔断），数据库是否扛住*
```

### 缓存击穿测试

> 某个热点 Key 过期瞬间，大量并发请求同时查库
> 
> 

```Bash
*# 模拟：删除热点商品缓存*
DEL product:hot:1001
*# 同时用 JMeter 发起 1000 并发请求访问该商品*
*# 验证：是否有互斥锁保护，数据库查询次数应远小于请求数*
```

### Redis 宕机降级测试

```Bash
*# 模拟 Redis 宕机*
redis-cli shutdown
*# 访问系统各功能模块*
*# 预期：系统自动降级直查数据库，功能可用但响应变慢，不出现白屏或报错*
```

---

## 🔄 数据一致性测试

### 更新后缓存同步验证

```Bash
*# 步骤1：修改数据库中的用户昵称*
*# 步骤2：立即查询 Redis*
GET user:1000:name
*# 验证：缓存是否已更新为新值（或已被删除等待下次回写）*
```

### 并发修改一致性验证

- 模拟两个用户同时修改同一条数据

- 验证最终数据库和缓存中的值是否一致，不出现脏数据

- 重点关注"先更新数据库还是先删缓存"的策略实现

### 数据格式一致性验证

```Bash
*# 对比接口返回值与 Redis 存储值*
GET user:1000:profile
*# 验证：字段类型是否一致（如时间戳 vs 格式化字符串）*
*# 验证：是否有冗余字段或缺失字段*
```

---

## 🏗️ 高可用测试

### 主从复制测试

- 主节点写入数据后，验证从节点能同步读取

- 主节点宕机后，手动执行 `SLAVEOF` 切换，验证从节点晋升为主节点

### Sentinel 哨兵测试

```Bash
*# 模拟主节点故障*
kill -9 <redis-master-pid>
*# 观察 Sentinel 日志状态流转*
*# +sdown → +odown → +failover → +switch-master*
*# 验证：自动选主完成，客户端能自动重连新主节点*
```

### Cluster 集群测试

- 验证 16384 个哈希槽分布均匀

- 模拟某个主节点宕机，验证从节点自动晋升

- 使用 `iptables` 模拟网络分区，验证写入行为是否符合预期

---

## 🔒 安全测试

```Bash
*# 未授权访问测试（应返回 -NOAUTH）*
redis-cli -h 127.0.0.1 -p 6379 GET test_key

*# 密码认证测试*
redis-cli -h 127.0.0.1 -p 6379 -a your_password GET test_key

*# ACL 权限控制测试（Redis 6.0+）*
ACL SETUSER testuser on ">password" ~cache:* +get +set
*# 验证：testuser 只能访问 cache:* 前缀的 Key，且只能执行 GET/SET*
```

---

## 📋 测试场景速查表

|维度|核心测试点|工具/方法|
|---|---|---|
|功能|缓存读写、过期、数据结构正确性|redis\-cli|
|性能|QPS、延迟、命中率、并发承载|redis\-benchmark、JMeter|
|异常|穿透/雪崩/击穿、宕机降级|手动模拟 \+ JMeter|
|一致性|DB与缓存同步、并发修改、格式校验|接口测试 \+ redis\-cli|
|高可用|主从切换、哨兵故障转移、集群扩缩容|kill进程 \+ 日志观察|
|安全|未授权访问、ACL权限、TLS加密|redis\-cli 直连测试|

---

> 📌 测试建议：优先覆盖异常容灾和数据一致性两类场景——这两类是线上事故最高发的区域。性能测试建议在独立环境进行，避免影响生产；压测前确认关闭或调整持久化策略以减少 IO 干扰。
> 
> 

---

---

## 相关笔记
- [[08-环境搭建]]
- [[Nginx配置详解]]
- [[MongoDB操作指南]]

---
title: Linux系统监控-网络
type: concept
domain: 环境与工具
created: 2026-09-14
updated: 2026-09-14
sources: [raw/legacy/笔记/08-环境搭建/Linux系统监控-网络.md]
tags: [linux, tooling, env-setup, performance-testing, interview]
confidence: high
status: active
publish: true
interview:
  cat: database-linux
  kind: skill
  level: 中级
---

# Linux 系统监控：网络

## 一句话
网络排查三板斧：**ss/lsof 管端口与连接**、**ping 管延迟与抖动**、**队列长度管应用是否跟上**。比"延迟多少毫秒"更值得盯的是**抖动（mdev）**——平均 50ms 但抖动 20ms 的网络，体验远差于平均 80ms 而抖动 2ms 的。

## 端口与连接：ss / lsof

```bash
ss -tulnp | grep <端口>    # netstat 的现代替代，更快、信息更全（-p 要 sudo）
lsof -i :<端口> -P -n      # 精准定位某端口被哪个进程占用；-P/-n 禁止名称解析防卡顿
```

**ss 输出的两个队列是排障金矿**：
- `Recv-Q` 持续不为 0 → 应用取数据的速度跟不上网络收包速度（应用处理慢了）
- `Send-Q` 持续不为 0 → 网络拥塞或对端处理缓慢

## 延迟与抖动：ping 的进阶用法

```bash
ping -c 100 -i 0.2 <target>   # 采样 100 次（-i <0.2 需 root）
ping -q -c 100 <target>       # 静默模式，直接取统计摘要
ping -s 1472 -M do <target>   # 大包探测 MTU/分片问题
```

统计行 `rtt min/avg/max/mdev` 里，**mdev（抖动）比 avg 更重要**：mdev <1ms 极稳定（局域网/专线）；1~10ms 正常公网；>20ms 严重抖动，查 QoS/拥塞/设备负载。

**实用判别技巧**：
- 先 `ping IP` 再 `ping 域名`——域名首包明显更慢是 **DNS 解析慢**，不是网络问题
- 建立基线：业务低峰期采一轮数据做对照；"CPU 60% 算不算高"没有绝对答案，延迟同理
- 周期性延迟尖峰 → 多半是定时任务/备份在抢带宽

延迟参考（同地域云服务器 <2ms 优秀、跨省公网 40~100ms 正常、Web/API 含后端处理 50~150ms 正常——完整表见原料）。

## 测试视角的落点

- **压测时的网络观测**：重传率 >2%、建连时间 >50ms 是 [[性能瓶颈的分层模型]] 网络层的风险阈值；`ss` 的 Recv-Q/Send-Q 堆积说明瓶颈在应用或对端而非带宽
- **连接数验证**：长连接是否真被复用，看 `ss` 里 ESTABLISHED 数量是否符合连接池配置，而不是想当然
- 排查顺序上网络排在 CPU/内存/磁盘之后，见 [[性能瓶颈定位的分层排查路径]]

## 相关
- [[Linux系统监控-CPU]]
- [[Linux系统监控-磁盘]]
- [[TCP与UDP的核心差异]]
- [[性能瓶颈定位的分层排查路径]]
- [[面试助手题库索引]]

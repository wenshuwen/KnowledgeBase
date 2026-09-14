---
title: Linux系统监控-内存
type: concept
domain: 环境与工具
created: 2026-09-14
updated: 2026-09-14
sources: [raw/legacy/笔记/08-环境搭建/Linux系统监控-内存.md]
tags: [linux, tooling, env-setup, performance-testing, interview]
confidence: high
status: active
publish: true
interview:
  cat: database-linux
  kind: skill
  level: 中级
---

# Linux 系统监控：内存

## 一句话
看内存健康只认一个指标：**`available`**。`free` 少是 Linux 的正常姿态（空闲内存拿去做缓存了），而 Swap 是否在**持续换入换出**才是内存不足的真正信号。

## free 的正确读法

```bash
free -h        # 人类可读单位（推荐）
free -s 3      # 每 3 秒刷新，观察趋势
```

`buff/cache` 虽被占用但随时可回收；`available` = free + 可回收的 buff/cache，**才是"还能给新程序多少内存"的答案**。

## 关键命令

```bash
top 按大写 M            # 按内存排序找"内存大户"；主要看 RES 列
ps aux --sort=-%mem | head
vmstat 1 10            # 核心：观察 si / so 两列
cat /proc/meminfo | grep -E "SwapTotal|SwapFree|SwapCached|Dirty"
sar -W 1               # 专门看每秒换页数
```

**Swap 速率判读**（比 Swap used 大小重要得多）：

| si/so 表现 | 结论 | 动作 |
|---|---|---|
| 始终为 0 | Swap 只是静态占用，无性能影响 | 忽略 |
| 持续 > 几百 KB/s | 内存带宽被 Swap 拖垮，响应时间剧烈波动 | 查内存泄漏 / 流量超物理内存上限 |
| 间歇性突发 | 定时任务瞬间申请大内存 | 错峰执行 / 调整堆与内存池 |

## 高频问题与判别

- **available 充足但 Swap 还在涨** → 内核的内存冷热分级策略：主动把"冷"页换出腾给文件缓存。看速率，不看存量
- **内存还有，应用却 OOM** → 进程级限制不是系统级：查 `ulimit -a`、JVM `-Xmx` 是否设小了
- **容器内 free 显示充足但应用报内存不足** → 容器看到的是宿主机内存；真实限额要读 cgroup（`/sys/fs/cgroup/memory/memory.limit_in_bytes`）
- **RES 持续增长不回落** → 疑似内存泄漏，Heap Dump 后用 MAT 分析 GC Root 引用链
- **swappiness 调优**：数据库服务器设 1~10（内核"不到万不得已别用 Swap"），默认 60 适合通用服务器

## 物理内存 vs 虚拟内存

物理内存（RAM）纳秒级、断电即失，决定"跑多快"；虚拟内存是拿磁盘充当内存的蓄水池（Swap），毫秒级——**慢 3~4 个数量级**，这就是"Swap 是性能杀手"的物理原因。

## 相关
- [[Linux系统监控-CPU]]
- [[Linux系统监控-磁盘]]
- [[性能瓶颈的分层模型]]
- [[Redis缓存的五类经典问题]]
- [[面试助手题库索引]]

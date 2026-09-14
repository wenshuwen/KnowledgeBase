---
title: Linux系统监控-CPU
type: concept
domain: 环境与工具
created: 2026-09-14
updated: 2026-09-14
sources: [raw/legacy/笔记/08-环境搭建/Linux系统监控-CPU.md]
tags: [linux, tooling, env-setup, performance-testing, interview]
confidence: high
status: active
publish: true
interview:
  cat: database-linux
  kind: skill
  level: 中级
---

# Linux 系统监控：CPU

## 一句话
CPU 监控的核心不是看利用率数字，而是**拆开 us/sy/wa 三个成分**——它们分别指向计算密集、锁/系统调用、I/O 等待三条完全不同的排查路径。

## CPU 使用率成分判读（top 的 %Cpu(s) 行）

| 成分 | 含义 | 高了说明什么 | JVM 关联 |
|---|---|---|---|
| `us` | 用户态 | 计算密集 / 死循环 / 算法低效 | 业务代码、GC 线程主要耗在这里 |
| `sy` | 内核态 | 锁竞争、系统调用频繁、上下文切换多 | JNI/native 调用过重 |
| `wa` | I/O 等待 | **CPU 在等磁盘/网络 I/O，元凶往往不是 CPU** | GC 日志同步写盘会加剧 |
| `st` | 虚拟化窃取 | 宿主机超卖，邻居租户在抢 CPU（云环境专属） | >5% 找云厂商 |

经验线：`us + sy` 长期 > 80% 是计算瓶颈；`wa` 持续 > 20% 是 I/O 信号——**wa 高时先查磁盘，别盯着 CPU 优化**。

## 关键命令

```bash
top -o %CPU          # 按 CPU 排序；按 1 可看各核心
top -Hp <PID>        # 线程视图：进程内哪个线程在烧 CPU（jstack 的实时版）
ps aux --sort=-%cpu | head    # 快照式列出 CPU 前 10 进程
uptime               # load average：1/5/15 分钟平均负载，持续 > 核心数即过载
vmstat 1             # 看 cs（上下文切换）、in（中断）、r（运行队列）
```

线程数直接统计：`ls /proc/<PID>/task | wc -l`（最准确，适合脚本）。

## 避坑清单

- **不要只看一次快照**：top 是实时工具，单次截图意义有限；至少观察 3–5 个刷新周期，或 `top -b -d 1 -n 60 > top.log` 录制趋势
- **%CPU > 100% 不是 bug**：多核机器上一个进程上限 = 核心数 × 100%
- **容器内 top 可能失真**：旧内核下看到的是宿主机资源，务必确认 cgroup 视图
- **Load 高但 CPU 空闲**：多半是 D 状态进程堆积（`ps axo state,pid,comm | grep ^D`），根因常在 I/O 或 NFS 挂载
- **生产慎用 `jmap -heap`**：会触发 Full GC，优先 `jcmd`/`jstat`

## 症状速查

| 症状 | top 特征 | 下一步 |
|---|---|---|
| us 高、wa 低 | us > 80% | `top -Hp` 找热点线程 → jstack 看栈 |
| wa 高 | wa > 20~30%，进程大量 D 状态 | 转 [[Linux系统监控-磁盘]]：iostat 看 %util/await |
| sy 高 | sy > 30%，cs 飙升 | vmstat 看 cs/in；jstack 搜 BLOCKED |
| st 高 | st > 5% | 联系云厂商 / 迁独占实例 |
| Load 高 CPU 空闲 | load ≫ 核数，id > 70% | 找 D 状态进程，查 I/O 与网络存储 |

## 相关
- [[Linux系统监控-内存]]
- [[Linux系统监控-磁盘]]
- [[性能瓶颈的分层模型]]
- [[性能瓶颈定位的分层排查路径]]
- [[面试助手题库索引]]

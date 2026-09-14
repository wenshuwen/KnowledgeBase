---
title: Linux系统监控-磁盘
type: concept
domain: 环境与工具
created: 2026-09-14
updated: 2026-09-14
sources: [raw/legacy/笔记/08-环境搭建/Linux系统监控-磁盘.md]
tags: [linux, tooling, env-setup, performance-testing, interview]
confidence: high
status: active
publish: true
interview:
  cat: database-linux
  kind: skill
  level: 中级
---

# Linux 系统监控：磁盘

## 一句话
磁盘排查分两个问题：**空间够不够**（df/du）和**速度快不快**（iostat）。性能问题里更要命的是后者——`%util` 与 `await` 两个指标组合起来读，才能定性 I/O 瓶颈。

## 空间：df / du / inode

```bash
df -h            # 各文件系统使用率（>80% 重点关注）
df -i            # inode 使用情况——空间充足却建不了新文件，多半是 inode 耗尽
du -sh /var/log  # 定位大目录
du -h --max-depth=1 / | sort -hr | head -10   # 根目录下最大的 10 个目录
```

`df` 看文件系统、`du` 看目录；两者对不上时，通常是**文件已删除但进程仍持有句柄**——`lsof | grep deleted` 找到进程，重启即释放。

## 性能：iostat 字段判读

```bash
iostat -dx 1 5   # 每秒采样，共 5 次
```

| 字段 | 含义 | 判读 |
|---|---|---|
| `%util` | 磁盘繁忙度 | <70% 正常；**≥80% 持续 = I/O 饱和**（与 [[性能瓶颈的分层模型]] 阈值一致） |
| `await` | 平均 I/O 等待（ms） | SSD <1ms、HDD 10~30ms 正常；>20ms 警惕，>50ms 严重 |
| `avgqu-sz` | 平均队列长度 | 持续 >10 = 请求在排队，磁盘处理不过来 |
| `r/s w/s` | IOPS | 与吞吐（rkB/s、wkB/s）分开看 |

**避坑**：iostat 第一次输出是开机以来的平均值，会掩盖瞬时波动——**忽略第一次，只看后续采样**。

**三个瓶颈信号**（同时满足更确定）：%util 持续接近 100% 且 await 升高（饱和）；avgqu-sz > 10（队列堆积）；CPU `wa` > 20~30%（CPU 在等 I/O）。

**一个典型误判**：%util 高但 rkB/s 很低 → 大量**小文件随机读写**（频繁打日志、随机更新索引），这是最坏的 I/O 模式，比大文件顺序写伤害大得多。定位具体进程用 `sudo iotop -o`。

## 案例：/tmp 目录爆满的处置套路

**先诊断，后清理，再根治**，严禁盲目 rm：

1. `df -h /tmp` 确认是独立分区还是 tmpfs
2. 快速恢复：`find /tmp -type f -mtime +1 -delete` 按时间清旧文件（最安全的清理方式）；正被使用的日志改为清空（`> file.log`）而非删除
3. 清了还是 100%？→ 进程持有已删除文件的句柄（`lsof /tmp | grep deleted`），或 **inode 耗尽**（`df -i /tmp`，清理海量小文件）
4. 根治：独立分区/LVM 扩容、fstab 限制 tmpfs size、设 80% 阈值告警

## 相关
- [[Linux系统监控-CPU]]
- [[Linux系统监控-内存]]
- [[性能瓶颈定位的分层排查路径]]
- [[性能瓶颈的分层模型]]
- [[面试助手题库索引]]

---
type: note
tags: [Linux] [环境搭建] [性能排查]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 系统监控：CPU

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-CPU 小节

## 1\.1 top

## **🐾 常用命令参数说明**

```Shell
*# 指定刷新间隔（秒）*
top -d 2          *# 每2秒刷新一次*

*# 指定运行次数后自动退出*
top -n 5          *# 刷新5次后退出*

*# 批处理模式（适合脚本和日志记录）*
top -b            *# 批处理模式*
top -b -n 1       *# 批处理模式，只运行一次*

*# 监控指定进程*
top -p 1234       *# 只监控PID为1234的进程*
top -p 1234,5678  *# 监控多个进程*

*# 指定排序字段*
top -o %CPU       *# 按CPU使用率排序*
top -o %MEM       *# 按内存使用率排序*

*# 显示完整命令行*
top -c

*# 以其他用户身份运行*
top -u username   *# 只显示指定用户的进程*
top -u mysql      *# 只显示mysql用户的进程*

*# 安全模式（禁用交互命令）*
top -s

*# 延迟启动*
top -d 5 -n 10    *# 5秒刷新，运行10次*

### 批处理模式输出到文件 ###
*# 单次快照*
top -b -n 1 > top_snapshot.txt

*# 持续监控并记录*
top -b -d 2 -n 60 > top_log.txt  *# 每2秒记录一次，共60次*

*# 监控特定进程*
top -b -p 1234 -n 10 > process_monitor.log
### 批处理模式输出到文件 ###

# 查看CPU占用最高的进程
top -o %CPU
ps aux --sort=-%cpu | head
 
*# 看进程内各线程的CPU消耗，查看指定 Java 进程的线程数*
top -Hp <PID>
*-H：显示线程视图*
*-p <PID>：指定进程 ID*
*输出中每一行代表一个线程，可直观看到线程数和 CPU 占用情况*
```

- **针对 JVM 的高级用法**

```Shell
# 只看 Java 进程，按内存排序，批处理模式输出一次
top -b -n 1 -p $(pgrep -d',' java) -o %MEM

# 线程模式查看指定 JVM 进程（等价于 jstack 的实时版）
top -H -p <JVM_PID>

# 自定义显示列：加入 SWAP 和 PSS（如果内核支持）
top -o %MEM
# 然后按 f → 勾选 SWAP、PSS → q 返回
```

## **🎈 CPU 使用率字段说明**

```Shell
%Cpu(s):  2.3 us,  1.0 sy,  0.0 ni, 95.7 id,  0.8 wa,  0.0 hi,  0.2 si,  0.0 st

*us (用户态) + sy (内核态) 长期 > 80%：说明CPU被计算密集任务耗尽（如死循环、复杂算法）。*
*wa (I/O等待) 持续 > 20%：强烈信号——CPU在等磁盘或网络I/O，应用很可能是被I/O拖慢，而非计算。*
```

- us \(User\)：用户空间进程使用的 CPU 时间百分比

- sy \(System\)：内核空间进程使用的 CPU 时间百分比

- ni \(Nice\)：被调整优先级的用户进程使用的 CPU 时间

- id \(Idle\)：空闲的 CPU 时间百分比

- wa \(IO Wait\)：等待 I/O 操作完成的 CPU 时间百分比

- hi \(Hardware IRQ\)：硬件中断占用的 CPU 时间

- si \(Software IRQ\)：软件中断占用的 CPU 时间

- st \(Steal Time\)：虚拟化环境中被其他虚拟机占用的时间

|缩写|全称|含义|JVM 关联|
|---|---|---|---|
|`us`|user|用户态 CPU|JVM 业务代码、GC 线程主要消耗在此|
|`sy`|system|内核态 CPU|JNI 调用、系统调用、线程上下文切换过多时升高|
|`ni`|nice|低优先级用户态|调整过 nice 值的进程|
|`id`|idle|空闲|越低越繁忙|
|`wa`|iowait|I/O 等待|高 wa = 磁盘瓶颈，GC 日志写盘慢会加剧此值|
|`hi`|hardware irq|硬中断|网卡/磁盘控制器中断|
|`si`|software irq|软中断|网络包处理密集时升高|
|`st`|steal|虚拟化窃取|云环境专属。\>0 表示宿主机超卖，邻居租户在抢 CPU|

> ***⚠️ JVM GC 诊断：如果 ******`us`****** 很高且伴随频繁 FGC，是堆内存问题；如果 ******`sy`****** 很高，检查是否有大量 JNI/native 调用或锁竞争导致的系统调用。***
> 
> 

## **🔍 进程详情列表区**

|列名|含义|JVM 排查要点|
|---|---|---|
|`PID`|进程 ID|用于 `jcmd`/`jstack`/`jmap` 的目标标识|
|`USER`|进程所有者|确认是否以正确用户运行|
|`PR`|优先级|数值越小优先级越高|
|`NI`|Nice 值|\-20\(最高\) \~ 19\(最低\)，影响调度权重|
|`VIRT`|虚拟内存总量|JVM 预分配的地址空间，不代表真实占用。通常远大于 RES|
|`RES`|驻留物理内存|⭐ top %MEM 的计算分子。包含堆\(committed\)\+堆外\+共享库。如果这个数值持续增长且不回落 → 疑似内存泄漏。|
|`SHR`|共享物理内存|与其他进程共享的部分（如 libc\.so、classes\.jsa）|
|`S`|进程状态|R=运行, S=睡眠, D=不可中断 I/O, Z=僵尸, T=停止|
|`%CPU`|CPU 使用率|单核百分比。多核机器上可 \>100%|
|`%MEM`|物理内存占比|`RES / MemTotal × 100%`|
|`TIME+`|累计 CPU 时间|格式 `分:秒.百分秒`，反映进程历史总消耗|
|`COMMAND`|启动命令|按 `c` 键切换显示完整命令行（含 JVM 参数）|

- **VIRT vs RES vs SHR 关系图**

```Shell
┌─────────────────── VIRT ───────────────────┐
│  ┌──────── RES ────────┐                   │
│  │ Private Memory      │  ← JVM Heap/Stack │
│  │ (匿名页)             │     Direct Memory │
│  ├─────────────────────┤                   │
│  │ SHR (共享物理内存)   │  ← .so / .jsa     │
│  └─────────────────────┘                   │
│  Unmapped / Swapped out                    │
│  (已分配但未加载到物理内存的虚拟页)           │
└────────────────────────────────────────────┘
```

## **🌤️ 交互命令详解**

|按键|功能|
|---|---|
|P|按%CPU 降序排序（默认）|
|M|按%MEM 降序排序（排查内存占用）|
|N|按 PID 升序排序|
|T|按 TIME\+降序排序（排查 CPU 累计占用高的进程）|
|R|反转当前排序顺序|
|1|显示所有 CPU 核心的详细使用率（多核心服务器必备）|
|c|切换显示简化命令/完整命令行|
|z|切换颜色/黑白显示模式|
|b|高亮显示运行中的进程|
|x|高亮显示排序列|
|E|切换内存单位（KB/MB/GB）|
|e|切换单个进程内存单位|
|k|杀死进程（输入 PID 和信号）|
|r|重新设置进程优先级（renice）|
|d|修改刷新间隔时间|
|u|只显示指定用户的进程|
|n|设置显示的进程数量|
|q|退出 top|
|Ctrl\+L|清屏并重新绘制|

## **🎱 使用场景示例**

|场景|操作|
|---|---|
|监控 CPU 飙升进程|按 P 键（已默认按 CPU 降序）—\>按 1 键查看各 CPU 核心使用情况|
|监控内存泄漏|按 M 键（按内存使用率降序）—\>观察 RES 和%MEM 列的变化|
|僵尸进程处理|如果 zombie 数量不为 0：<br>\# 1\. 找到状态为 Z 的进程<br>\# 2\. 找到其父进程（PPID）<br>\# 3\. 重启或杀死父进程|
|实时监控脚本<br>|\#\!/bin/bash<br>\# 监控 CPU 使用率超过 80%的进程<br>while true; do<br>clear<br>echo "=== CPU 使用率超过 80%的进程 ==="<br>top \-b \-n 1 \| awk 'NR\>7 \&\& $9\>80 \{print $0\}'<br>sleep 5<br>done|
|高负载排查|如果 load average 持续很高：<br>\# 1\. 按 P 查看 CPU 占用高的进程<br>\# 2\. 按 1 查看是否有单个 CPU 核心过载<br>\# 3\. 检查 wa（I/O 等待）是否过高|
|内存不足排查|如果内存使用率很高：<br>\# 1\. 按 M 查看内存占用高的进程<br>\# 2\. 检查 swap 使用情况<br>\# 3\. 查看 buff/cache 是否异常|

## 1\.2 lscpu

- 常用命令：

```Shell
**lscpu             **# 查看CPU硬件架构详细信息(核心数、线程数、型号等)
**lscpu -a          ***# 显示所有CPU信息***
****lscpu -e          ***# 以扩展格式显示***
****lscpu -p          ***# 以解析格式显示*
```

- 输出示例及含义：

```Shell
Architecture:        x86_64          # CPU架构
CPU(s):              8               # 逻辑CPU总数
Thread(s) per core:  2               # 每个核心的线程数
Core(s) per socket:  4               # 每个插槽的核心数
Socket(s):           1               # 物理CPU插槽数
Model name:          Intel Core i7   # CPU型号
CPU MHz:             2904.000        # CPU频率
```

## 1\.3 cpuinfo

- 常用命令：

```Shell
# 查看详细CPU信息
cat /proc/cpuinfo
**   **
*# 查看CPU型号*
cat /proc/cpuinfo | grep "model name" | uniq

*# 查看物理CPU个数*
cat /proc/cpuinfo | grep "physical id" | sort | uniq | wc -l

*# 查看逻辑CPU个数*
cat /proc/cpuinfo | grep "processor" | wc -l

*# 查看每个物理CPU的核心数*
cat /proc/cpuinfo | grep "cpu cores" | uniq
```

## 1\.4 htop

功能说明：

- top 的增强版本，提供更友好的图形化界面

- 支持鼠标操作和颜色高亮

```Shell
*# Ubuntu/Debian*
sudo apt install htop

*# CentOS/RHEL*
sudo yum install htop
```

## 1\.5 uptime

功能说明：

- 主要用于查看系统运行了多长时间以及系统的整体负载情况。

- 显示过去 1 分钟、5 分钟、15 分钟内的平均负载

```Shell
10:57:00 up 10 days, 2:25, 2 users, load average: 0.10, 0.15, 0.12

1.当前时间（例如 10:57:00）
显示当前系统的本地时间。

2.系统运行时长（例如 up 10 days, 2:25）
表示系统自上次重启以来，已经连续运行了 10天2小时25分钟。如果这个时间很短，说明服务器最近可能经历过重启或崩溃。

3.当前登录用户数（例如 2 users）
表示当前有多少个用户终端（包括 SSH 远程连接和物理终端）登录到了系统。

4.系统平均负载（例如 load average: 0.10, 0.15, 0.12）
这是 uptime 命令中最核心、也最容易让人困惑的指标。这三个数字分别代表系统在过去 1分钟、5分钟、15分钟 内的平均负载。
```

## 1\.6 ps

- 命令行快速列出 cpu 占用前 10 的进程

```Shell
# 按CPU使用率（%CPU）降序排列
ps aux --sort=-%cpu | head
```

## 1\.7 速查总结

|问题场景|top 关键特征|根因假设|下一步排查动作|
|---|---|---|---|
|JVM 堆内存溢出 / FGC 频繁|`us` ↑, `%MEM` 高且稳定, Swap=0|堆空间不足或内存泄漏|① `jstat -gcutil <PID> 1000` 看 O 区增长<br>② `jmap -histo:live <PID>` 看大对象<br>③ Dump 堆用 MAT 分析|
|堆外内存泄漏 \(OOM Killed\)|`%MEM` 持续↑, VIRT≫RES, Swap=0|DirectMemory/NIO/Metaspace 泄漏|① 开启 NMT: `jcmd <PID> VM.native_memory summary`<br>② 检查 `-XX:MaxDirectMemorySize`<br>③ 查 glibc malloc 统计|
|I/O 阻塞 / 磁盘瓶颈<br>|`wa` \> 30%, 进程状态大量 `D`|日志刷盘/数据库慢查询/GC 日志|① `iostat -xz 1` 看 %util/await<br>② `iotop -aP` 定位 I/O 线程<br>③ 检查 GC 日志是否同步写盘|
|CPU 热点 \(业务代码\)|`us` \> 80%, 单进程 %CPU 极高|死循环/复杂计算/序列化|① `top -H -p <PID>` 找热点线程 TID<br>② `printf '%x\n' <TID>` 转 16 进制<br>③ \`jstack |
|锁竞争 / 上下文切换风暴|`sy` \> 30%, running 数 ≫ CPU 核数|synchronized/Lock 争抢|① `vmstat 1` 看 cs/in 列<br>② `jstack <PID>` 搜 BLOCKED/WAITING<br>③ Arthas: `thread -b` 查阻塞源|
|JNI / Native 调用过重|`sy` ↑, `us` 正常, RES 波动大|压缩解压/加密/本地库调用|① `perf top -p <PID>` 看内核态函数<br>② Arthas: `trace native_method`<br>③ 审查 JNI 代码中的内存分配|
|云主机 CPU 被窃取|`st` \> 5%, id 低但 us/sy 不高|宿主机超卖/邻居租户抢占|① 联系云厂商确认 SLA<br>② 迁移至独占型实例<br>③ 应用层增加超时重试兜底|
|Swap 抖动 \(GC 停顿秒级\)|Swap used \> 0, `wa` ↑, STW 暴增|物理内存不足触发换页|① 立即: `swapoff -a && swapon -a` 临时止血<br>② 调小 `-Xmx`, 设 `vm.swappiness=1`<br>③ 排查是否有其他进程挤占内存|
|线程泄漏|Tasks total 持续↑, RES 缓慢↑|Thread\.new\(\) 未复用/连接池泄漏|① \`jstack |
|Load 高但 CPU 空闲|load avg ≫ CPU 核数, id \> 70%|I/O 等待 / D 状态进程堆积|① `ps axo state,pid,comm | grep ^D`<br>② `cat /proc/<PID>/wchan` 看卡在哪<br>③ 排查 NFS/网络存储挂载点|

**⚠️ 排查时的避坑提醒**

- 不要只看一次快照：`top` 是实时工具，单次截图意义有限。至少观察 3\-5 个刷新周期 或使用 `top -b -d 1 -n 60 >> /tmp/top.log` 录制趋势。

- 生产环境慎用 `jmap -heap`：该命令会触发 Full GC（JDK8u40 之前），优先使用 `jcmd` 或 `jstat`。

- 容器内 top 可能失真：在旧版内核 Docker 中，`top` 看到的是宿主机资源。务必确认 cgroup 视图。

- %CPU \> 100% 不是 Bug：多核机器上，一个 JVM 进程的 %CPU 上限 = `核心数 × 100%`。8 核机器上看到 600% 是正常的。

- free 内存少 ≠ 内存不足：Linux 哲学是"闲着的内存不如做缓存"。永远以 `avail Mem` 为准，而非 `free`。

## 1\.8 常见问题

- **常见性能问题速查**

    |    症状表现|    命令输出特征|    问题定性|    下一步排查方向|
    |---|---|---|---|
    |    应用卡顿，CPU `us` 高|    `us` \> 80%，`wa` \< 5%|    计算密集或死循环|    `strace`/`perf` 抓取 CPU 热点函数，检查算法复杂度|
    |    应用响应慢，CPU `wa` 高|    `wa` \> 20%，`iostat` 的 `%util` \> 90%|    磁盘 I/O 瓶颈|    检查是否在写大量日志、数据库是否缺索引、是否使用 Swap|
    |    内存监控持续上升不回落|    `top` 中 `RES` 持续增长；GC 后内存不降|    内存泄漏|    导出 Heap Dump，用 MAT 分析 GC Root 引用链|
    |    系统偶尔卡死，之后恢复|    `free -h` 看到 `Swap used` 从 0 开始增长|    物理内存不足，触发 Swap|    增加物理内存，或优化应用内存占用（减少缓存、池化对象）|
    |    CPU 高，但 `pidstat` 看不出异常|    `top` 的 `sy`（内核态）占比很高|    系统调用频繁或上下文切换多|    用 `vmstat 1` 看 `cs`（上下文切换）和 `in`（中断），排查锁竞争|
    |    数据库连接池满，但 SQL 不快|    `iostat` 的 `await` 偏高，`top` 正常|    磁盘随机读写延迟高|    检查磁盘类型（是否 SSD），优化数据库缓冲区大小|

- **CPU 爆满，但 wa 很低**

    - 现象：`us` 飙升到 90%，`wa` 接近 0%。

    - 推理：纯计算或死循环。使用 `top` 找到 PID 后，用 `strace -p <PID>` 或 `jstack`（Java）抓取线程栈，看代码卡在哪个函数。

    - 举例：一个排序算法复杂度退化，数据量翻倍时 CPU 瞬间打满。

- **查看指定 Java 进程的线程数**

    **`top -H -p <PID>`**

    ```Shell
    top -H -p <PID>
    
    -H：显示线程视图
    -p <PID>：指定进程 ID
    输出中每一行代表一个线程，可直观看到线程数和 CPU 占用情况
    ```

    **`ps -eLf | grep <PID>`**

    ```Shell
    ps -eLf | grep <PID> | wc -l
    
    -eLf：列出所有线程（LWP）
    wc -l：统计行数即为线程数
    ```

    **`/proc/<PID>/task`**

    ```Shell
    ls /proc/<PID>/task | wc -l
    
    /proc/<PID>/task 目录下每个子目录代表一个线程
    此方法最直接、最准确，适合脚本自动化
    ```

    **💡建议操作**

    1. 先定位 Java 进程 PID：

    ```Shell
    *jps -l | grep xxl*
    ```

    2. 快速统计线程数：

    ```Shell
    ls /proc/<PID>/task | wc -l
    ```

    3. 结合 CPU 使用率分析：

    ```Shell
    top -H -p <PID>
    ```

    按 `P` 键按 CPU 排序，找出最耗资源的线程

    4. 导出线程快照用于深度分析：

    ```Shell
    jstack <PID> > /tmp/jstack_$(date +%s).log
    ```

    > 如果你发现线程数异常高（如超过 500），且大量处于 `RUNNABLE` 状态，说明应用可能陷入死循环、频繁 GC 或外部调用阻塞，需结合 `jstack` 堆栈进一步定位具体代码行。
    > 
    > 

- **线程问题排查方法**

    ```Shell
    *# 1. 找到执行器 Java 进程 PID*
    jps -l | grep xxl
    
    *# 2. 抓线程快照，看线程都在干什么*
    jstack <pid> > /tmp/jstack.log
    
    *# 3. 查看线程状态分布*
    grep "java.lang.Thread.State" /tmp/jstack.log | sort | uniq -c | sort -rn
    ```

    重点关注：

    - 是否有大量线程处于 `WAITING` 或 `BLOCKED` 状态

    - 是否有线程卡在数据库连接、HTTP 调用等外部依赖上

    - 搜索 `tariffCommodityAuditJob` 关键字，看这个任务是否卡住了

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux系统监控-内存]]
- [[Linux系统监控-磁盘]]

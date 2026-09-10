---
type: note
tags: [Linux] [环境搭建] [进程]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 进程管理

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-进程管理 小节

Linux 进程管理核心遵循“先查后控”原则：通过 ps/top/htop/pstree 定位进程，使用 kill/pkill/killall 控制生命周期，借助 nohup/jobs/fg/bg 管理前后台作业，并利用 nice/renice 调整优先级。

## **7\.1 进程基础概念**

进程是程序的一次执行实例，拥有独立的内存空间、PID（进程 ID）和状态。Linux 作为多任务操作系统，通过内核的进程管理机制实现高效调度。

进程常见状态（ps 输出中的 STAT 列）：

|状态|含义|
|---|---|
|R|Running/Runnable，运行中或就绪|
|S|Interruptible Sleep，可中断睡眠（等待 I/O）|
|D|Uninterruptible Sleep，不可中断睡眠（等待硬件）|
|T|Stopped，被信号暂停|
|Z|Zombie，僵尸进程|

## **7\.2 核心命令详解**

### **7\.2\.1 ps \- 查看进程快照（最常用）**

`ps` 是定位进程的首选命令，输出系统当前进程的"快照"。

```Shell
*# 查看所有进程（BSD 风格，含 CPU/内存占用）*
ps aux

*# 查看所有进程（UNIX 风格，含父子关系）*
ps -ef

*# 查找特定进程*
ps aux | grep nginx

*# 按 CPU 使用率降序排序*
ps aux --sort=-%cpu

*# 查看某个用户的进程*
ps -u alice

*# 自定义输出列*
ps -o pid,comm,%cpu,%mem

*# 用 ps 直接查看线程数*
ps -T -p <PID> | wc -l
*# 注意：输出结果需要减 1（减去表头行）*

# 查出指定进程并kill
ps aux | grep 关键字 | grep -v grep | awk '{print $2}' | xargs kill -9
```

输出字段解读（ps aux）：

- PID：进程 ID（唯一标识）

- %CPU / %MEM：CPU 和内存占用率

- VSZ：虚拟内存大小

- RSS：物理内存常驻集

- STAT：进程状态

- COMMAND：启动命令

### **7\.2\.2 top / htop \- 实时监控进程**

`top` 实时动态监控进程资源占用，服务器卡顿时必用，默认每 3 秒刷新。

```Shell
top              *# 启动实时监控*
top -p 1234      *# 只监控指定 PID*
top -n 1 -b | head -n 15  *# 非交互模式，取前 10 进程*
```

交互快捷键：

- `P`：按 CPU 排序

- `M`：按内存排序

- `k`：输入 PID 终止进程

- `r`：调整进程优先级

- `q`：退出

> `htop` 是 `top` 的增强版，界面更友好，支持鼠标操作和彩色显示，需手动安装（`apt install htop` 或 `yum install htop`）。
> 
> 

### **7\.2\.3 pstree \- 树形查看进程关系**

以树形结构展示进程间的父子关系，排查衍生进程时非常直观。

```Shell
pstree              *# 查看进程树*
pstree -p           *# 同时显示 PID*
pstree -p | grep nginx  *# 过滤特定进程*
```

### **7\.2\.4 pgrep / pidof \- 快速查找 PID**

无需通过 `ps | grep` 过滤，直接按进程名获取 PID。

```Shell
pgrep nginx          *# 返回 nginx 所有进程的 PID*
pgrep -l nginx       *# 同时显示进程名和 PID*
pidof sshd           *# 返回 sshd 的 PID*
```

### **7\.2\.5 kill / pkill / killall \- 终止进程**

通过向进程发送信号来控制进程行为。

```Shell
*# 按 PID 终止（默认发送 SIGTERM，友好终止）*
kill 1234

*# 强制终止（SIGKILL，不可被捕获）*
kill -9 1234

*# 按真实进程名批量终止*
pkill nginx
killall java
pkill -f 'script_start.sh'  # -f 参数的作用，“不要去匹配真实的进程名，去匹配完整命令行”

*# 暂停和恢复进程*
kill -STOP 1234      *# 暂停进程*
kill -CONT 1234      *# 恢复进程*
```

**常用信号：**

|信号|编号|含义|
|---|---|---|
|SIGHUP|1|挂断（终端关闭时发送）|
|SIGINT|2|中断（Ctrl\+C）|
|SIGTERM|15|正常终止（默认）|
|SIGKILL|9|强制终止（不可忽略）|
|SIGSTOP|17|暂停进程|
|SIGCONT|19|继续进程|

> ⚠️ 优先使用普通 `kill`（SIGTERM），让进程有机会清理资源；`kill -9` 可能导致数据丢失，仅在进程无响应时使用。
> 
> 

### **7\.2\.6 nice / renice \- 调整进程优先级**

Linux 进程优先级通过 nice 值控制，范围 \-20（最高）到 19（最低），默认为 0。

```Shell
*# 启动时设置低优先级*
nice -n 10 ./test.sh

*# 调整运行中进程的优先级*
renice 10 -p 1234

*# 查看进程优先级*
ps -p 1234 -o ni
```

> 普通用户只能设置 0\~19，root 可设置 \-20\~\-1。
> 
> 

### **7\.2\.7 jobs / fg / bg \- 作业控制**

管理当前终端的前后台进程。

```Shell
*# 后台运行命令（命令后加 &）*
sleep 1000 &

*# 查看当前终端的后台作业*
jobs
jobs -l          *# 显示 PID*

*# 暂停前台进程（Ctrl+Z）→ 进入 Stopped 状态*
*# 恢复后台运行*
bg %1

*# 调回前台运行*
fg %1
```

### **7\.2\.8 nohup \- 脱离终端运行**

让进程忽略 SIGHUP 信号，即使关闭终端也不会终止。

```Shell
*# 推荐写法：后台运行 + 输出重定向*
nohup ./app.sh > app.log **2**>**&1** &

nohup (No Hang Up):不挂断地运行命令。
2>&1:将标准错误重定向到标准输出。
1 代表标准输出（stdout）
2 代表标准错误（stderr）
&1 表示“引用标准输出的目标位置”（注意 & 不能省略，否则会被当成普通文件名）。
```

## **7\.3 实战场景详解**

**场景 1：服务器变卡，如何定位"资源小偷"？**

```Plain Text
*# 第一步：启动 top，按 P 键按 CPU 排序*
top

*# 第二步：记录高占用进程的 PID（如 5678）*
*# 第三步：查看该进程详情*
ps -p 5678 -o pid,user,%cpu,%mem,comm

*# 第四步：根据情况处理*
*# 如果是正常但低优先级的任务，降低优先级*
renice 10 -p 5678

*# 如果是异常进程，强制终止*
kill -9 5678
```

**场景 2：脚本关闭终端后就消失？**

```Plain Text
*# 错误做法：关闭终端后进程被终止*
./long_task.sh &

*# 正确做法：使用 nohup 脱离终端*
nohup ./long_task.sh > output.log **2**>**&1** &

*# 或使用 screen 终端复用器*
screen -S mytask
./long_task.sh
*# 按 Ctrl+A 再按 D 分离会话*
*# 重新连接：screen -r mytask*
```

**场景 3：出现僵尸进程（Z）怎么处理？**

僵尸进程是已终止但父进程未回收其资源的子进程，无法通过 kill 命令清除。

```Plain Text
*# 第一步：找到僵尸进程*
ps aux | grep Z

*# 第二步：查看其 PPID（父进程 PID）*
ps -o ppid= -p <僵尸进程PID>

*# 第三步：终止父进程（僵尸进程会被 init/systemd 接管并清理）*
kill -9 <父进程PID>

*# 注意：如果父进程是核心服务，优先重启服务而非直接 kill*
systemctl restart <服务名>
```

**场景 4：安全重启服务**

```Plain Text
*# 推荐方式：使用 systemctl*
systemctl restart nginx

*# 不推荐：直接 kill 再启动（可能丢数据）*
killall nginx && nginx
```

**场景 5：前后台作业完整操作流**

```Plain Text
*# 1. 前台运行一个长时间任务*
./study.sh

*# 2. 按 Ctrl+Z 暂停 → [1]+ 已停止  ./study.sh*
*# 3. 查看作业列表*
jobs -l
*# 输出：[1]+  12345 已停止  ./study.sh*

*# 4. 让它在后台继续运行*
bg %1

*# 5. 需要时调回前台*
fg %1

*# 6. 终止后台作业*
kill %1
```

## **7\.4 命令速查表**

|命令|作用|典型示例|
|---|---|---|
|ps aux|查看所有进程快照|ps aux \-\-sort=\-%mem|
|top / htop|实时监控进程资源|top \-p 1234|
|pstree|查看进程树|pstree \-p|
|pgrep / pidof|按名字找 PID|pgrep \-f nginx|
|kill / pkill|发送信号/终止进程|kill \-9 1234|
|nice / renice|调整调度优先级|renice \-5 \-p 1234|
|jobs / fg / bg|作业控制|Ctrl\+Z 挂起，bg 转后台|
|nohup|脱离终端运行|nohup \./app \> app\.log 2\>\&1 \&|
|cat /proc/\<pid\>/status|查看进程内核信息|cat /proc/1/status|

## **7\.5 避坑提醒**

- 禁止乱杀进程：PID=1 的 init/systemd 进程绝不能动，杀前务必用 `ps` 确认进程详情。

- 优先使用 systemctl：nginx、mysql 等系统服务，用 `systemctl restart 服务名` 比 `kill` 更安全。

- kill \-9 是最后手段：优先使用默认的 SIGTERM（15），让进程有机会清理资源。

- pkill 需谨慎：`pkill java` 会终止所有 java 进程，建议先用 `pgrep` 验证匹配结果。

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux用户权限管理]]
- [[Linux常用操作命令]]

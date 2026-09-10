---
type: note
tags: [Linux] [环境搭建] [网络]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 系统监控：网络

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-网络 小节

## 4\.1 ss

功能说明：

- **ss **是 **netstat **的现代替代工具，属于 iproute2 套件。它的执行速度更快，且能直接从内核获取更详细的信息。

- 常用命令：

```Shell
*ss -tulnp | grep 端口号*
# 仅查看 TCP 监听端口：ss -tlnp

-t：显示 TCP 协议的端口。
-u：显示 UDP 协议的端口。
-l：仅显示正在监听（Listening）状态的端口。
-n：不进行域名和服务名解析，直接显示数字形式的 IP 和端口（速度更快）。
-p：显示占用该端口的进程名和 PID（注意：必须加 sudo 才能看到进程信息）。
```

- 输出示例：

```Shell
Netid  State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process*
*tcp    LISTEN  0       128     0.0.0.0:22          0.0.0.0:*          users:(("sshd",pid=1234,fd=3))*
*tcp    LISTEN  0       128     0.0.0.0:80          0.0.0.0:*          users:(("nginx",pid=5678,fd=6))


*Netid（网络类型）：表示套接字使用的网络协议类型。在您的示例中，tcp 代表使用的是 TCP 协议。其他常见的类型还包括 udp（UDP协议）和 unix（Unix域套接字）等。*

*State（连接状态）：表示当前套接字的运行状态。示例中的 LISTEN 表示该端口正处于监听状态，正在等待来自客户端的连接请求。其他常见状态还包括 ESTABLISHED（已建立连接）、TIME-WAIT 等。*

*Recv-Q（接收队列）：表示当前接收队列中尚未被应用程序读取的字节数。如果该值持续不为 0，通常意味着应用程序处理数据的速度落后于网络接收数据的速度。*

*Send-Q（发送队列）：表示当前发送队列中尚未被远端确认（ACK）的字节数。如果该值持续不为 0，通常意味着网络拥塞或远端处理数据缓慢。*

*Local Address:Port（本地地址与端口）：表示本地服务器正在监听的 IP 地址和端口号。示例中的 0.0.0.0:22 和 0.0.0.0:80 分别表示服务器在所有网络接口上监听 22 端口（SSH服务）和 80 端口（HTTP服务）。*

*Peer Address:Port（对端地址与端口）：表示与本地建立连接的远端 IP 地址和端口号。对于处于 LISTEN（监听）状态的端口，该列通常显示为 *:*，表示尚未有具体的客户端与其建立连接。*

*Process（进程信息）：表示占用该套接字的进程详细信息。示例中 users:(("sshd",pid=1234,fd=3)) 表示该连接由名为 sshd 的进程管理，其进程 ID（PID）为 1234，使用的文件描述符（fd）为 3。需要注意的是，查看此信息通常需要 root 权限。*
```

## 4\.2 netstat

功能说明：

- netstat 属于老旧的 net\-tools 工具包，性能和效率不如 ss。

- 常用命令：

```Shell
*netstat -tulnp | grep 端口号*

-t：TCP 协议。
-u：UDP 协议。
-l：仅显示监听状态的套接字。
-n：拒绝显示别名，直接显示数字形式的地址和端口。
-p：显示建立相关连接的程序名和 PID。
```

## 4\.3 lsof

功能说明：

- lsof（List Open Files）通过读取内核的文件描述符来工作，在排查端口占用时非常精准，尤其适合查找某个特定端口被哪个进程占用。

- 常用命令：

```Shell
*lsof -i :端口号 -P -n*
*lsof -i :端口号*
# 仅查看处于监听状态的 TCP 端口：lsof -iTCP -sTCP:LISTEN -P -n

-i：列出符合条件的网络连接。
-P：禁止将端口号转换为端口名（如把 80 转为 http）。
-n：禁止将 IP 地址转换为主机名（避免 DNS 解析卡顿）。
```

## 4\.4 ping

功能说明：

- `ping` 命令虽然基础，但其参数组合是精准诊断网络延迟、丢包和 MTU 问题的核心手段。

- 核心延迟检测参数：

|参数|作用|延迟检测意义|示例|
|---|---|---|---|
|`-c <count>`|指定发送数据包数量|避免无限 ping，获取统计样本|`ping -c 50 8.8.8.8`|
|`-i <interval>`|设置发包间隔（秒）<br>|模拟真实业务频率，避免触发限速|`ping -i 0.1 -c 100 target`|
|`-s <size>`|自定义 ICMP 载荷大小|测试大包延迟（MTU/分片影响）|`ping -s 1472 -M do target`|
|`-D`|显示时间戳|关联延迟波动与具体时间点|`ping -D -c 20 target`|
|`-q`|静默模式，仅输出摘要|脚本中快速获取 min/avg/max/mdev|`ping -q -c 100 target`|
|`-W <timeout>`|等待响应超时（秒）|区分“高延迟”与“完全不可达”|`ping -W 2 -c 10 target`|
|`-m <mark>`|标记数据包（SO\_MARK）|配合 tc/qdisc 测试特定队列延迟|`ping -m 100 target`|

> **⚠️ ****关键注意****：****`-i`**** 参数小于 0\.2 秒时通常需要 root 权限；普通用户最小间隔为 0\.2s。**
> 
> 

- **延迟分析关键指标解读**

执行 `ping -c 100 target` 后，关注以下统计行：

```Shell
ping -c 100 10.1.203.70

*PING 10.1.203.70 (10.1.203.70) 56(84) bytes of data.
64 bytes from 10.1.203.70: icmp_seq=1 ttl=63 time=0.348 ms
64 bytes from 10.1.203.70: icmp_seq=2 ttl=63 time=3.94 ms
64 bytes from 10.1.203.70: icmp_seq=3 ttl=63 time=4.43 ms
64 bytes from 10.1.203.70: icmp_seq=4 ttl=63 time=0.262 ms
64 bytes from 10.1.203.70: icmp_seq=5 ttl=63 time=0.293 ms
64 bytes from 10.1.203.70: icmp_seq=6 ttl=63 time=0.779 ms
64 bytes from 10.1.203.70: icmp_seq=7 ttl=63 time=0.347 ms
64 bytes from 10.1.203.70: icmp_seq=8 ttl=63 time=0.300 ms
64 bytes from 10.1.203.70: icmp_seq=9 ttl=63 time=0.234 ms
64 bytes from 10.1.203.70: icmp_seq=10 ttl=63 time=0.229 ms
64 bytes from 10.1.203.70: icmp_seq=11 ttl=63 time=0.328 ms
64 bytes from 10.1.203.70: icmp_seq=12 ttl=63 time=0.308 ms
64 bytes from 10.1.203.70: icmp_seq=13 ttl=63 time=0.253 ms
--- 10.1.203.70 ping statistics ---
13 packets transmitted, 13 received, 0% packet loss, time 12220ms
****rtt min/avg/max/mdev = 0.229/0.926/4.426/1.397 ms***
```

- min：最佳路径延迟，反映物理距离和设备处理基线。

- avg：平均延迟，业务体验的直接参考值。

- max：最差延迟，暴露网络抖动或拥塞峰值。

- mdev \(Mean Deviation\)：延迟抖动指标，比 avg 更重要！

    - mdev \< 1ms：极稳定（局域网/专线）

    - mdev 1\~10ms：正常公网

    - mdev \> 20ms：严重抖动，需排查 QoS/拥塞/设备负载

---

- **实战场景**

**精准测量生产环境延迟**

```Shell
# 模拟 API 调用频率（每100ms一次），持续10秒，带时间戳
sudo ping -i 0.1 -c 100 -D api.example.com
*适用*：验证 SLA 承诺、对比不同时段延迟基线。

# 先用 IP 测纯网络延迟
ping -c 20 1.1.1.1
# 再用域名测（含 DNS 解析时间）
ping -c 20 example.com
*判断*：若域名 ping 首包延迟显著高于 IP → DNS 解析慢，非网络问题。
```

- **延迟正常范围参考表**

|场景|优秀|正常|需关注|严重异常|关键说明|
|---|---|---|---|---|---|
|局域网 \(LAN\)|\< 1ms|1\-5ms|5\-20ms|\> 20ms|交换机/路由器故障或广播风暴|
|同地域云服务器|\< 2ms|2\-10ms|10\-30ms|\> 30ms|VPC 内通信应接近 LAN 水平|
|国内跨运营商|\< 30ms|30\-80ms|80\-150ms|\> 150ms|电信↔联通/移动互联常见瓶颈|
|国内跨省公网|\< 40ms|40\-100ms|100\-200ms<br>|\> 200ms|地理距离\+路由跳数影响显著|
|跨境\(亚太\)|\< 100ms|100\-200ms|200\-300ms|\> 300ms|新加坡/日本到中国典型值|
|跨境\(欧美\)|\< 180ms|180\-280ms|280\-400ms|\> 400ms|物理距离决定下限\(光速限制\)|
|实时音视频|\< 100ms|100\-200ms|200\-300ms|\> 300ms|\>200ms 明显卡顿，\>300ms 无法对话|
|在线游戏\(FPS/MOBA\)|\< 30ms|30\-60ms|60\-100ms|\> 100ms|\>80ms 操作延迟感强烈|
|Web/API 服务|\< 50ms|50\-150ms|150\-300ms|\> 300ms|含 DNS/TLS/后端处理总耗时|

**⚠️ 比绝对值更重要的指标：抖动**

- 抖动 = max \- min 或 mdev：即使平均延迟 50ms，若 mdev \> 20ms，体验远差于平均 80ms 但 mdev \< 2ms 的网络。

- 业务容忍度：视频通话可接受 200ms 延迟但要求抖动 \< 30ms；文件传输对抖动不敏感但受高延迟影响吞吐。

**🔍 判断延迟是否正常的实操步骤**

- 建立基线：在业务低峰期用 `ping -c 100 -i 0.2 target` 采集基准数据。

- 对比参照物：

    - 同机房服务器互 ping \< 1ms → 你的服务器到目标 \> 10ms 则异常。

    - 用户本地 ping 网关 \< 5ms → ping 你的服务 \> 100ms 则问题在服务端/骨干网。

- 排除干扰项：

    - 首包延迟高后续正常 → DNS 解析慢（用 IP 直连验证）。

    - 周期性延迟尖峰 → 定时任务/备份作业抢占带宽。

    - 仅特定源 IP 延迟高 → 运营商路由策略或 ACL 限制。

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux系统监控-内存]]
- [[Linux常用操作命令]]

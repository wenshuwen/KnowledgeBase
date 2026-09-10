---
type: note
tags: [Nginx] [环境搭建] [反向代理]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Nginx 安装与配置

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 中间件章-Nginx 小节（安装部署，内容较长）

Nginx 是由俄罗斯工程师 Igor Sysoev 开发的开源 Web 服务器软件，最初发布于2004年。其设计初衷是为了解决传统 Web 服务器面临的 C10K 问题（单机处理一万个并发连接），采用异步非阻塞事件驱动架构，专为实现高并发、低资源消耗而设计。官方测试可支持5万个并发连接，实际生产环境能稳定承载2\-3万个并发连接。

Nginx 不仅可作为基础 HTTP 服务器托管静态资源，还集成了反向代理、负载均衡、邮件代理（IMAP/POP3/SMTP）、HTTP 缓存等功能。根据 W3Techs 数据，截至2023年，Nginx 在全球 Web 服务器市场份额占比超过35%。

## **🛠️ 安装部署**

Nginx 的安装方式主要有包管理器安装和源码编译安装两种，以下分别介绍。

### 包管理器安装（推荐）

Ubuntu/Debian 系统：

```Bash
*# 1. 更新软件包索引*
sudo apt update && sudo apt upgrade -y

*# 2. 安装 Nginx*
sudo apt install nginx -y

*# 3. 启动并设置开机自启*
sudo systemctl start nginx
sudo systemctl enable nginx

*# 4. 配置防火墙（允许 HTTP 和 HTTPS）*
sudo ufw allow 'Nginx Full'

*# 5. 验证安装*
nginx -v
sudo systemctl status nginx
```

CentOS/RHEL 系统：

```Bash
*# 1. 安装 EPEL 仓库*
sudo yum install epel-release -y

*# 2. 安装 Nginx*
sudo yum install nginx -y

*# 3. 启动并设置开机自启*
sudo systemctl start nginx
sudo systemctl enable nginx

*# 4. 配置防火墙*
sudo firewall-cmd --zone=public --permanent --add-service=http
sudo firewall-cmd --zone=public --permanent --add-service=https
sudo firewall-cmd --reload
```

### 源码编译安装

源码编译安装可以自定义模块和编译参数，适合需要定制化的场景：

```Bash
*# 1. 安装依赖*
sudo yum install -y pcre-devel zlib-devel gcc gcc-c++ make openssl-devel

*# 2. 创建专用用户*
sudo useradd -m -s /sbin/nologin nginx

*# 3. 下载并解压源码*
cd /usr/local/src
wget http://nginx.org/download/nginx-1.24.0.tar.gz
tar zxvf nginx-1.24.0.tar.gz
cd nginx-1.24.0

*# 4. 配置编译选项*
./configure \
  --prefix=/usr/local/nginx \
  --user=nginx \
  --group=nginx \
  --with-http_ssl_module \
  --with-http_stub_status_module \
  --with-pcre

*# 5. 编译安装*
make && make install

*# 6. 启动*
/usr/local/nginx/sbin/nginx
```

### 关键目录结构

|路径|说明|
|---|---|
|/etc/nginx/nginx\.conf|主配置文件|
|/etc/nginx/sites\-available/|可用站点配置（Ubuntu）|
|/etc/nginx/conf\.d/|配置片段目录（CentOS）|
|/var/www/html/|默认网页根目录|
|/var/log/nginx/access\.log|访问日志|
|/var/log/nginx/error\.log|错误日志|

### 常用运维命令

```Bash
nginx -t              *# 测试配置文件语法*
systemctl reload nginx  *# 平滑重载配置（不中断服务）*
systemctl restart nginx *# 重启服务*
nginx -s stop         *# 快速停止*
nginx -s quit         *# 优雅停止（处理完当前请求后退出）*
```

---

## ⚙️ 实现原理

Nginx 的高性能源于其独特的架构设计，核心可以概括为多进程模型 \+ 异步非阻塞事件驱动。

### Master\-Worker 进程模型

Nginx 启动后会创建两类进程：

- Master 进程（管理者）：以 root 权限运行，负责读取并验证配置文件、管理 Worker 进程的生命周期（启动/停止/重启）、接收外部信号（如 reload、stop）、监控 Worker 进程状态并在异常退出时自动重启。Master 进程不直接处理用户请求。

- Worker 进程（执行者）：由 Master fork 而来，数量通常配置为与 CPU 核心数一致。每个 Worker 进程彼此独立，通过竞争机制获取新连接，采用异步非阻塞方式处理请求。一个 Worker 崩溃不会影响其他 Worker，Master 会自动拉起新的 Worker 进程。

---

### 异步非阻塞事件驱动

这是 Nginx 高性能的核心所在。每个 Worker 进程内部运行一个事件循环，利用操作系统提供的高效 I/O 多路复用机制（Linux 下为 epoll，FreeBSD 下为 kqueue）来同时监听大量连接上的事件。

与传统 Apache 的"一连接一线程/进程"模型不同，Nginx 的单个 Worker 可以通过一个线程同时管理数万个连接：

- 非阻塞：当 Worker 执行 I/O 操作（如读取请求、发送响应）时，如果操作未完成，不会阻塞等待，而是立即返回继续处理其他事件。

- 事件驱动：Worker 通过 epoll 监听所有连接上的可读/可写事件，只有当事件就绪时才进行相应处理，避免了 CPU 空转。

---

### 请求处理流程

一个完整的 HTTP 请求在 Nginx 中的处理流程如下：

- 建立连接：客户端通过 TCP 三次握手与 Nginx 建立连接，Worker 进程通过 accept 获取连接。

- 接收请求：Worker 读取并解析 HTTP 请求（请求方法、URI、请求头等）。

- 匹配规则：根据 `server` 块（虚拟主机）和 `location` 块（路径匹配）确定处理方式。

- 处理请求：

    - 静态资源 → 直接从磁盘读取文件返回（利用 `sendfile` 零拷贝技术，跳过用户态与内核态的数据拷贝）。

    - 动态请求 → 通过 `proxy_pass` 转发到后端应用服务器（如 Tomcat、Node\.js、PHP\-FPM）。

- 返回响应：组装 HTTP 响应报文发送给客户端，可按需进行 gzip 压缩。

- 连接管理：根据 `keepalive` 配置决定是否保持长连接复用。

---

### 模块化架构

Nginx 的功能通过模块化体系实现，主要包括：

- 事件模块（event module）：封装操作系统的事件处理机制（epoll/kqueue）。

- Handler 模块：处理客户端请求并生成响应内容（如静态文件模块、FastCGI 模块）。

- Filter 模块：对输出内容进行加工处理（如 gzip 压缩、Header 修改）。

- Upstream 模块：实现反向代理功能，将请求转发到后端服务器。

- Load\-balancer 模块：实现负载均衡算法（轮询、加权轮询、IP 哈希、最少连接等）。

---

## 🧭 核心参数配置

主配置文件通常位于 `/etc/nginx/nginx.conf`，采用层级嵌套的块状结构，从外到内依次为：全局块 → events 块 → http 块 → server 块 → location 块。每个层级的指令作用范围不同，上层配置会被下层继承。下面逐层拆解核心参数。

### 📐 配置文件整体结构

```Bash
*# ========== 全局块（Main Context）==========*
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;
worker_rlimit_nofile 65535;

*# ========== events 块 ==========*
events {
    worker_connections 10240;
    use epoll;
    multi_accept on;
}

*# ========== http 块 ==========*
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;

    *# ---------- server 块（虚拟主机）----------*
    server {
        listen 80;
        server_name example.com;
        root /var/www/html;

        *# ------ location 块（路径匹配）------*
        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
```

---

#### **全局块（Main Context）**

> 全局块位于配置文件最外层，不属于任何 `{}` 块内，控制 Nginx 进程的整体运行行为。
> 
> ###### 1\.1 user
> 
> ```Bash
> user nginx;
> *# 或指定用户和组*
> user nginx nginx;
> ```
> 
> - 作用：指定 Worker 进程运行时所使用的系统用户和用户组。
> 
> - 原理：Master 进程以 root 启动（需要绑定 80/443 等特权端口），但 Worker 进程应降权运行，避免安全漏洞导致系统被完全控制。
> 
> - 注意：该用户的权限需与网站根目录、日志目录的读写权限匹配，否则会出现 `403 Forbidden` 或日志写入失败。
> 
> ---
> 
> ###### 1\.2 worker\_processes
> 
> ```Bash
> worker_processes auto;
> *# 或手动指定*
> worker_processes 4;
> ```
> 
> - 作用：设置 Worker 进程的数量，直接决定 Nginx 的并发处理能力上限。
> 
> - 原理：每个 Worker 进程独立处理连接，进程数过少无法利用多核 CPU，过多则导致上下文切换开销增大。
> 
> - 推荐值：`auto`（自动检测 CPU 逻辑核心数）是最佳选择。也可通过 `nproc` 或 `grep processor /proc/cpuinfo | wc -l` 查看核心数后手动设置。
> 
> ---
> 
> ###### 1\.3 worker\_cpu\_affinity
> 
> ```Bash
> *# 自动绑定（Nginx 1.9.10+）*
> worker_cpu_affinity auto;
> 
> *# 手动绑定（4核CPU示例）*
> worker_cpu_affinity 0001 0010 0100 1000;
> ```
> 
> - 作用：将每个 Worker 进程绑定到指定的 CPU 核心，避免进程在多核间频繁迁移导致 CPU 缓存失效。
> 
> - 原理：每个 CPU 核心有自己的 L1/L2 缓存，进程迁移后缓存命中率下降，绑定后可提升缓存局部性。
> 
> - 效果：实测数据显示，4 核服务器上绑定后 QPS 提升约 15%。
> 
> ---
> 
> ###### 1\.4 worker\_rlimit\_nofile
> 
> ```Bash
> worker_rlimit_nofile 65535;
> ```
> 
> - 作用：设置单个 Worker 进程能打开的最大文件描述符数量。
> 
> - 原理：在 Linux 中，每个网络连接占用一个文件描述符（FD），默认系统限制为 1024，高并发时远远不够。
> 
> - 配套操作：需同步修改系统级限制，否则此配置无效：
> 
> ```Bash
> *# /etc/security/limits.conf*
> nginx soft nofile 65535
> nginx hard nofile 65535
> ```
> 
> - 计算关系：建议设置为 `worker_connections` 的 1\~1\.5 倍，因为除了连接，还需要额外的 FD 用于日志文件、upstream 连接等。
> 
> ---
> 
> ###### 1\.5 error\_log
> 
> ```Bash
> error_log /var/log/nginx/error.log warn;
> ```
> 
> - 作用：定义全局错误日志的路径和记录级别。
> 
> - 日志级别（从低到高）：`debug` → `info` → `notice` → `warn` → `error` → `crit` → `alert` → `emerg`
> 
> - 推荐：生产环境使用 `warn` 或 `error`，`debug` 级别会产生海量日志，严重消耗磁盘 I/O。
> 
> ###### 1\.6 pid
> 
> ```Bash
> pid /run/nginx.pid;
> ```
> 
> - 作用：指定存储 Master 进程 PID 的文件路径。`nginx -s stop`、`nginx -s reload` 等信号命令依赖此文件定位主进程。
> 
> ---
> 
> ###### 1\.7 include（全局）
> 
> ```Bash
> include /usr/share/nginx/modules/*.conf;
> ```
> 
> - 作用：引入外部配置文件，实现配置模块化。常用于加载动态模块或拆分虚拟主机配置。
> 
> ---
> 
> 

#### **events 块**

> events 块控制 Nginx 的网络连接处理模型，直接影响并发连接能力。
> 
> ###### 2\.1 worker\_connections
> 
> ```Bash
> events {
>     worker_connections 10240;
> }
> ```
> 
> - 作用：定义每个 Worker 进程能同时处理的最大连接数。
> 
> - 计算公式：`理论最大并发连接数 = worker_processes × worker_connections`
> 
> - 示例：4 个 Worker × 10240 连接 = 40960 并发连接。
> 
> - 注意：该值不能超过 `worker_rlimit_nofile` 的设置，且需确保系统 `ulimit -n` 值大于该值。
> 
> ---
> 
> ###### 2\.2 use
> 
> ```Bash
> events {
>     use epoll;   *# Linux 2.6+*
>     *# use kqueue;  # FreeBSD*
> }
> ```
> 
> - 作用：指定事件驱动模型（I/O 多路复用机制）。
> 
> - 推荐：
> 
>     - Linux 2\.6\+ → `epoll`（最高效）
> 
>     - FreeBSD → `kqueue`
> 
>     - 通常 Nginx 会自动选择最优模型，无需手动指定。
> 
> - 原理：`epoll` 采用事件回调机制，只处理活跃连接，时间复杂度 O\(1\)；而 `select`/`poll` 需要遍历所有连接，连接数超过 1024 时性能急剧下降。
> 
> ###### 2\.3 multi\_accept
> 
> ```Bash
> events {
>     multi_accept on;
> }
> ```
> 
> - 作用：控制 Worker 进程是否在一次事件通知中批量接受所有新到达的连接。
> 
> - 默认值：`off`（每次只接受一个新连接）。
> 
> - 推荐：设为 `on`，高并发连接涌入时可减少 `accept()` 系统调用次数，提升吞吐量。实测连接建立速度提升约 40%。
> 
> ---
> 
> ###### 2\.4 accept\_mutex
> 
> ```Bash
> events {
>     accept_mutex off;
> }
> ```
> 
> - 作用：控制是否启用"惊群保护"。设为 `on` 时，同一时刻只有一个 Worker 被唤醒去接受新连接；设为 `off` 时，所有 Worker 都会被唤醒竞争。
> 
> - 权衡：
> 
>     - `on`：避免惊群效应，减少不必要的上下文切换，但可能略微降低连接分配速度。
> 
>     - `off`：提升吞吐量，但会增加 CPU 上下文切换开销。
> 
> - 推荐：Nginx 1\.11\.3\+ 版本中，`accept_mutex` 默认已改为 `off`，因为现代 Linux 内核的 `EPOLLEXCLUSIVE` 标志已能较好解决惊群问题。
> 
> ---
> 
> 

#### **http 块**

> http 块是 Nginx 配置中最复杂、最核心的部分，涵盖 HTTP 协议处理、代理、缓存、压缩等几乎所有 Web 功能。http 块内可嵌套多个 `server` 块。
> 
> ###### 3\.1 基础传输优化
> 
> ###### 3\.1\.1 sendfile
> 
> ```Bash
> sendfile on;
> ```
> 
> - 作用：启用内核级零拷贝文件传输。
> 
> - 原理：传统文件传输需要 4 次数据拷贝（磁盘 → 内核缓冲区 → 用户缓冲区 → Socket 缓冲区 → 网卡），`sendfile` 将流程简化为 2 次（磁盘 → 内核缓冲区 → 网卡），跳过用户态拷贝，可降低 CPU 占用 30% 以上。
> 
> ---
> 
> ###### 3\.1\.2 tcp\_nopush
> 
> ```Bash
> tcp_nopush on;
> ```
> 
> - 作用：在 `sendfile` 开启时生效，将响应头和文件内容合并到一个 TCP 包中发送，减少网络包数量。
> 
> - 原理：利用 Linux 的 `TCP_CORK` 选项，攒够数据再发送，适合大文件传输。
> 
> ---
> 
> ###### 3\.1\.3 tcp\_nodelay
> 
> ```Bash
> tcp_nodelay on;
> ```
> 
> - 作用：禁用 Nagle 算法，在 keepalive 连接空闲时立即发送小数据包，降低延迟。
> 
> - 原理：Nagle 算法会将多个小包合并发送以减少网络开销，但对于交互式应用（如 WebSocket、API 调用），延迟比带宽更重要。
> 
> - 搭配：`tcp_nopush` 和 `tcp_nodelay` 同时开启时，Nginx 会在发送大文件时使用 `tcp_nopush` 攒包，发送完毕后自动关闭 `TCP_CORK` 并启用 `tcp_nodelay` 立即发送剩余数据，两者互补。
> 
> ---
> 
> ###### 3\.2 连接保持与超时
> 
> ###### 3\.2\.1 keepalive\_timeout
> 
> ```Bash
> keepalive_timeout 65;
> ```
> 
> - 作用：设置客户端 keepalive 长连接的超时时间（秒）。超时后服务端主动关闭连接。
> 
> - 推荐值：
> 
>     - API 网关/短连接场景：30\~65 秒
> 
>     - 静态资源/长连接场景：65\~120 秒
> 
>     - WebSocket：300 秒以上
> 
> - 设为 0：禁用 keepalive，每次请求都重新建立 TCP 连接（不推荐）。
> 
> ---
> 
> ###### 3\.2\.2 keepalive\_requests
> 
> ```Bash
> keepalive_requests 1000;
> ```
> 
> - 作用：单个 keepalive 连接上允许处理的最大请求数，达到上限后关闭连接。
> 
> - 推荐值：500\~2000。过小会导致频繁建连，过大会导致单个连接占用过久。
> 
> ---
> 
> ###### 3\.2\.3 client\_header\_timeout
> 
> ```Bash
> client_header_timeout 15s;
> ```
> 
> - 作用：读取客户端请求头的超时时间。超时未读完则返回 `408 Request Timeout`。
> 
> - 安全意义：防止慢速攻击（Slowloris）——恶意客户端缓慢发送请求头，长期占用连接资源。
> 
> ---
> 
> ###### 3\.2\.4 client\_body\_timeout
> 
> ```Bash
> client_body_timeout 15s;
> ```
> 
> - 作用：读取客户端请求体的超时时间。适用于 POST 请求。
> 
> ---
> 
> ###### 3\.2\.5 send\_timeout
> 
> ```Bash
> send_timeout 15s;
> ```
> 
> - 作用：向客户端发送响应的超时时间。指两次连续写操作之间的间隔，而非整个响应的发送时间。
> 
> ---
> 
> ###### 3\.3 缓冲区配置
> 
> ```Bash
> *# 客户端请求头缓冲区*
> client_header_buffer_size 4k;
> large_client_header_buffers 8 16k;
> 
> *# 客户端请求体缓冲区*
> client_body_buffer_size 128k;
> 
> *# 请求体最大限制（上传文件大小上限）*
> client_max_body_size 100m;
> 
> *# 代理缓冲区*
> proxy_buffer_size 4k;
> proxy_buffers 8 4k;
> proxy_busy_buffers_size 8k;
> ```
> 
> - client\_header\_buffer\_size：读取请求头的初始缓冲区大小。大多数请求头不超过 1k\~4k。
> 
> - large\_client\_header\_buffers：当请求头（含 Cookie）超过初始缓冲区时使用的备用缓冲区。数量和大小格式为 `数量 大小`。如果请求行超出此限制，返回 `414 URI Too Long`。
> 
> - client\_body\_buffer\_size：请求体在内存中的缓冲区大小。如果请求体超过此值，Nginx 会将数据写入临时文件。
> 
> - client\_max\_body\_size：允许客户端请求体的最大字节数。超出则返回 `413 Request Entity Too Large`。文件上传场景需适当调大。
> 
> ---
> 
> ###### 3\.4 Gzip 压缩
> 
> ```Bash
> gzip on;                          *# 启用 gzip*
> gzip_min_length 1k;               *# 小于 1k 的内容不压缩（压缩收益低）*
> gzip_comp_level 6;                *# 压缩级别 1-9（6 为性能与压缩率的平衡点）*
> gzip_vary on;                     *# 添加 Vary: Accept-Encoding 头（CDN 缓存兼容）*
> gzip_proxied any;                 *# 对所有代理请求也进行压缩*
> gzip_buffers 16 8k;               *# 压缩缓冲区：16 个 8k*
> gzip_http_version 1.1;            *# 识别 HTTP 协议的版本*
> gzip_types                        *# 需要压缩的 MIME 类型*
>     text/plain
>     text/css
>     text/xml
>     text/javascript
>     application/json
>     application/javascript
>     application/xml
>     application/xml+rss
>     image/svg+xml;
> ```
> 
> - 原理：Gzip 对文本类资源（HTML/CSS/JS/JSON）压缩率可达 60%\~90%，大幅减少传输体积。
> 
> - 注意：图片（JPG/PNG）、视频等已是压缩格式的文件不需要再 gzip，加入反而浪费 CPU。
> 
> ---
> 
> ###### 3\.5 日志配置
> 
> ```Bash
> *# 自定义日志格式*
> log_format main '$remote_addr - $remote_user [$time_local] "$request" '
>                 '$status $body_bytes_sent "$http_referer" '
>                 '"$http_user_agent" "$http_x_forwarded_for" '
>                 '$request_time $upstream_response_time';
> 
> *# 引用日志格式*
> access_log /var/log/nginx/access.log main;
> 
> *# 带缓冲的日志写入（减少磁盘 I/O）*
> access_log /var/log/nginx/access.log main buffer=32k flush=5s;
> ```
> 
> - 常用变量：
> 
>     - `$remote_addr`：客户端 IP
> 
>     - `$request_time`：Nginx 处理请求的总耗时（秒，精确到毫秒）
> 
>     - `$upstream_response_time`：后端服务器响应时间
> 
>     - `$status`：HTTP 响应状态码
> 
>     - `$body_bytes_sent`：发送给客户端的响应体大小
> 
> - 推荐：生产环境务必在日志中包含 `$request_time` 和 `$upstream_response_time`，便于定位慢请求。
> 
> ---
> 
> ###### 3\.6 MIME 类型与默认类型
> 
> ```Bash
> include /etc/nginx/mime.types;
> default_type application/octet-stream;
> ```
> 
> - include mime\.types：引入文件扩展名与 MIME 类型的映射表，确保 Nginx 能正确设置 `Content-Type` 响应头。
> 
> - default\_type：当文件扩展名无法匹配时使用默认类型。`application/octet-stream` 表示二进制流，浏览器会触发下载而非直接展示。
> 
> ---
> 
> ###### 3\.7 文件缓存
> 
> ```Bash
> open_file_cache max=100000 inactive=20s;
> open_file_cache_valid 30s;
> open_file_cache_min_uses 2;
> open_file_cache_errors on;
> ```
> 
> - 作用：缓存文件的元数据（文件大小、修改时间、目录信息等），避免频繁调用 `stat()` 系统调用。
> 
> - 参数说明：
> 
>     - `max=100000`：缓存中最多存放 10 万个文件条目
> 
>     - `inactive=20s`：20 秒内未被访问的条目自动清除
> 
>     - `valid=30s`：每 30 秒重新验证缓存条目的有效性
> 
>     - `min_uses=2`：在 inactive 时间内至少被访问 2 次才保留在缓存中
> 
>     - `errors=on`：也缓存文件不存在的错误信息，避免重复查找
> 
> - 效果：高并发静态文件服务中可减少大量系统调用开销。
> 
> ---
> 
> 

#### **server 块（虚拟主机）**

> 每个 `server` 块定义一个虚拟主机，一个 `http` 块内可以包含多个 `server` 块，实现一台服务器托管多个网站。
> 
> ###### 4\.1 listen
> 
> ```Bash
> listen 80;
> listen 443 ssl http2;
> listen 8080 default_server;
> ```
> 
> - 作用：指定该虚拟主机监听的 IP 地址和端口。
> 
> - 常用参数：
> 
>     - `default_server`：标记为默认虚拟主机，当请求的域名不匹配任何 `server_name` 时，由该 server 处理。
> 
>     - `ssl`：启用 HTTPS。
> 
>     - `http2`：启用 HTTP/2 协议（需配合 SSL）。
> 
> ---
> 
> ###### 4\.2 server\_name
> 
> ```Bash
> *# 精确匹配*
> server_name example.com;
> 
> *# 通配符匹配*
> server_name *.example.com;
> server_name www.example.*;
> 
> *# 正则匹配*
> server_name ~^www\d+\.example\.com$;
> ```
> 
> - 匹配优先级（从高到低）：
> 
>     - 精确匹配（如 `www.example.com`）
> 
>     - 前缀通配符（如 `*.example.com`）
> 
>     - 后缀通配符（如 `www.example.*`）
> 
>     - 正则表达式匹配（按配置文件中的顺序）
> 
>     - 兜底到 `default_server` 或第一个 server 块
> 
> ---
> 
> ###### 4\.3 root 与 alias
> 
> ```Bash
> *# root：将 location 路径追加到 root 后面*
> root /var/www/html;
> location /images/ {
>     *# 请求 /images/logo.png → /var/www/html/images/logo.png*
> }
> 
> *# alias：用 alias 路径替换 location 路径*
> location /images/ {
>     alias /data/static/pics/;
>     *# 请求 /images/logo.png → /data/static/pics/logo.png*
> }
> ```
> 
> - 核心区别：`root` 是拼接，`alias` 是替换。使用 `alias` 时 location 路径必须以 `/` 结尾。
> 
> ---
> 
> ###### 4\.4 index
> 
> ```Bash
> index index.html index.htm index.php;
> ```
> 
> - 作用：当请求以 `/` 结尾时，Nginx 按顺序尝试返回这些默认文件。
> 
> ---
> 
> ###### 4\.5 SSL/TLS 配置
> 
> ```Bash
> ssl_certificate     /etc/ssl/certs/example.com.pem;
> ssl_certificate_key /etc/ssl/private/example.com.key;
> 
> *# 仅允许安全协议版本*
> ssl_protocols TLSv1.2 TLSv1.3;
> 
> *# 加密套件（优先使用 ECDHE 前向保密套件）*
> ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
> ssl_prefer_server_ciphers on;
> 
> *# SSL 会话缓存（减少重复握手）*
> ssl_session_cache shared:SSL:50m;
> ssl_session_timeout 1d;
> ssl_session_tickets off;
> 
> *# OCSP Stapling（加速证书验证）*
> ssl_stapling on;
> ssl_stapling_verify on;
> ```
> 
> - 推荐：禁用 TLSv1\.0/1\.1（存在已知漏洞），仅保留 TLSv1\.2 和 TLSv1\.3。
> 
> ---
> 
> 

#### **location 块（路径匹配）**

> location 块是 Nginx 最灵活的配置单元，通过 URL 路径匹配来决定如何处理请求。
> 
> ###### 5\.1 匹配语法
> 
> ```Bash
> *# 精确匹配：请求 URI 必须完全等于 /exact*
> location = /exact { ... }
> 
> *# 前缀匹配：请求 URI 以 /images/ 开头*
> location /images/ { ... }
> 
> *# 前缀匹配（优先级最高，匹配后不再查找正则）*
> location ^~ /static/ { ... }
> 
> *# 正则匹配（区分大小写）*
> location ~ \.(jpg|png|gif)$ { ... }
> 
> *# 正则匹配（不区分大小写）*
> location ~* \.(jpg|png|gif)$ { ... }
> ```
> 
> ---
> 
> ###### 5\.2 匹配优先级（从高到低）
> 
> 1. `=` 精确匹配（命中后立即处理，不再查找其他 location）
> 
> 2. `^~` 前缀匹配（命中后不再查找正则 location）
> 
> 3. `~` / `~*` 正则匹配（按配置文件中的顺序，第一个命中的生效）
> 
> 4. 普通前缀匹配（取最长匹配，但如果有正则匹配则被正则覆盖）
> 
> ---
> 
> ###### 5\.3 try\_files
> 
> ```Bash
> location / {
>     try_files $uri $uri/ /index.html;
> }
> ```
> 
> - 作用：按顺序检查文件是否存在，返回第一个找到的文件。全部找不到则返回最后一个参数指定的 URI（或状态码）。
> 
> - 典型用途：前端 SPA（Vue/React）部署，所有路径回退到 `index.html`，由前端路由接管。
> 
> ---
> 
> ###### 5\.4 反向代理
> 
> ```Bash
> location /api/ {
>     proxy_pass http://127.0.0.1:8080;
>     proxy_set_header Host $host;
>     proxy_set_header X-Real-IP $remote_addr;
>     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
>     proxy_set_header X-Forwarded-Proto $scheme;
>     proxy_http_version 1.1;
>     proxy_set_header Connection "";
> }
> ```
> 
> - proxy\_pass：将请求转发到后端服务器。注意末尾有无 `/` 的区别：
> 
>     - `proxy_pass http://backend;`（无 `/`）：原始 URI 完整传递
> 
>     - `proxy_pass http://backend/;`（有 `/`）：去掉 location 匹配部分后传递
> 
> - proxy\_set\_header：设置转发给后端的请求头，传递客户端真实信息。
> 
> - Connection ""：配合 `proxy_http_version 1.1` 启用与后端的长连接复用。
> 
> ---
> 
> ###### 5\.5 代理超时
> 
> ```Bash
> proxy_connect_timeout 5s;    *# 与后端建立连接的超时*
> proxy_send_timeout 60s;      *# 向后端发送请求的超时*
> proxy_read_timeout 60s;      *# 从后端读取响应的超时*
> ```
> 
> ---
> 
> 

#### **upstream 块（负载均衡）**

> upstream 块定义后端服务器集群，配合 `proxy_pass` 实现负载均衡。
> 
> ###### 6\.1 负载均衡
> 
> ```Bash
> upstream backend {
>     *# 负载均衡算法*
>     *# 默认轮询（round-robin）*
>     *# ip_hash;              # 基于客户端 IP 哈希（会话保持）*
>     *# least_conn;           # 最少连接数优先*
> 
>     *# 后端服务器*
>     server 192.168.1.10:8080 weight=3 max_fails=3 fail_timeout=30s;
>     server 192.168.1.11:8080 weight=2 max_fails=3 fail_timeout=30s;
>     server 192.168.1.12:8080 backup;   *# 备用节点（主节点全部宕机时启用）*
>     server 192.168.1.13:8080 down;     *# 标记为离线（不参与负载）*
> 
>     *# 到后端的长连接池*
>     keepalive 32;
>     keepalive_requests 100;
>     keepalive_timeout 60s;
> }
> ```
> 
> - weight：权重值，数值越大分配的请求越多。
> 
> - max\_fails：在 `fail_timeout` 时间窗口内允许的最大失败次数，超过后标记为不可用。
> 
> - fail\_timeout：时间窗口，也是节点被标记不可用后的"冷却时间"。
> 
> - keepalive：保持到后端服务器的长连接数量，减少反复建连开销。
> 
> ---
> 
> ###### 6\.2 故障转移
> 
> ```Bash
> location / {
>     proxy_pass http://backend;
>     proxy_next_upstream error timeout http_502 http_503;
> }
> ```
> 
> - proxy\_next\_upstream：定义在哪些情况下将请求转发到下一个后端服务器。
> 
> ---
> 
> 

#### **安全与限流配置**

#### 7\.1 访问控制

```Bash
location /admin/ {
    allow 192.168.1.0/24;    *# 允许内网*
    deny all;                 *# 拒绝其他所有 IP*
}
```

---

#### 7\.2 请求限流（漏桶算法）

```Bash
*# 定义限流区域：每个客户端 IP 每秒 10 个请求*
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
    }
}
```

- rate：允许的请求速率。

- burst：突发请求的缓冲队列大小。

- nodelay：突发请求不排队，直接处理（消耗 burst 配额）。

---

#### 7\.3 连接数限制

```Bash
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    location / {
        limit_conn conn_limit 50;    *# 每个 IP 最多 50 个并发连接*
    }
}
```

---

#### 7\.4 安全响应头

```Bash
add_header X-Frame-Options "SAMEORIGIN";          *# 防点击劫持*
add_header X-Content-Type-Options "nosniff";       *# 禁止 MIME 嗅探*
add_header X-XSS-Protection "1; mode=block";      *# XSS 过滤*
add_header Content-Security-Policy "default-src 'self'";  *# CSP*
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;  *# HSTS*
```

---

#### 7\.5 隐藏版本号

```Bash
server_tokens off;
```

- 作用：隐藏 Nginx 版本号，避免攻击者针对特定版本漏洞发起攻击。

---

#### **完整生产环境配置示例**

将以上参数整合为一份可直接参考的生产配置：

```Bash
*# ==================== 全局块 ====================*
user nginx;
worker_processes auto;
worker_cpu_affinity auto;
worker_rlimit_nofile 65535;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;

*# ==================== events 块 ====================*
events {
    worker_connections 10240;
    use epoll;
    multi_accept on;
}

*# ==================== http 块 ====================*
http {
    *# 基础设置*
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    server_tokens off;

    *# 日志格式*
    log_format main '$remote_addr - [$time_local] "$request" '
                    '$status $body_bytes_sent '
                    '$request_time $upstream_response_time';
    access_log /var/log/nginx/access.log main buffer=32k flush=5s;

    *# 传输优化*
    sendfile    on;
    tcp_nopush  on;
    tcp_nodelay on;

    *# 连接保持*
    keepalive_timeout   65;
    keepalive_requests  1000;

    *# 超时控制*
    client_header_timeout 15s;
    client_body_timeout   15s;
    send_timeout          15s;

    *# 缓冲区*
    client_header_buffer_size  4k;
    large_client_header_buffers 8 16k;
    client_body_buffer_size    128k;
    client_max_body_size       100m;

    *# Gzip 压缩*
    gzip on;
    gzip_min_length 1k;
    gzip_comp_level 6;
    gzip_vary on;
    gzip_types text/plain text/css application/json
               application/javascript text/xml application/xml
               image/svg+xml;

    *# 文件缓存*
    open_file_cache max=100000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;

    *# 限流区域*
    limit_req_zone $binary_remote_addr zone=global_rate:10m rate=30r/s;

    *# 引入虚拟主机配置*
    include /etc/nginx/conf.d/*.conf;

    *# ==================== 默认 server ====================*
    server {
        listen 80 default_server;
        server_name _;
        return 301 https://$host$request_uri;
    }

    *# ==================== 主站点 ====================*
    server {
        listen 443 ssl http2;
        server_name example.com;

        *# SSL*
        ssl_certificate     /etc/ssl/certs/example.com.pem;
        ssl_certificate_key /etc/ssl/private/example.com.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:50m;
        ssl_session_timeout 1d;

        *# 安全头*
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Strict-Transport-Security "max-age=31536000" always;

        root /var/www/html;
        index index.html;

        *# 限流*
        limit_req zone=global_rate burst=50 nodelay;

        *# 前端 SPA 路由*
        location / {
            try_files $uri $uri/ /index.html;
        }

        *# 静态资源缓存*
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2|svg)$ {
            expires 30d;
            access_log off;
            add_header Cache-Control "public, immutable";
        }

        *# API 反向代理*
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_connect_timeout 5s;
            proxy_read_timeout 60s;
        }
    }
}

*# ==================== upstream 块 ====================*
upstream backend {
    server 127.0.0.1:3000 weight=3 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:3001 weight=2 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:3002 backup;
    keepalive 32;
}
```

---

### 📌 配置管理最佳实践

|操作|命令|
|---|---|
|语法检查|nginx \-t|
|平滑重载|systemctl reload nginx 或 nginx \-s reload|
|优雅停止|nginx \-s quit|
|快速停止|nginx \-s stop|

- 修改配置前：先 `cp nginx.conf nginx.conf.bak` 备份。

- 修改后：先 `nginx -t` 验证语法，再 `reload` 生效。

- 模块化：将不同虚拟主机拆分到 `/etc/nginx/conf.d/` 目录下的独立文件，通过 `include` 引入，便于维护。

- 版本管理：建议将 `/etc/nginx/` 目录纳入 Git 管理，记录每次配置变更。

> 📌 总结：Nginx 配置的核心思路是——全局块管进程、events 块管连接、http 块管协议、server 块管域名、location 块管路径。理解这个层级关系后，任何配置需求都能快速定位到对应的配置块。参数调优应遵循"先内核 → 再进程模型 → 再缓冲区 → 再应用层"的优先级顺序，逐层调整并观察效果，避免盲目堆砌参数。
> 
> 

---

## ✅ 优势与劣势

> **优势**
> 
> 

- 高并发处理能力：采用异步非阻塞事件驱动架构，单机可轻松支撑数万甚至 5 万并发连接，而 Apache 在同等条件下可能因进程/线程过多导致资源耗尽。

- 轻量级，资源占用少：相比 Apache，Nginx 处理相同请求量时内存和 CPU 消耗显著更低，启动速度快，非常适合资源有限的服务器环境。

- 强大的反向代理与负载均衡：原生支持反向代理和多种负载均衡算法（轮询、加权、IP 哈希、最少连接等），并支持健康检查和故障自动转移。

- 静态资源处理高效：利用 `sendfile` 零拷贝和 `gzip` 压缩，静态文件处理性能约为 Apache 的 3 倍。

- 配置简洁灵活：配置文件结构清晰，语法简洁，支持 `nginx -t` 预检测配置语法，避免重启时因配置错误导致服务中断。

- 零停机更新：通过 `reload` 信号实现配置热加载，Master 会启动新 Worker 并优雅关闭旧 Worker，整个过程不中断服务。

- 高稳定性：Worker 进程彼此隔离，单个 Worker 异常不影响整体服务，Master 会自动重启异常退出的 Worker。

---

> **劣势**
> 
> 

- 动态内容处理需依赖外部：Nginx 本身不直接处理 PHP、Python 等动态脚本，需要通过 FastCGI（如 PHP\-FPM）等方式转发给后端处理，增加了架构复杂度。

- 模块扩展需重新编译：添加或更新第三方模块通常需要重新编译 Nginx，不像 Apache 那样可以通过配置文件直接启用/禁用模块。

- 不支持 \.htaccess：Nginx 没有 Apache 的 `.htaccess` 机制，所有配置必须集中在主配置文件中，对于需要目录级别独立配置的场景灵活性稍差。

- 后端健康检查有限：开源版的后端健康检查仅支持端口检测，不支持 URL 级别的深度健康检查（商业版 Nginx Plus 支持）。

- 学习曲线：虽然配置语法简洁，但对于新手来说，理解事件驱动模型、location 匹配规则等概念仍需一定学习成本。

---

## 🌐 应用场景示例

### 场景一：静态资源服务器

Nginx 最擅长的场景之一。直接托管 HTML、CSS、JS、图片等静态文件，配合 `sendfile` 和 `gzip` 实现高效传输。

```Bash
server {
    listen 80;
    server_name static.example.com;
    root /var/www/static;

    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;          *# 浏览器缓存30天*
        access_log off;       *# 关闭静态资源日志减少IO*
    }
}
```

### 场景二：反向代理 \+ 动态应用

将 Nginx 作为前端入口，将动态请求代理到后端应用服务器（如 Node\.js、Java、Python），同时 Nginx 处理 SSL 终止和静态资源。

```Bash
server {
    listen 443 ssl;
    server_name app.example.com;

    ssl_certificate     /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    *# 静态资源由 Nginx 直接处理*
    location /static/ {
        alias /var/www/app/static/;
    }

    *# 动态请求代理到后端*
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 场景三：负载均衡集群

将流量分发到多台后端服务器，实现高可用和水平扩展。

```Bash
upstream backend {
    *# 加权轮询：性能好的服务器分配更多流量*
    server 192.168.1.10:8080 weight=3;
    server 192.168.1.11:8080 weight=2;
    server 192.168.1.12:8080 backup;  *# 备用节点*

    *# 健康检查参数*
    *# max_fails=2 表示连续失败2次后标记为不可用*
    *# fail_timeout=30s 表示30秒内不再分配请求*
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://backend;
    }
}
```

### 场景四：前端 SPA 应用部署（Vue/React）

单页面应用的所有路由都由前端 JavaScript 处理，需要将所有路径回退到 `index.html`。

```Bash
server {
    listen 80;
    server_name spa.example.com;
    root /var/www/spa/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;  *# 关键：所有路径回退到index.html*
    }
}
```

### 场景五：缓存加速服务器

Nginx 可以作为反向代理缓存服务器，缓存后端响应以减少后端压力、加速用户访问。

```Bash
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g;

server {
    location / {
        proxy_pass http://backend;
        proxy_cache my_cache;
        proxy_cache_valid 200 60m;  *# 200响应缓存60分钟*
    }
}
```

### 场景六：API 网关与限流

利用 `limit_req` 模块基于漏桶算法控制请求速率，防止后端被突发流量压垮。

```Bash
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://api_backend;
    }
}
```

---

> 📌 总结：Nginx 凭借事件驱动 \+ 异步非阻塞的架构设计，在高并发、低资源消耗方面表现卓越，是现代 Web 架构中不可或缺的基础组件。它最适合作为反向代理、负载均衡器和静态资源服务器使用；对于动态内容处理，通常需要搭配后端应用服务器（如 PHP\-FPM、Tomcat、Node\.js）协同工作。在实际生产中，Nginx 常被部署在架构的最前端，充当"流量入口"和"安全屏障"的角色。
> 
> 

---

## 相关笔记
- [[08-环境搭建]]
- [[Redis使用指南]]
- [[Linux用户权限管理]]

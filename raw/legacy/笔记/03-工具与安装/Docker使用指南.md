---
type: note
tags: [环境搭建] [容器化] [工具]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Docker 使用指南

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 测试工具章-Docker 小节

## **6\.1 核心概念与原理**

> **什么是 Docker？**
> 
> 

Docker 是一个开源的应用容器引擎。基于 Go 语言开发实现，遵从 Apache 2\.0 协议。它允许开发者将应用及其依赖包打包到一个轻量级、可移植的“容器”中，然后发布到任何支持 Docker 的环境（Linux/Windows/macOS）中运行。

Docker 的核心理念是 “Build, Ship and Run Any App, Anywhere” ——即“构建、分发、运行任何应用，在任何地方”。通过镜像技术将应用程序及其运行环境完整打包，实现 “一次镜像，处处运行” 。

---

> **核心概念**
> 
> 

- 镜像 \(Image\)：只读模板，包含运行应用所需的一切（代码、运行时、库、环境变量）。类似于面向对象编程中的“类”。

- 容器 \(Container\)：镜像的运行实例。容器之间相互隔离，拥有独立的文件系统、网络和进程空间。类似于“对象”。

- 仓库 \(Repository\)：集中存放镜像的地方，如 Docker Hub、阿里云 ACR、Harbor 等。类似于 Git 仓库或 Maven 仓库。

- Dockerfile：是一个文本文件，包含了一系列指令，用于自动化构建镜像。通过 Dockerfile，开发者可以精确地定义应用的运行环境。

- 工作流程：开发人员通过 Dockerfile 定义应用环境 → 构建成 Image（镜像） → 推送到 Registry（仓库） → 运维人员拉取 Image 并运行成 Container（容器） 。

---

> **底层原理**
> 
> 

Docker 并非虚拟机，它直接复用宿主机内核，主要依赖 Linux 内核的三大技术：

- **Namespace（命名空间）**：实现资源隔离。包括 PID（进程）、NET（网络）、MNT（挂载点）、UTS（主机名）、IPC（信号量）、USER（用户）6种隔离，让容器以为自己在一个独立的系统中运行。

> *一句话概括：容器本质上是宿主机上的普通进程，只是被内核“骗”成了以为自己独占整台机器*
> 
> 

- **Cgroups（控制组）**：实现资源限制。限制容器能使用的 CPU、内存、磁盘 I/O 等资源上限，防止单个容器耗尽宿主机资源。

- **UnionFS（联合文件系统）**：实现分层存储。Docker 镜像由多层只读层叠加而成，容器启动时在最上层加一个可写层（Copy\-on\-Write 机制），极大节省了存储空间并提升了启动速度。多个容器可以共享相同的基础镜像层，节省存储空间；构建镜像时可以复用缓存层，加速构建过程。

> *⚠️ Docker vs 虚拟机*
> *虚拟机通过 Hypervisor 模拟硬件，每个 VM 都有完整 OS，启动慢（分钟级）、占用大（GB级）；Docker 共享宿主内核，启动快（秒级）、占用小（MB级），但隔离性弱于 VM。*
> 
> 

---

## **6\.2 安装部署指南**

### **Linux 环境（生产环境推荐）**

**CentOS / RHEL / Alibaba Cloud Linux:**

```Shell
*# 1. 卸载旧版本*
sudo yum remove docker docker-client docker-client-latest docker-common \
    docker-latest docker-latest-logrotate docker-logrotate docker-engine

*# 2. 安装依赖 & 添加官方源（国内推荐阿里云镜像源加速）*
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

*# 3. 安装 Docker CE*
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

*# 4. 启动并设置开机自启*
sudo systemctl start docker
sudo systemctl enable docker

*# 5. 验证*
docker version
```

**Ubuntu / Debian:**

```Shell
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 安装依赖包
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置稳定版仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker引擎
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证安装
sudo docker run hello-world    # 输出 "Hello from Docker!" 表示安装成功

# 便携式安装方式
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### macOS / Windows（开发环境）

直接下载 Docker Desktop 安装包即可：

- 官网：[https://www\.docker\.com/products/docker\-desktop/](https://www.docker.com/products/docker-desktop/)

- 安装后自动配置好 Docker Engine \+ Docker CLI \+ Docker Compose。

### ⭐ 配置镜像加速器（国内必做）

由于网络原因，拉取镜像可能超时，建议配置加速器：

```Shell
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com"
  ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

> *💡 提示：2024年以来国内镜像源变动频繁，如上述地址失效，可搜索“docker proxy 加速”获取最新可用源，或使用自建代理。*
> 
> 

---

## **6\.3 操作使用指南**

### Docker服务管理（Linux）

```Shell
*# 启动 Docker 服务*
sudo systemctl start docker

*# 停止 Docker 服务*
sudo systemctl stop docker

*# 重启 Docker 服务*
sudo systemctl restart docker

*# 查看运行状态*
sudo systemctl status docker

*# 设置开机自启*
sudo systemctl enable docker

*# 查看引擎信息*
docker info
```

### 镜像管理

```Shell
*# 搜索镜像*
docker search nginx

*# 拉取镜像（指定标签）*
docker pull nginx:1.25-alpine

*# 查看本地镜像*
docker images

*# 删除镜像*
docker rmi nginx:1.25-alpine

*# 构建自定义镜像*
docker build -t myapp:v1.0 .

*# 推送镜像到仓库*
docker tag myapp:v1.0 registry.example.com/myapp:v1.0
docker push registry.example.com/myapp:v1.0

# 导出镜像
docker save -o myapp.tar myapp:1.0    # 保存为 tar 文件

# 导入镜像
docker load -i myapp.tar
```

### 容器生命周期管理

```Shell
*# 运行容器（最常用命令）*
docker run -d \                    *# 后台运行*
  --name my-nginx \                *# 容器名称*
  -p 8080:80 \                     *# 端口映射 宿主机:容器*
  -v /data/html:/usr/share/nginx/html \  *# 目录挂载*
  -e TZ=Asia/Shanghai \            *# 环境变量*
  --restart=always \               *# 重启策略*
  nginx:1.25-alpine

*# 查看运行中的容器*
docker ps
docker ps -a                       *# 查看所有（含已停止）*

*# 进入容器内部-终端*
docker exec -it my-nginx /bin/sh

*# 停止 / 启动 / 重启 / 删除*
docker stop my-nginx
docker start my-nginx
docker restart my-nginx
docker rm my-nginx                 *# 删除已停止容器*
docker rm -f my-nginx              *# 强制删除运行中容器*

# 查看资源占用
docker stats    # 实时 CPU/内存监控
```

### 日志与调试

```Shell
*# 查看实时日志*
docker logs -f --tail 100 my-nginx

*# 查看容器详细信息（IP、挂载、配置等）*
docker inspect my-nginx

*# 查看容器资源占用*
docker stats my-nginx

*# 复制文件*
docker cp my-nginx:/var/log/nginx/access.log ./access.log
docker cp ./index.html my-nginx:/usr/share/nginx/html/
```

### 网络管理

```Shell
*# 查看网络列表*
docker network ls

*# 创建自定义网络*
docker network create --driver bridge mynet

*# 将容器连接到网络*
docker run -d --name app --network mynet myapp
```

### Docker Compose（多容器编排）

Docker Compose 是 Docker 官方提供的多容器编排工具。它的核心作用是：用一个 YAML 文件定义多个容器的配置、网络和依赖关系，一条命令同时启动/停止/管理它们。对于多服务应用，使用 `docker-compose.yml` 声明式管理：

```YAML
version: '3.8'
services:
  web:
    image: nginx:1.25-alpine
    ports:
      - "8080:80"
    volumes:
      - ./html:/usr/share/nginx/html
    depends_on:
      - api
  api:
    build: ./api
    environment:
      - DB_HOST=db
    restart: always
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
    volumes:
      - db_data:/var/lib/mysql
volumes:
  db_data:
```

操作命令：

```Shell
docker compose up -d       *# 启动所有服务*
docker compose down        *# 停止并删除*
docker compose logs -f     *# 查看所有服务日志*
docker compose ps          *# 查看服务状态*
```

---

## **6\.4 最佳实践与安全建议**

|类别|建议|
|---|---|
|镜像瘦身|使用 Alpine/Slime 基础镜像；多阶段构建；合并 RUN 指令减少层数|
|安全|不以 root 运行容器（USER appuser）；定期扫描漏洞（docker scout）；不使用 \-\-privileged|
|数据持久化|始终使用 Volume 或 Bind Mount，不要将数据写入容器可写层|
|日志管理|配置日志驱动和大小限制，避免磁盘爆满：\-\-log\-opt max\-size=10m \-\-log\-opt max\-file=3|
|网络|使用自定义 bridge 网络而非默认 default 网络，便于服务发现和隔离|
|CI/CD|镜像打语义化 Tag，禁止在生产中使用 latest 标签|

---

## **6\.5 学习路线建议**

- 入门：掌握本文上述命令，能独立部署 Nginx/MySQL/Redis

- 进阶：编写优化 Dockerfile、Docker Compose 编排、网络/存储深入理解

- 高级：Kubernetes 容器编排、CI/CD 流水线集成、容器安全加固、性能调优

- 认证：DCA（Docker Certified Associate）→ CKA（Certified Kubernetes Administrator）

---

## 相关笔记
- [[03-工具与安装]]
- [[Fiddler抓包工具]]
- [[Nmon监控工具]]

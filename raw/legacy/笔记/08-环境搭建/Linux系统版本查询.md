---
type: note
tags: [Linux] [环境搭建]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 系统版本与发行版

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-系统版本 小节

## **5\.1 查看 Linux 发行版版本**

- **通用方法（推荐）**

    - `cat /etc/os-release`：适用于绝大多数现代 Linux 发行版，可以显示发行版的名称、版本号等详细信息。

    - `lsb_release -a`：适用于所有 Linux 发行版，能列出所有版本信息（包括发行商、版本号、代号等）。如果提示命令未找到，可能需要安装 `redhat-lsb` 包。

    - `cat /etc/issue`：同样适用于所有 Linux 发行版，在系统登录前通常会显示此文件的内容，其中包含版本信息。

    - `hostnamectl`：显示系统的详细信息，包括操作系统版本、内核版本和系统架构等。

- **针对特定发行版的方法**

    - Red Hat / CentOS / Fedora 系列：使用 `cat /etc/redhat-release`。

    - Arch Linux：使用 `cat /etc/arch-release`。

## **5\.2 查看 Linux 内核版本**

- `uname -r`：仅显示当前的内核版本号。

- `uname -a`：显示所有系统信息，包括内核版本、系统名称、硬件架构等。

- `cat /proc/version`：显示详细的内核版本信息，包括编译时间、GCC 版本等。

## **5\.3 Linux 发行版（Distro）**

> **Debian / Ubuntu 系（以用户友好和生态丰富著称）**
> 
> 

- Debian：历史最悠久、社区驱动的发行版之一，以极高的稳定性和安全性著称，是许多其他发行版（如 Ubuntu）的基础，非常适合用作服务器基础镜像。

- Ubuntu：基于 Debian 优化而来，提供友好的图形界面和长期支持（LTS）版本，拥有庞大的社区和完善的文档，是目前最适合初学者、开发者以及企业应用的首选。

- Linux Mint：基于 Ubuntu，强化了多媒体支持，其传统桌面布局非常贴近 Windows 的操作习惯，是 Windows 用户迁移的绝佳选择。

> **Red Hat 系（企业级解决方案与服务器首选）**
> 
> 

- Red Hat Enterprise Linux \(RHEL\)：付费的商业发行版，提供 7×24 小时官方技术支持，以高稳定性和安全性广泛应用于金融、电信等关键业务领域。

- Rocky Linux / AlmaLinux：作为原 CentOS 的免费替代品，它们与 RHEL 二进制兼容，提供长达 10 年的支持周期，是中小型企业服务器和云部署的理想选择。

- Fedora：Red Hat 的上游开发版，追求最新技术（如 Wayland 显示协议），适合希望体验前沿技术的开发者和技术爱好者。

> **SUSE 系（工业级可靠性与强大管理工具）**
> 
> 

- SUSE Linux Enterprise Server \(SLES\)：支持大型关键业务系统，提供实时内核和高可用性集群解决方案，在宝马、大众等车企的生产线控制系统中广泛使用。

- openSUSE：SUSE 的社区版，提供滚动更新和稳定版本，其特色在于拥有强大的 YaST 图形化配置工具，能一站式管理系统设置。

> **极客与高级用户定制系**
> 
> 

- Arch Linux：采用滚动更新模式，用户可自由选择安装组件，搭配 AUR（Arch 用户仓库）获取海量软件包，适合追求极致定制化和最新软件的高级用户。

- Gentoo：基于源码编译安装，支持细粒度的编译参数优化，可针对特定 CPU 架构榨取最高性能，适合技术专家和高性能计算场景。

> **国产主流发行版（自主可控与本土化适配）**
> 
> 

- 银河麒麟：在党政军领域应用广泛，深度适配国产 CPU（如飞腾、鲲鹏等），安全等级高。

- 统信 UOS：界面美观、易用性强，能够满足日常办公与国产替代的需求。

- openEuler：由华为开源，面向数字基础设施和云原生场景深度优化，支持多样性计算。

> **专用领域发行版**
> 
> 

- Kali Linux / Parrot OS：预装大量渗透测试、数字取证和安全攻防工具，是网络安全人员的首选。

- Ubuntu Studio：专为内容创作者和多媒体内容制作者优化，提供音视频编辑等工具链。

## **5\.4 识别版本方式**

> **最通用标准：查看 ****`/etc/os-release`**** 文件**
> 
> 

这是现代 Linux（Systemd 时代）最标准、最通用的识别方式，几乎所有主流发行版都提供此文件。

- 执行命令：`cat /etc/os-release`

- 如何区分：重点关注 `ID` 和 `ID_LIKE` 字段。

    - 看到 `ID=ubuntu` 或 `ID_LIKE=debian`，即为 Debian/Ubuntu 系。

    - 看到 `ID=centos` 或 `ID_LIKE="rhel fedora"`，即为 Red Hat 系（注：Rocky Linux 会显示 `ID="rocky"`，Oracle Linux 显示 `ID="ol"`）。

    - 看到 `ID=arch`，即为 Arch Linux。

    - 看到 `ID=opensuse`，即为 SUSE 系。

> **快捷识别：检查发行版专属文件**
> 
> 

不同发行版在 `/etc/` 目录下通常会留下专属的版本标识文件，通过检查这些文件可以快速区分系列：

- Debian / Ubuntu 系：`cat /etc/debian_version`

- Red Hat / CentOS 系：`cat /etc/redhat-release` 或 `cat /etc/centos-release`

- Fedora 系：`cat /etc/fedora-release`

- SUSE 系：`cat /etc/SuSE-release`

- Arch Linux：`test -f /etc/arch-release && echo "Arch"`

> **辅助判断：通过包管理器检测**
> 
> 

不同的发行版家族使用不同的包管理工具，通过检测这些命令是否存在也能精准区分：

- `command -v apt`：存在则为 Debian/Ubuntu 系。

- `command -v yum`：存在则为 RHEL/CentOS 7 系。

- `command -v dnf`：存在则为 RHEL/CentOS 8\+ 或 Fedora 系。

- `command -v pacman`：存在则为 Arch Linux 系。

- `command -v zypper`：存在则为 SUSE 系。

**💡 避坑提示**

1. 不要依赖 `uname -r` 或 `uname -a` 判断发行版：`uname` 命令仅显示 Linux 内核版本和硬件架构，不包含发行版名称。同一个内核可以被多个不同的发行版复用。

2. 慎用 `/etc/issue`：该文件是登录前的欢迎文本，极易被管理员手动修改（如改为自定义欢迎语），导致丢失真实的发行版信息。

3. 注意精简环境：在 Docker 容器或最小化安装的系统（如 CentOS Stream）中，`lsb_release` 命令可能未安装，甚至 `/etc/os-release` 的内容也可能被精简，此时结合包管理器检测最为可靠。

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux包管理工具]]
- [[Linux系统监控-CPU]]

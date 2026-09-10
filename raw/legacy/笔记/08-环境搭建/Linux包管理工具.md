---
type: note
tags: [Linux] [环境搭建] [软件安装]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 包管理工具

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-包管理工具 小节

Linux 的包管理工具因发行版而异，主要可以分为两大阵营：基于 Debian 的系统（如 Ubuntu、Debian）和基于 Red Hat 的系统（如 CentOS、Fedora、Rocky Linux）。此外，还有一些跨发行版的现代工具。

## 6\.1 APT \(Advanced Package Tool\)

适用系统：**Debian、Ubuntu** 及其衍生版。
特点：APT 是底层 `dpkg` 工具的前端，能够自动处理复杂的软件依赖关系，是 Debian 系系统的核心包管理器。

常用命令示例：

- 更新软件源列表（安装或升级软件前建议先执行）：
`sudo apt update`

- 升级所有已安装的软件包：
`sudo apt upgrade`

- 安装指定软件：
`sudo apt install <package_name>`

- 卸载软件（保留配置文件）：
`sudo apt remove <package_name>`

- 彻底卸载软件（同时删除配置文件）：
`sudo apt purge <package_name>`

- 清理不再需要的依赖包：
`sudo apt autoremove`

- 搜索软件包：
`apt search <keyword>`

## 6\.2 YUM / DNF

适用系统：**CentOS、RHEL、Fedora、Rocky Linux **等。
特点：YUM 是老牌的包管理器，而 DNF 是其现代化的继任者，旨在解决 YUM 的性能和依赖解析问题。在较新的系统中，`dnf` 命令已取代 `yum`，但许多基础命令语法保持一致。

常用命令示例（以 DNF 为例，YUM 用法类似）：

- 检查可用更新：
`sudo dnf check-update`

- 更新所有已安装的软件包：
`sudo dnf update`

`yum/dnf list installed | grep 包名`

- 安装指定软件：
`sudo dnf install <package_name>`

- 卸载指定软件：
`sudo dnf remove <package_name>`

- 搜索软件包：
`dnf search <keyword>`

- 查看软件包详细信息：
`dnf info <package_name>`

- 清理缓存：
`sudo dnf clean all`

- 列出所有可用和已安装的软件包：
`dnf list`

## 6\.3 底层包管理工具：dpkg \& rpm

特点：它们是各自阵营的底层工具，可以手动安装、卸载单个软件包文件，但不会自动处理依赖关系。日常使用建议优先用 APT/YUM/DNF，仅在离线安装或排查问题时使用底层工具。

- dpkg \(Debian 系\)：

    - 安装本地 `.deb` 包：`sudo dpkg -i <package_name>.deb`

    - 处理安装失败时的依赖问题：`sudo apt --fix-broken install`

    - 列出已安装的包：`dpkg -l`

- rpm \(Red Hat 系\)：

    - 安装本地 `.rpm` 包：`sudo rpm -ivh <package_name>.rpm`

    - 卸载软件包：`sudo rpm -e <package_name>`

    - 查询已安装的包：`rpm -qa | grep <package_name>`

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux系统版本查询]]
- [[Linux进程管理]]

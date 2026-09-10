---
type: note
tags: [Linux] [环境搭建] [权限]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 用户与权限管理

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-用户权限管理 小节

## 8\.1 用户管理

### 8\.1\.1 创建用户 \(`useradd`\)

`useradd` 是用于添加新用户的核心命令，通常需要 `root` 或 `sudo` 权限。
常用选项：

- `-m`：自动为用户创建家目录（默认路径通常为 `/home/用户名`）。

- `-s`：指定用户登录时使用的 Shell（如 `/bin/bash`）。

- `-g`：指定用户的主组（需提前创建）。

- `-G`：指定用户的附加组（多个组用逗号分隔）。

- `-d` \(指定路径\)：用于指定该用户家目录的具体路径。默认情况下，家目录会创建在 `/home/用户名`，使用此选项可以将其更改为其他位置（例如 `/data/user` 或 `/opt/user`）。

- `-m` \(强制创建目录\)：告诉系统自动创建该家目录，并从 `/etc/skel/` 复制默认的配置文件（如 `.bashrc`）进去。这是一个新手极易忽略的必加选项，如果不加 `-m`，系统只会在配置文件中记录该路径，而不会真正在磁盘上创建这个目录，导致用户无法正常登录。

**操作示例：**
创建一个名为 `alice` 的普通用户，自动创建家目录并指定 Bash 作为 Shell：

```Shell
sudo useradd -m -s /bin/bash alice

# 创建用户并指定自定义家目录
sudo useradd -m -d /自定义/路径/家目录 用户名
```

创建后，必须使用 `passwd` 命令为其设置密码，否则无法登录：

```Shell
sudo passwd alice
```

*\(注：在 Ubuntu/Debian 系统中，也可使用更友好的交互式命令 **`sudo adduser username`** 来创建用户\)*

### 8\.1\.2 删除用户 \(`userdel`\)

`userdel` 用于删除不再需要的用户账户。
常用选项：

- `-r`：在删除用户的同时，递归删除其家目录及邮件池（`/var/spool/mail/用户名`）。

- `-f`：强制删除用户，即使用户当前处于登录状态或有运行中的进程。

**操作示例：**
彻底删除用户 `alice` 及其家目录：

```Shell
sudo userdel -r alice
```

### 8\.1\.3 查看 \& 修改用户信息

- 查看用户信息：使用 `id 用户名` 查看 UID、GID 及所属组；使用 `groups 用户名` 仅查看所属组。

- 修改用户属性：使用 `usermod` 命令。例如，将用户 `alice` 追加到 `sudo` 组以赋予管理员权限：

```Shell
sudo usermod -aG sudo alice
```

### 8\.1\.3 用户密码管理

`passwd` 命令用于设置或修改用户密码。普通用户只能修改自己的密码，而 `root` 可以修改任何人的密码。

```Shell
# 修改当前登录用户的密码
passwd    #*系统会要求输入当前密码进行验证，然后输入两次新密码*

# 管理员修改指定用户的密码
sudo passwd alice    #*管理员修改他人密码时，不需要知道旧密码，且可以设置不符合复杂度的弱密码*

# 锁定与解锁用户密码（常用于离职或临时禁用账号）
sudo passwd -l alice   # 锁定用户，使其无法通过密码登录
sudo passwd -u alice   # 解锁用户

# 强制用户下次登录时修改密码（常用于创建初始账号后）
sudo passwd -e alice
```

**查看用户状态以及密码是否过期：**

1. **使用 ****`chage -l`**** 命令（推荐）**
`chage` 命令可以显示用户密码的详细信息，包括密码的最后修改时间、过期时间、最大有效期等。

- 命令格式：`chage -l 用户名`

- 查看结果：执行后，查看输出中的 `Password expires`（密码过期时间）字段。如果显示具体的日期，则表示密码会在该日期过期；如果显示 `never`，则表示密码永不过期。

2. **使用 ****`passwd -S`**** 命令**
该命令用于显示指定用户的密码状态信息。

- 命令格式：`passwd -S 用户名`

- 查看结果：输出内容的第二个字段表示密码状态。例如，`P` 或 `PS` 表示密码已设置且有效（未过期）；`L` 表示密码已锁定；`NP` 表示没有密码。

3. **查看 ****`/etc/shadow`**** 文件**
用户的密码及过期信息实际上存储在 `/etc/shadow` 文件中。

- 命令格式：`cat /etc/shadow | grep 用户名`

- 查看结果：输出结果以冒号分隔，其中第 3 个字段是最后一次更改密码的日期（从 1970 年 1 月 1 日算起的天数），第 5 个字段是密码的最大有效天数。需要注意的是，该文件包含敏感信息，通常需要 `root` 权限才能查看。

4. **查看用户的登录历史记录**

如果您想排查用户近期的登录状态或是否有异常登录：

- `last 用户名`：显示该用户最近的登录成功记录，包括登录时间、来源 IP 等。

- `lastb 用户名`：显示该用户最近的登录失败记录（排查暴力破解等攻击）。

5. **查看账户的登录失败计数（针对安全锁定）**

如果系统配置了登录失败自动锁定策略，可以通过以下命令查看失败次数：

- `sudo faillog -u 用户名`：查看指定用户的登录失败记录，如果显示 `locked`，则表示账户因多次失败被锁定。

### 8\.1\.4 切换用户

> **su \(Switch User\)**
> 
> 

用于切换到另一个用户（默认是 root）。

- su username：仅切换身份，保留当前用户的环境变量（工作目录、PATH 等不变）。

- su \- username：完全切换身份，加载目标用户的环境变量（相当于重新登录）。

```Shell
su - root          # 切换到 root，并加载 root 的环境变量（推荐）
su alice           # 切换到 alice，保留当前环境变量

*(注：退出当前切换的用户环境，返回上一个用户，使用 exit 命令或快捷键 Ctrl+D)*
```

> **`sudo -i`**** / ****`sudo su -`**
> 
> 

如果你当前登录的是普通用户，且拥有 sudo 权限，想直接获取一个完整的 root Shell：

```Shell
sudo -i    # *执行后提示符通常会从 $ 变为 #，表示已进入 root 环境*
```

`sudo su -` 和 `sudo su` 的核心区别在于是否加载目标用户（root）的完整登录环境。

简单来说，`sudo su -` 会模拟一次完整的 root 用户登录，而 `sudo su` 仅仅是借用了 root 的身份，但保留了你原来普通用户的环境。

> **`sudo su`****（不带 ****`-`****）**
> 
> 

- 环境变量：不加载 root 的完整登录环境（如 `.bash_profile` 等）。`PATH` 变量通常会被 `sudo` 重置为安全路径，既不是原用户的，也不是 root 的默认路径。

- 工作目录：保持在原用户的当前目录（例如 `/home/student`），不会发生跳转。

- 行为本质：相当于以 root 身份执行了 `su` 命令。它只是切换了身份，但 Shell 环境仍然是普通用户的 Shell。

> **`sudo su -`****（带 ****`-`****）**
> 
> 

- 环境变量：完全模拟 root 的登录环境。系统会清空原有环境，加载 root 的完整配置文件，`PATH` 等变量会被设置为 root 的默认路径。

- 工作目录：自动切换到 root 的家目录（`/root`）。

- 行为本质：相当于安全地获得了一个干净的 root 环境，等同于直接以 root 身份登录系统。

|对比维度|`sudo su`|`sudo su -`|
|---|---|---|
|环境加载|不加载 root 的登录脚本|加载 root 的完整登录环境|
|工作目录|保持原用户目录（如 `/home/user`）|自动切换至 `/root`|
|PATH 变量|被 sudo 重置为安全路径|恢复为 root 的默认路径（如 `/usr/local/sbin`）|
|适用场景|临时获取 root 权限，但环境受限|完全以 root 身份操作，需要完整环境|

### 8\.1\.5 提升 sudoers 权限

在 Ubuntu/Debian 系中，通常将用户加入 `sudo` 组；在 CentOS/RHEL 系中，通常加入 `wheel` 组。如果需要更精细的权限控制，则需要编辑 `sudoers` 文件（/etc/sudoers）。

- **基础提权：加入管理员组**

```Shell
*# Ubuntu/Debian 系统*
sudo usermod -aG sudo alice

*# CentOS/RHEL 系统*
sudo usermod -aG wheel alice
```

*\(⚠️ 注意：修改组权限后，用户必须重新登录（或执行 **`newgrp sudo`**）才能生效。\)*

- **进阶提权：自定义 sudoers 规则**

如果只想让普通用户 `alice` 拥有部分管理员权限（例如：只允许她重启 Nginx 服务，但不允许执行其他 root 命令），需要编辑 sudoers 配置。

⚠️ *核心安全警告：绝对不要直接使用 **`vim /etc/sudoers`** 编辑该文件！一旦语法写错，会导致整个系统的 sudo 权限瘫痪，连 root 都无法修复。必须使用 **`visudo`** 命令，它会在保存时自动检查语法。*

操作示例：

```Shell
sudo visudo
```

在打开的编辑器中，找到 `# User privilege specification` 区域，添加如下规则：

```Shell
# 允许 alice 无需密码即可执行重启 nginx 的命令
alice ALL=(ALL) NOPASSWD: /usr/sbin/nginx -s reload    # 用户名/用户组 主机=(可切换的身份) 标签: 可执行的命令

# 允许 devs 组内的所有用户执行 /opt/scripts/ 目录下的所有脚本
%devs ALL=(ALL) /opt/scripts/*
```

*\(保存退出后，alice 就可以通过 **`sudo /usr/sbin/nginx -s reload`** 来重启服务了。\)*

**常见配置示例：**

1. 赋予用户完全管理员权限（需密码）：

```Shell
alice ALL=(ALL:ALL) ALL    # *用户 alice 可以在任何主机上，以任何用户和组的身份，执行任何命令*

# 无需密码
alice ALL=(ALL:ALL) NOPASSWD: ALL  
# *允许 alice 在任何主机上，以任何身份，无需密码执行任何命令。包含了免密执行 sudo su -*
```

2. 赋予用户免密执行特定命令的权限：

```Shell
alice ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx    
# *用户 alice 在执行重启 nginx 命令时，无需输入密码。这在自动化脚本中非常常用*
```

3. 赋予整个用户组权限：

```Shell
%devs ALL=(ALL) /opt/scripts/*    # *devs 组内的所有用户，都可以执行 /opt/scripts/ 目录下的所有脚本*
```

- **推荐的最佳实践：使用 ****`/etc/sudoers.d/`**** 目录**

为了保持主配置文件整洁且避免误操作，现代 Linux 强烈建议将自定义权限写在独立文件中：

```Shell
*# 1. 创建一个独立的配置文件（visudo -f 同样会检查语法）*
sudo visudo -f /etc/sudoers.d/alice-custom

*# 2. 在文件中写入权限规则并保存*
alice ALL=(ALL) NOPASSWD: /usr/sbin/nginx -s reload

*# 3. 确保文件权限正确（必须是 440）*
sudo chmod 0440 /etc/sudoers.d/alice-custom
```

**💡 运维小贴士：**

在日常排查问题时，如果不确定某个普通用户当前到底拥有哪些 sudo 权限，可以切换到该用户后执行：

```Shell
sudo -l    # 这会列出该用户所有被授权的 sudo 命令清单，是排查权限问题的神器。
```

- **添加免密切换规则**

> **使用 ****`visudo`**** 安全编辑**
> 
> 

为了防止语法错误导致系统 sudo 权限瘫痪，必须使用 `visudo` 命令进行编辑：

```Shell
sudo visudo
```

> **添加免密切换规则**
> 
> 

在打开的文件中，根据你的需求添加以下规则之一：

- 针对特定用户免密（例如用户名为 `alice`）：

```Shell
alice ALL=(ALL:ALL) NOPASSWD: ALL
# *允许 alice 在任何主机上，以任何身份，无需密码执行任何命令。这自然包含了免密执行 sudo su - 的操作*
```

- 针对用户组免密（例如 `sudo` 组或 `wheel` 组）：

```Shell
%sudo ALL=(ALL:ALL) NOPASSWD: ALL    # *允许 sudo 组内的所有成员无需密码执行任何命令*
```

---

## 8\.2 权限管理

### **8\.2\.1 权限基础概念**

使用 `ls -l` 命令可查看文件/目录的详细权限。权限字符串由 10 个字符组成，例如 `-rwxr-xr--`：

- 第 1 位：文件类型（`-` 为普通文件，`d` 为目录，`l` 为软链接）。

- 第 2\-4 位：所有者（User, `u`）的权限。

- 第 5\-7 位：所属组（Group, `g`）的权限。

- 第 8\-10 位：其他用户（Other, `o`）的权限。

**三种基本权限：**

- `r` \(Read\)：读取文件内容 / 列出目录内容。

- `w` \(Write\)：修改文件内容 / 在目录中创建、删除、重命名文件。

- `x` \(Execute\)：作为程序执行文件 / 进入（`cd`）该目录。

### **8\.2\.2 修改访问权限 \(****`chmod`****\)**

`chmod` \(Change Mode\) 用于修改文件或目录的读、写、执行权限，支持字符模式和数字模式。

- **字符模式（精准加减权限）：**

```Shell
chmod u+x script.sh      *# 给所有者添加执行权限*
chmod go-w config.txt    *# 移除所属组和其他用户的写权限*
chmod a=rwx test.py      *# 赋予所有用户读、写、执行权限*
```

- **数字模式（生产环境常用）：**
权限对应数值为 `r=4, w=2, x=1`，将同一主体的权限相加即可（如 `rwx = 4+2+1 = 7`）。

```Shell
chmod 755 script.sh      *# 所有者rwx(7)，所属组r-x(5)，其他用户r-x(5)*
chmod 644 config.txt     *# 所有者rw-(6)，所属组r--(4)，其他用户r--(4)*
```

- **递归修改：**
对目录及其内部所有子文件/子目录统一修改权限时，必须加 `-R` 参数：

```Shell
chmod -R 755 /path/to/directory
```

### **8\.2\.3 修改文件归属 \(****`chown`****\)**

`chown` \(Change Owner\) 用于修改文件或目录的所有者及所属组，此操作通常需要 `root` 权限。

操作示例：

```Shell
chown alice file.txt           *# 仅修改所有者为 alice*
chown alice:devs file.txt      *# 同时修改所有者为 alice，所属组为 devs*
chown -R bob:staff project/    *# 递归修改目录及内部所有内容的归属*
```

> *⚠️ 安全建议：在生产环境中，应遵循“最小权限原则”（PoLP），仅赋予用户和进程完成工作所需的最低访问权限，慎用 **`chmod 777`** 等全开权限配置。*
> 
> 

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux进程管理]]
- [[Linux软链接与硬链接]]

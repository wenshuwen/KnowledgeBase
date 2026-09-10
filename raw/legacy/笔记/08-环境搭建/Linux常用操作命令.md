---
type: note
tags: [Linux] [命令速查]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 常用操作命令大全

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-常用操作命令 小节（sed/xargs/awk/find/curl 等，内容较长）

## 10\.1 sed

**sed**（Stream EDitor，流编辑器）是 Linux/Unix 系统中一个非常强大且高效的文本处理工具。它逐行读取输入，在内存中的临时缓冲区（称为“模式空间”）进行处理，最后将结果输出到标准输出。它不会直接修改原文件（除非使用特定选项）。

**基本语法：**

```Shell
*sed [选项] '命令' 文件名*
*
*# 或者从脚本文件读取命令：
sed [选项] -f 脚本文件 文件名
```

**常用选项：**

- `-n`：静默模式。取消默认的输出，通常配合 `p` 命令只打印匹配的行。

- `-e`：允许多项编辑。可以在命令行中指定多个 `sed` 命令。

- `-i`：直接修改原文件（原地编辑）。慎用，建议加后缀备份，如 `-i.bak`。

- `-r` 或 `-E`：使用扩展正则表达式（ERE），简化部分正则语法（如 `+`, `?`, `|` 不需要转义）。

- `-f`：从指定的脚本文件中读取 `sed` 命令。

**核心操作命令：**

- **替换（s 命令）**

```Shell
# 基本替换（替换每行第一个匹配项）
*sed 's/apple/orange/' file.txt*

# 全局替换（替换每行所有匹配项，使用 g 标志）
*sed 's/apple/orange/g' file.txt*

# 替换第 N 个匹配项
*sed 's/apple/orange/2' file.txt
*
# 自定义分隔符（当替换内容包含 / 时，可用 @ 或 # 代替）
*sed 's@/home/user@/tmp@g' file.txt
*
```

- **删除（d 命令）**

```Shell
# 删除指定行（如删除第 3 行）
*sed '3d' file.txt
*
# 删除行范围（如删除第 2 到第 5 行）
*sed '2,5d' file.txt*

# 删除最后一行
*sed '$d' file.txt**
*
# 按条件删除（删除包含 "error" 的行）
*sed '/error/d' file.txt*
*
*# 删除空行
*sed '/^$/d' file.txt*
```

- **打印（p 命令，通常配合 ****`-n`**** 使用）**

```Shell
# 打印匹配的行
*sed -n '/success/p' file.txt
*
# 打印指定行范围
*sed -n '1,3p' file.txt
*
# 打印最后一行
*sed -n '$p' file.txt*
```

- **直接修改并备份原文件（强烈推荐的安全做法）**

```Shell
sed -i.bak 's/test/TEST/g' file.txt
```

## 10\.2 xargs

**xargs**（eXtended ARGuments）是 Linux/Unix 系统中一个非常强大且常用的命令。它的核心作用是从标准输入（stdin）读取数据，并将其转换为命令行参数传递给其他命令。

### **10\.2\.1 核心概念**

> **为什么要用 xargs？**
> 
> 

在 Linux 中，管道符 \(`|`\) 可以将前一个命令的输出作为后一个命令的输入。但很多命令（如 `rm`、`ls`、`echo`）并不从标准输入读取数据，而是从命令行参数获取。`xargs` 解决了这个矛盾，它读取标准输入中的内容，再将其作为参数传递给指定的命令。

此外，`xargs` 还有两个关键作用：

- 分批处理：当要删除或操作的文件数量巨大时，直接使用 `rm -f *.log` 可能会因为参数列表太长而报错。`xargs` 可以按批次将参数传递给命令，避免这个问题。

- 并行执行：通过 `-P` 选项，`xargs` 可以同时运行多个进程，极大地提高处理速度。

### **10\.2\.2 常用选项详解**

|选项|说明|典型场景|
|---|---|---|
|`-0`|空字符分隔：以空字符（`\0`）而非空白字符作为输入项的分隔符，并禁用引号和反斜杠的特殊含义。这是处理包含空格或换行符的文件名的标准做法。|与 `find -print0` 配合，安全处理文件名。|
|`-I {}`|替换字符串：将命令中出现的 `{}` 替换为从标准输入读取的每一项。这让你可以灵活地控制参数位置。|对每个输入项执行一次命令，如复制文件到指定目录：`... | xargs -I {} cp {} /target/`。|
|`-n`|限制参数个数：指定每条命令行最多使用的参数个数。|将大量参数分批处理，或强制每行输出特定数量的内容。|
|`-P`|并行进程数：同时运行最多 N 个进程。若设为 0，则尽可能多地同时运行。|在多核 CPU 上并行处理任务，如批量转换图片。|
|`-r`|无输入不执行：如果标准输入中没有非空白字符，则不运行命令。GNU 扩展特性。|防止在输入为空时，命令被意外执行一次（默认行为）。|
|`-d`|自定义分隔符：使用指定的单个字符作为输入项的分隔符，而非默认的空白字符。|处理格式为 `a:b:c` 的简单列表。|

### **10\.2\.3 使用示例**

- **安全地删除文件（核心用法）**

处理文件名时，空格和换行是常见陷阱。使用 `-print0` 和 `-0` 是解决这个问题的标准方案。

```Shell
*# 查找所有 .txt 文件并安全删除
*find . -name "*.txt" -type f -print0 | xargs -0 rm -f
```

- **将多行输入转换为单行**

`xargs` 的默认行为就是读取输入，并将其以空格分隔合并到一行。

```Shell
*# 默认目标命令是 echo，将多行内容变成一行输出
*cat example.txt | xargs
```

- **批量重命名文件**

`-I` 允许我们构建更复杂的命令模板，对每个文件执行操作。

```Shell
# 将当前目录下所有 .jpg 文件复制到 backup 目录
ls *.jpg | xargs -I {} cp {} /backup/

ls *.txt | xargs -I {} mv {} backup_{}
```

- **统计代码行数**

```Shell
find . -name "*.c" | xargs wc -l
```

> *文件名的空格问题：这是新手最容易掉进的坑。只要你的输入可能包含空格或特殊字符（如文件名），就应该优先考虑 **`-0`** 选项。*
> 
> 

## 10\.3 awk

**awk **是 Linux/Unix 环境下极其强大的文本处理和数据分析工具，被誉为“文本处理三剑客”之一。它不仅仅是一个命令行工具，更是一门完整的编程语言，特别适合处理结构化文本（如日志、表格、CSV 文件），能够轻松完成数据提取、格式化输出、数值计算和生成报表等任务。

**awk** 的核心思想可以概括为：逐行读取 → 按列分割 → 条件过滤 → 执行动作。在处理有规律的文本数据时，它比传统的 grep（侧重行匹配）和 sed（侧重流编辑替换）更具优势，是系统管理员和开发者不可或缺的数据处理利器。

### 10\.3\.1 核心概念与基本语法

`awk` 的基本工作原理是：逐行读取文本 → 按分隔符将每行切片（分割为多个字段） → 根据条件进行过滤 → 对匹配的行执行指定动作。

```Shell
*awk '条件 {动作}' 文件名*
```

- 条件 \(Pattern\)：用于筛选行，可以是正则表达式、关系表达式等。如果省略，默认对所有行执行动作。

- 动作 \(Action\)：用花括号 `{}` 包围，表示匹配成功后要执行的操作（如打印、计算等）。如果省略，默认执行 `{print $0}` 输出整行。

- 字段引用：`awk` 默认以空格或制表符作为分隔符。`$0` 代表整行，`$1` 代表第一个字段，`$2` 代表第二个字段，以此类推。

- 记录与字段：默认每行是一条记录，行内由空格或制表符分隔成多个字段。`$1`、`$2`\.\.\.代表第 1、2 个字段，`$0`代表整行，`NF`是当前行字段总数，`NR`是当前行号。

- 模式与动作：基本语法是 `awk '模式 {动作}' 文件`。模式用于筛选行（比如 `NR>5` 或 `/error/`），动作是处理逻辑（比如 `{print $1}`）。如果省略模式，则对所有行执行动作。

### 10\.3\.2 常用内置变量

掌握内置变量是高效使用 `awk` 的关键：

- `NR`：当前处理的行号（Number of Record）。

- `NF`：当前行的字段数/列数（Number of Fields）。`$NF` 代表最后一个字段。

- `FS`：输入字段分隔符（默认是空格/制表符）。

- `OFS`：输出字段分隔符（默认是空格）。

- `FILENAME`：当前正在处理的文件名。

### 10\.3\.3 基础使用示例

- **提取特定列**

```Shell
*# 输出文件每行的第一个字段
awk '{print $1}' test.txt

# 输出第1和第3个字段，中间用默认空格分隔
awk '{print $1, $3}' test.txt

# 输出行号 + 整行内容
**awk '{print NR, $0}' test.txt*
```

- **自定义分隔符**

当文本不以空格分隔时（如 `/etc/passwd` 使用冒号），可以使用 `-F` 选项或 `FS` 变量指定分隔符：

```Shell
*# 以冒号 : 为分隔符，提取用户名（第1列）和默认Shell（最后一列）
awk -F: '{print $1, $NF}' /etc/passwd

# 处理 CSV 文件，以逗号 , 为分隔符
**awk -F, '{print $2}' test.csv*
```

- **条件匹配与过滤**

```Shell
*# 正则匹配：只输出包含 "root" 的行的第一个字段
awk '/root/ {print $1}' /etc/passwd

# 数值比较：输出第3列值大于 80 的行
awk '$3 > 80 {print $2, $3}' score.txt

# 字符串精确匹配：输出姓名为 Alice 的行
awk '$2 == "Alice" {print $0}' score.txt

# 逻辑与 (&&)：输出分数大于80且小于等于90的学生
**awk '$3 > 80 && $3 <= 90 {print $2, $3}' score.txt*
```

- **使用****`BEGIN`****和****`END`****做汇总**

```Shell
*awk '{sum += $1; count++} END {print "总和:", sum, "平均值:", sum/count}' numbers.txt*
```

- **分析 Nginx 访问日志（统计 IP 访问频次）**

假设日志格式为 `IP - 请求方法 路径 状态码`，统计每个 IP 的访问次数并按降序排列：

```Shell
*awk '{count[$1]++} END {for(ip in count) print ip, count[ip]}' access.log | sort -nr*
```

- **批量生成 SQL 语句**

根据文本文件中的内容，快速生成数据库插入语句：

```Shell
*awk '{print "INSERT INTO student VALUES(" $1 ", \x27" $2 "\x27, " $3 ");"}' students.txt*
```

- **提取磁盘使用率**

结合 `df -h` 命令，跳过表头（NR\>1），提取使用率和挂载点：

```Shell
*df -h | awk 'NR>1 {print $5, $6}'*
```

## 10\.4 find

Linux 系统中最强大、最灵活的文件查找工具。它不仅能根据文件名、类型、大小、时间等多种条件精准定位文件，还能直接对找到的文件执行删除、移动、权限修改等批量操作。

### 10\.4\.1 按文件名查找（最常用）

- \-name：区分大小写。

- \-iname：不区分大小写。

- 支持通配符 \*（匹配任意字符）和 ?（匹配单个字符）。

```Shell
*# 在当前目录及子目录下查找所有 .log 结尾的文件
find . -name "*.log"

# 在 /etc 目录下查找名为 hosts 的文件（忽略大小写）
find /etc -iname "hosts"

# 查找文件名以一个大写字母开头的 .txt 文件
**find . -name "[A-Z]*.txt"*
```

> 💡 避坑提示：使用通配符 \* 时，务必加上引号（如 "\*\.txt"），防止被 Shell 提前解析导致查找失败。
> 
> 

### 10\.4\.2 按文件类型查找

- f：普通文件。

- d：目录。

- l：符号链接。

```Shell
*# 查找当前目录下所有的目录
find . -type d

# 查找 /usr 下所有以 python 开头的目录
**find /usr -type d -name "python*"*
```

### 10\.4\.3 按文件大小查找

常用于磁盘空间告警时清理大文件。\+ 表示大于，\- 表示小于，无符号表示等于。

- 单位：c \(字节\), k \(KB\), M \(MB\), G \(GB\)。

```Shell
*# 查找当前目录下大于 100MB 的文件
find . -type f -size +100M

# 查找 /var/log 下小于 10KB 的日志文件
**find /var/log -type f -size -10k*

# 查找空文件
find . -type f -empty

# 查找空目录
find . -type d -empty
```

### 10\.4\.4 按时间查找

Linux 文件有三个核心时间戳：mtime（内容修改时间）、atime（访问时间）、ctime（状态改变时间，如权限修改）。单位默认为“天”，也可以用 mmin 表示“分钟”。

```Shell
*# 查找 7 天内修改过的 .txt 文件
find . -name "*.txt" -mtime -7

# 查找超过 30 天未访问过的文件（常用于清理旧日志）
find /tmp -type f -atime +30

# 查找 10 分钟前状态发生过改变的文件
**find . -type f -cmin +10*
```

### 10\.4\.5 按权限与所有者查找

```Shell
*# 查找当前目录下权限为 777 的文件（存在安全隐患）
find . -type f -perm 777

# 查找所有者为 www 的文件
**find . -user www*
```

### 10\.4\.6 限制搜索深度

```Shell
*# 仅在当前目录及下一级子目录中查找 .conf 文件
**find . -maxdepth 2 -name "*.conf"*
```

### 10\.4\.7 对搜索结果执行动作（批量操作）

#### 10\.4\.7\.1 直接删除（\-delete）

```Shell
*# 查找 /var/log 下 30 天前的旧日志并直接删除
**find /var/log -name "*.log" -mtime +30 -delete*
```

#### 10\.4\.7\.2 执行复杂命令（\-exec）

\-exec 后面可以接任何 Linux 命令，\{\} 代表找到的文件名，\\; 代表命令结束。

```Shell
*# 找到所有 .log 文件，并列出它们的详细信息（相当于执行 ls -lh 文件名）
find . -name "*.log" -exec ls -lh {} \;

# 找到所有 .txt 文件，并将它们复制到 /backup 目录
**find . -name "*.txt" -exec cp {} /backup \;*
```

#### 10\.4\.7\.3 组合条件（逻辑运算）

- \-a 或空格：表示“且”（同时满足）。

- \-o：表示“或”（满足其一）。

- \! 或 \-not：表示“非”（取反）。

```Shell
*# 查找以 .txt 结尾 或 以 .pdf 结尾的文件
find . \( -name "*.txt" -o -name "*.pdf" \)

# 查找所有不是以 .txt 结尾的普通文件
**find . -type f ! -name "*.txt"*
```

### 10\.4\.8 find 命令速查表

|查找维度|常用参数|参数说明与示例|
|---|---|---|
|按名称|`-name`, `-iname`|`-iname` 忽略大小写，如 `find . -name "*.sh"`|
|按类型|`-type f/d/l`|f=文件, d=目录, l=软链接|
|按大小|`-size +100M/k/G`|`+`大于, `-`小于，如 `find . -size +100M`|
|按时间|`-mtime/-atime`|修改/访问时间，`-7`表示 7 天内，`+30`表示 30 天前|
|按权限|`-perm 755`|精确匹配权限，如 `find . -perm 777`|
|按用户|`-user username`|查找指定用户拥有的文件|
|限制搜索深度|`-maxdepth 1`|只查当前层，不递归进入子目录|
|逻辑组合|`-o` \(或\), `!` \(非\)，`-not`\(非\)|组合多个条件，如 `find . -name "*.txt" -o -name "*.pdf"`|
|执行动作|`-exec`, `-delete`|对结果执行命令或直接删除|

## 10\.5 curl

一个功能强大的命令行数据传输工具，支持几乎所有的网络协议（HTTP、HTTPS、FTP、SFTP、TELNET、SMTP 等）。它的核心工作是在命令行中通过 URL 与服务器传输数据，是日常开发、调试和自动化脚本中最得力的助手之一。

### 10\.5\.1 核心功能分类

- **基础请求类**

|参数|说明|示例|
|---|---|---|
|`-X` / `--request`|指定请求方法|`curl -X POST http://example.com`|
|`-H` / `--header`|添加请求头|`curl -H "Content-Type: application/json" http://api.com`|
|`-i`|显示响应头信息|`curl -i http://example.com`|
|`-I`|只显示响应头|`curl -I http://example.com`|
|`-v`|显示详细通信过程|`curl -v http://example.com`|

- **数据发送类**

|参数|说明|示例|
|---|---|---|
|`-d` / `--data`|发送 POST 数据（表单格式）|`curl -d "name=john&age=25" http://api.com`|
|`-F` / `--form`|模拟表单上传文件|`curl -F "file=@/path/to/file.jpg" http://upload.com`|
|`--data-urlencode`|URL 编码的数据|`curl --data-urlencode "name=张三 李四" http://api.com`|
|`-G` / `--get`|将 `-d` 数据附加到 URL 后|`curl -G -d "key=value" http://api.com`|

- **输出控制类**

|参数|说明|示例|
|---|---|---|
|`-o`|保存到指定文件|`curl -o output.txt http://example.com`|
|`-O`|使用远程文件名保存|`curl -O http://example.com/file.zip`|
|`-s`|静默模式，不显示进度|`curl -s http://api.com`|
|`-S`|静默但显示错误|`curl -sS http://api.com`|
|`-#`|显示进度条|`curl -# -O http://largefile.zip`|

- **网络控制类**

|参数|说明|示例|
|---|---|---|
|`-L`|跟随重定向|`curl -L http://short.link`|
|`-k`|跳过 SSL 证书验证|`curl -k https://self-signed.com`|
|`-x` / `--proxy`|使用代理|`curl -x http://proxy:8080 http://target.com`|
|`-m` / `--max-time`|最大执行时间（秒）|`curl -m 30 http://slow.com`|
|`--connect-timeout`|连接超时（秒）|`curl --connect-timeout 10 http://api.com`|
|`-C` / `--continue-at`|断点续传|`curl -C - -O http://largefile.zip`|

- **认证与 Cookie 类**

|参数|说明|示例|
|---|---|---|
|`-u` / `--user`|HTTP 基本认证|`curl -u "username:password" http://api.com`|
|`-b` / `--cookie`|发送 Cookie|`curl -b "name=value" http://example.com`|
|`-c` / `--cookie-jar`|保存 Cookie 到文件|`curl -c cookies.txt http://login.com`|
|`-e` / `--referer`|设置来源 URL|`curl -e "http://google.com" http://target.com`|
|`-A` / `--user-agent`|设置 User\-Agent|`curl -A "Mozilla/5.0" http://example.com`|

### 10\.5\.2 实战使用示例

#### **场景 1：API 接口测试**

```Shell
*# 1. 测试 GET 接口
curl -X GET "https://api.github.com/users/octocat"

# 2. 测试 POST JSON 接口
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "张三",
    "email": "zhangsan@example.com",
    "age": 28
  }'

# 3. 测试 PUT 请求更新数据
curl -X PUT https://api.example.com/users/123 \
  -H "Content-Type: application/json" \
  -d '{"name": "李四"}'

# 4. 测试 DELETE 请求
curl -X DELETE https://api.example.com/users/123 \
**  -H "Authorization: Bearer YOUR_TOKEN"*
```

#### **场景 2：文件下载**

```Shell
*# 1. 简单下载
curl -O https://example.com/images/photo.jpg

# 2. 指定文件名下载
curl -o myphoto.jpg https://example.com/images/photo.jpg

# 3. 断点续传下载大文件
curl -C - -O https://example.com/large-file.iso
**-C -：自动计算已下载的字节数，从中断处继续*
-O：使用远程文件名保存到本地
*
# 4. 限速下载（限制为 1MB/s）
curl --limit-rate 1M -O https://example.com/video.mp4

# 5. 下载多个文件
curl -O https://example.com/file1.zip -O https://example.com/file2.zip

# 6. 显示进度条下载
**curl -# -O https://example.com/huge-file.zip*
```

#### **场景 3：表单提交与文件上传**

```Shell
*# 1. 模拟 HTML 表单提交（application/x-www-form-urlencoded）
curl -X POST https://example.com/login \
  -d "username=admin" \
  -d "password=123456"

# 2. 多部分表单上传文件
curl -X POST https://example.com/upload \
  -F "file=@/home/user/document.pdf" \
  -F "description=我的文档"

# 3. 上传多个文件
curl -X POST https://example.com/upload \
  -F "files[]=@/path/file1.jpg" \
  -F "files[]=@/path/file2.jpg"

# 4. 从文件读取 POST 数据
curl -X POST https://api.example.com/data \
  -H "Content-Type: application/json" \
**  -d @/path/to/data.json*
```

#### **场景 4：Cookie 会话管理**

```Shell
*# 1. 登录并保存 Cookie
curl -c cookies.txt -X POST https://example.com/login \
  -d "username=john" \
  -d "password=secret"

# 2. 使用 Cookie 访问需登录的页面
curl -b cookies.txt https://example.com/dashboard

# 3. 手动设置 Cookie
curl -b "session_id=abc123; user=john" https://example.com/profile

# 4. 同时保存和使用 Cookie
**curl -b cookies.txt -c cookies.txt https://example.com/api/data*
```

#### **场景 5：HTTP 头操作**

```Shell
*# 1. 设置自定义请求头
curl -H "X-API-Key: YOUR_API_KEY" \
     -H "Accept-Language: zh-CN" \
     https://api.example.com/data

# 2. 查看响应头
curl -I https://www.baidu.com

# 3. 查看完整交互过程（请求头+响应头）
curl -v https://httpbin.org/get

# 4. 只显示响应头状态码
**curl -s -o /dev/null -w "%{http_code}\n" https://example.com*
```

#### **场景 6：代理与网络调试**

```Shell
*# 1. 使用 HTTP 代理
curl -x http://127.0.0.1:8080 https://www.google.com

# 2. 使用 SOCKS5 代理
curl -x socks5://127.0.0.1:1080 https://twitter.com

# 3. 设置超时（连接超时 5 秒，总超时 30 秒）
curl --connect-timeout 5 -m 30 https://slow-api.com

# 4. 指定 DNS 服务器
curl --dns-servers 8.8.8.8 https://example.com

# 5. 忽略 SSL 证书（不推荐生产环境）
**curl -k https://self-signed-cert.example.com*
```

#### **场景 7：接口调试与性能分析**

```Shell
*# 显示完整的请求和响应细节（排错神器，能看到握手、请求头、响应头等全过程）
curl -v https://api.example.com/debug

# 查看接口响应耗时（常用于性能初步排查）
**curl -o /dev/null -s -w "总耗时: %{time_total} 秒\n" https://api.example.com*
```

#### **场景 8：模拟登录与 Cookie 管理**

```Shell
*# 第一步：登录并将 Cookie 保存到 cookies.txt
curl -c cookies.txt -d "username=admin&password=123456" https://example.com/login

# 第二步：携带保存的 Cookie 访问需要登录的页面
**curl -b cookies.txt https://example.com/user/info*
```

#### **场景 9：HTTP 证书认证**

```Shell
*# 发送客户端证书进行双向认证
curl --cert ./client.crt --key ./client.key https://your-server.com
- 注：如果证书和私钥合并在同一个 PEM 文件中，只需使用 -E 参数指定该文件即可。

# 指定 CA 证书验证服务器（单向认证：客户端验证服务器）
curl --cacert ./ca.crt https://your-server.com
**- 当服务器使用的是自签名证书，或证书链不完整时，可以通过 --cacert 参数指定受信任的 CA 根证书来进行安全验证*

# 跳过SSL证书验证
curl -k https://your-server.com
```

### 10\.5\.3 常见问题

#### **10\.5\.3\.1 URL 中的特殊字符**

```Shell
*# ❌ 错误：& 符号会被 shell 解释为后台运行
curl http://example.com?name=john&age=25

# ✅ 正确：用引号包裹
curl "http://example.com?name=john&age=25"

# ✅ 或转义特殊字符
**curl http://example.com?name=john\&age=25*
```

#### **10\.5\.3\.2 数据中包含单引号/双引号**

```Shell
*# 外部用单引号，内部用双引号
curl -d '{"name":"John \"Doe\"", "city":"Beijing"}' http://api.com

# 或使用转义
**curl -d "{\"name\":\"John Doe\"}" http://api.com*
```

#### **10\.5\.3\.3 HTTPS 证书问题**

```Shell
*# 临时跳过证书验证（测试用）
curl -k https://self-signed.com

# 指定 CA 证书文件进行验证服务端的证书
curl --cacert /path/to/ca-bundle.crt https://secure-site.com

# 指定发送客户端证书（双向认证）
**curl --cert client.pem --key key.pem https://api.com*
```

#### **10\.5\.3\.4 为什么 curl 能通，而 telnet 会不通？**

既然 curl 也要走传输层，为什么 telnet 会失败呢？

- 两者都走传输层：curl 和 telnet 在底层都要完成 TCP 三次握手。

- 区别在于应用层行为：curl 握手成功后，会立刻发送一个标准的 HTTP 请求，服务端收到后正常返回 200；而 telnet 握手成功后，什么都不发，只是傻等。某些服务端（或中间的 WAF、负载均衡器）发现连上来的客户端迟迟不发数据，或者发现这不是合法的 HTTP 请求，就会主动掐断传输层的 TCP 连接。

- 也可能是因为 Nginx 的配置或网络策略对“裸 TCP 连接”进行了限制。如果 Nginx 配置中只绑定了 127\.0\.0\.1，外部通过 telnet 测试真实 IP 时就会失败，但如果在服务器本地用 curl 测试则会返回 200；操作系统级别的防火墙也可能放行了 HTTP 协议，但对其他 TCP 探测（如 telnet）进行了拦截。

**总结来说：**
curl 并没有“跳过”传输层，它只是完美地完成了传输层的握手，并发送了合法的应用层数据。而 telnet 虽然也完成了传输层握手，但因为应用层没有后续动作，被服务端“嫌弃”并断开了连接，从而给你造成了“不通”的错觉。

### 10\.5\.4 总结

```Shell
*# 最常用命令速查
curl -O [url]           # 下载文件
curl -o [file] [url]    # 指定文件名下载
curl -X POST -d "data" [url]  # POST 表单
curl -H "Header: val" [url]   # 自定义头
curl -b cookies.txt [url]     # 使用 Cookie
curl -c cookies.txt [url]     # 保存 Cookie
curl -u user:pass [url]       # 基础认证
curl -L [url]           # 跟随重定向
curl -v [url]           # 详细调试
curl -s [url]           # 静默模式
curl -I [url]           # 仅头部信息
curl -k [url]           # 跳过 SSL 验证
curl -x proxy:port [url]      # 使用代理
curl -C - -O [url]      # 断点续传
**curl --limit-rate 1M [url]    # 限速下载*
```

|参数|含义|常用场景|
|---|---|---|
|`-X`|指定请求方法|发送 POST、PUT、DELETE 等请求|
|`-d`|发送数据（请求体）|POST 提交表单或 JSON 数据|
|`-H`|设置请求头|添加 Token 鉴权、指定 Content\-Type|
|`-i`|显示响应头和内容|查看完整响应信息（含状态码）|
|`-I`|仅显示响应头|快速检查接口状态（不下载内容）|
|`-v`|显示详细交互过程|排查请求失败、SSL 证书等网络问题|
|`-o` / `-O`|下载并保存文件|`-o` 自定义文件名，`-O` 使用原文件名|
|`-L`|跟随重定向|访问短链接或会自动跳转的接口|
|`-u`|用户名密码认证|访问需要 Basic Auth 认证的接口|

## 10\.6 文件查看器

### 10\.6\.1 cat：适合查看内容较少的小文件

将文件内容一次性全部输出到终端。

- 基本查看：cat filename\.txt

- 显示行号：cat \-n filename\.txt（查看代码或配置文件时非常有用）

- 合并文件：cat file1\.txt file2\.txt \> combined\.txt（将两个文件内容合并输出到一个新文件中）

- 追加文件内容：cat file1\.txt \>\> file2\.txt（将内容追加到目标文件的末尾）

- 创建文件：cat \> newfile\.txt（输入内容，按 Ctrl \+ D 组合键结束输入）

```Shell
*cat > newfile.txt
这是第一行内容
这是第二行内容
**（按 Ctrl + D 结束）*

# 显示文件内容行数
cat file.txt | wc -l
```

### 10\.6\.2 less：浏览大文件的最佳工具

**less** 不会一次性加载整个文件，因此即使查看几百 MB 的日志也不会卡顿。它支持上下翻页和搜索。

- 打开文件：less large\_log\.log

- 常用操作：

    - 空格键 / f：向下翻一页；b：向上翻一页

    - /关键词：向下搜索指定内容（按 n 跳转到下一个匹配项，N 查找上一个）

    - ?关键词：向上搜索指定的字符串

    - `j` 或 `向下箭头`：向下一行

    - `k` 或 `向上箭头`：向上一行

    - g：跳到文件开头；G：跳到文件末尾

    - v：调用默认的编辑器（通常是 vi）打开当前文件

    - q：退出查看

```Shell
*# 快速浏览一个巨大的日志文件，不会卡顿**
*less /var/log/syslog

# 显示行号并浏览文件
less -N /etc/nginx/nginx.conf

# 查看当前目录下所有文件，并支持上下翻页和搜索
ls -l | less

# 搜索日志中包含 "error" 的行，并保留高亮颜色
grep --color "error" /var/log/messages | less -R

# 防止长行自动折行，使用左右方向键横向查看
less -S large_file.txt

# 实时查看日志，还能保留 less 强大的翻页和搜索功能，
less +F /var/log/syslog

# 只显示包含 "ERROR" 的行，可以用 less 的上下键或翻页键查看
grep ERROR /var/log/syslog | less

# 加上 -n 显示行号，加上 -C 5 显示匹配行的前后各 5 行上下文（排查报错必备）
grep -n -C 5 "ERROR" /var/log/syslog | less

# 实时刷新过滤关键字，保留交互能力，推荐使用 less +F 配合管道
tail -f /var/log/syslog | less +/ERROR

-N：显示行号。这在排查代码或日志时非常有用。
-S：长行截断模式。默认情况下，长行会自动折行显示；加上 -S 后，长行会被截断，可以通过左右方向键来查看隐藏的部分，保持排版整洁。
-i：忽略大小写搜索。
-c：清屏重绘。在翻页时，先清空屏幕再显示新内容，避免屏幕闪烁。
-e：自动退出。当浏览到文件末尾时，自动退出 less。
-M：显示更详细的进度信息（如当前行号、总行数、百分比）。
-R：保留颜色输出。当结合管道符（|）使用，且前一个命令输出了带颜色的文本（如 grep --color）时，加上 -R 正常显示颜色。
```

### 10\.6\.3 head \& tail：只看开头或结尾

常用于快速确认文件格式，或者查看最新的日志记录。

- 查看前 10 行：head filename\.txt（默认显示 10 行）

- 查看前 20 行：head \-n 20 filename\.txt

- 查看末尾 50 行：tail \-n 50 app\.log

- 实时监控日志（运维高频用法）：tail \-f app\.log 或 tail \-100f app\.log

    - 加上 \-f 参数后，终端会实时滚动显示文件新增（100 行）的内容。

```Shell
*# 查看 mylog.log 的最后 10 行（默认）**
**tail mylog.log**

**# 查看 mylog.log 的最后 50 行**
**tail -n 50 mylog.log*

# 实时查看系统消息日志的更新
tail -f /var/log/messages

# 同时监控多个日志文件
tail -f /var/log/mail.log /var/log/apache/error_log

# 实时追踪日志，并只过滤出包含 "error" 关键字的行
tail -f /var/log/messages | grep "error"

# 提取文件的第 11 行到第 20 行（结合 head 命令）
head -n 20 file.txt | tail -n 10

-n <行数>：指定显示文件的最后几行。例如，tail -n 20 file.txt 会显示文件末尾的 20 行。
-f：实时追踪文件的变化（Follow）。当文件有新内容写入时，tail 会持续将新增加的内容输出到屏幕上。这在监控日志文件时非常实用。按 Ctrl+C 可以终止命令。
-c <字节数>：指定显示文件末尾的字节数。例如，tail -c 100 file.txt 会显示文件末尾的 100 个字节。
-r：逆序显示文件内容。即从文件的最后一行开始，反向输出到第一行。
-q：静默模式。当同时查看多个文件时，不显示文件名头部信息。
-v：详细模式。无论查看几个文件，始终在输出内容前显示文件名。
-s <秒数>：设置刷新间隔。通常与 -f 选项结合使用，指定每次检查文件更新的休眠秒数。
--pid=PID：与 -f 结合使用，当指定的进程（PID）结束后，tail 命令也会自动退出。
```

### 10\.6\.4 more \& tac \& nl：其他辅助查看命令

- more filename\.txt：老牌的分页查看工具，但只能向下翻页，功能不如 less 强大。

- tac filename\.txt：cat 的倒序版，从最后一行开始往前显示。

- nl filename\.txt：查看文件并自动添加行号（效果类似 cat \-n）。

## 10\.7 文件编辑器

### 10\.7\.1 nano：入门编辑器

Nano 的界面底部会直接显示快捷键提示，非常直观，适合新手快速修改文件。

- 打开/创建文件：nano filename\.txt

- 核心快捷键（通过 Ctrl 组合键操作）：

    - Ctrl \+ O：保存文件（按回车确认文件名）

    - Ctrl \+ X：退出编辑器（如果修改过未保存，会提示是否保存）

    - Ctrl \+ W：搜索关键词

---

### 10\.7\.2 vim：专业编辑器

#### 10\.7\.2\.1 普通模式 \(Normal Mode\) — 默认模式

打开 Vim 后默认进入的模式。在此模式下，你输入的字母不是用来打字的，而是用来发出指令（如移动光标、复制、删除等）。

核心功能与常用快捷键：

- 光标移动（手不离键盘区）：

    - h / j / k / l：分别对应 左 / 下 / 上 / 右

    - w / b：向后 / 向前跳一个单词

    - 0 / $：跳到当前行的行首 / 行尾

    - gg / G：跳到整个文件的首行 / 末行

- 编辑操作：

    - x：删除光标所在的单个字符

    - dd：删除（剪切）当前整行

    - 5dd：删除当前行及向下的 4 行（共删除 5 行）

    - :10,20d：删除第 10 行到第 20 行的内容

    - :\.,$d：删除从当前行（\. 代表当前行）到文件最后一行（$ 代表最后一行）

    - dw：删除一个单词

    - yy：复制（yank）当前整行

    - p / P：在光标后 / 前粘贴

    - u / Ctrl \+ r：撤销上一步操作 / 重做（反撤销）

---

**🛠️替换单个字符（小写 r）**

只替换光标下的 1 个字符，并且全程不需要进入插入模式，改完瞬间自动回到普通模式，非常高效。

- 操作：光标移到目标字符上 \-\> 按 r \-\> 输入新字符。

- 示例：文本是 hello，光标在 e 上，按 r 再按 a，文本立刻变成 hallo。

---

**🛠️连续替换多个字符（小写 r \+ 数字）**

如果你需要连续替换几个字符为同一个字符，可以给 r 加上数字前缀。

- 操作：数字 \+ r \+ 新字符。

- 示例：文本是 hello，光标在 e 上，输入 3r\*，文本会变成 h\*\*\*o（从光标处开始，连续 3 个字符都被替换成了 \*）。

---

**🛠️连续替换不同字符（大写 R）**

如果你想连续替换多个字符，且每个字符都不一样，就要用大写的 R。它会进入替换模式（Replace Mode），此时你输入的每一个字符都会直接覆盖（吃掉）光标后面原有的字符。

- 操作：按 R \-\> 连续输入新内容 \-\> 按 Esc 退出。

- 示例：文本是 hello world，光标在 h 上，按 R 然后输入 123，文本会变成 123o world（hel 被连续替换成了 123）。

- 注意：在替换模式下按退格键（Backspace），会恢复原本被替换掉的字符。

---

#### 10\.7\.2\.2 插入模式 \(Insert Mode\) — 打字模式

只有在这个模式下，Vim 才像普通的记事本一样，你输入的字符会直接变成文本内容。

如何进入与退出：

- 进入方式（在普通模式下按以下键）：

    - i：在光标前插入 \(insert\)

    - a：在光标后插入 \(append\)

    - o：在当前行下方新开一行插入 \(open\)

- 退出方式：

    - 按 Esc 键，随时退出插入模式，回到普通模式。

---

#### 10\.7\.2\.3 命令模式 \(Command\-line Mode\) — 执行指令

用于执行保存、退出、查找替换等复杂指令。

- 进入方式：在普通模式下按英文冒号 :，光标会跳到屏幕最底端等待输入。

- 常用指令（输入后按回车执行）：

    - :w：保存文件 \(write\)

    - :q：退出 \(quit\)

    - :wq 或 :x：保存并退出

    - :q\!：不保存，强制退出

    - /关键词：向下搜索指定内容（按 n 查找下一个，按 N 查找上一个）

    - :set nu：显示行号

    - :123：跳转到第 123 行

    > **`:x`**** 与 ****`:wq`**** 的区别**
    > 
    > 

    - `:wq` \(Write and Quit\)：无论文件是否被修改过，都会强制执行写入（保存）操作，然后退出。

    - `:x` \(eXit\)：会先检查文件是否有修改。只有在文件被修改过的情况下，它才会执行保存操作；如果文件没有任何改动，它会直接退出而不进行保存。

    因此，`:x` 命令更加智能，可以避免对未修改的文件进行不必要的写入，从而保持文件原有的修改时间戳。

---

**🛠️文本格式（换行符）设置为 Unix 格式**

1. 用 Vim 打开目标文件。

2. 确保处于普通模式。

3. 输入命令 **:set ff=unix** 并按回车（ff 是 fileformat 的简写）。

4. 输入命令 :wq 保存并退出。

保存后，Vim 会自动将文件中的 Windows 换行符（CRLF，即 \\r\\n）转换为 Unix 换行符（LF，即 \\n）。

**🔍 如何确认当前格式**

如果你想确认文件当前的换行格式，可以在普通模式下输入 **:set ff?** 并回车：

- 如果显示** fileformat=dos**，说明当前是 Windows 格式。

- 如果显示 **fileformat=unix**，说明已经是 Unix 格式。

---

**🛠️将 Tab 缩进转换为空格**

1. 打开文件，确保处于普通模式。

2. 设置 Tab 的宽度（比如设为 4 个空格）：
输入 :set tabstop=4 并回车。

3. 设置自动缩进的宽度（建议与 tabstop 保持一致）：
输入 :set shiftwidth=4 并回车。

4. 关键一步：开启用空格代替 Tab 的功能（可以忽略前面两步）：
输入 :set expandtab 并回车。

5. 执行替换：刷新并替换文件中已有的 Tab：
输入 :%retab\! 并回车（注意感叹号，它表示强制替换所有位置的 Tab，包括代码行中间的）。

6. 最后输入 :wq 保存退出。

**💡 永久生效**

将以下配置添加到你的 Vim 配置文件（\~/\.vimrc）中：

```Shell
*set tabstop=4
set shiftwidth=4
**set expandtab*
```

---

#### 10\.7\.2\.4 可视化模式 \(Visual Mode\) — 批量编辑

用于高亮选中一段文本块，以便进行批量复制或删除。

如何进入：

- 在普通模式下按 v：按字符进行选中。

- 在普通模式下按 V（大写）：按整行进行选中。

- 在普通模式下按 Ctrl \+ v：进行块状（矩形）选中。

---

**🛠️批量替换选中的单词**
假设你有一行代码：var name = "张三"; var age = 20;，你想把 name 快速改成 username。

1. 将光标移动到 name 的 n 上。

2. 按 v 进入字符可视化模式，按 w（或 e）选中整个单词 name。

3. 按 c（change，修改）或 d（delete，删除）。此时选中的文字被删除并进入插入模式。

4. 输入 username，按 Esc 退出。

---

**🛠️批量复制多行代码**

假设你想复制从第 10 行到第 20 行的代码。

1. 将光标移动到第 10 行。

2. 按 V 进入行可视化模式，此时整行会被高亮。

3. 按 j 或 10j 向下移动光标，高亮选中到第 20 行。

4. 按 y（yank，复制）。

5. 移动光标到目标位置，按 p（paste，粘贴）即可。
*\(注：如果想批量删除这些行，第 4 步按 d 即可\)*

---

**🛠️给多行代码批量添加 // 注释**
假设你有 3 行代码需要同时注释掉：

```Shell
*console.log(1);
console.log(2);
**console.log(3);*
```

1. 将光标定位在第 1 行的行首（字符 c 上）。

2. 按 Ctrl \+ v 进入块可视化模式。

3. 按 j 向下移动，选中这 3 行的行首（此时会看到一个竖向的矩形选区）。

4. 按大写 I（注意是 Shift \+ i，表示在选中块的开头插入）。此时只有第 1 行进入了插入模式，这是正常现象。

5. 输入 // （双斜杠加空格）。

6. 关键一步：输入完成后，连按两次 Esc 键。第一次退出插入模式，第二次触发 Vim 的“广播”机制，你会发现 //  自动添加到了下面所有选中行的行首。

---

**🛠️批量删除多行文本的相同前缀**

假设你从网页复制了一列带有序号的文本

```Shell
*1. 苹果
2. 香蕉
**3. 橘子*
```

快速去掉前面的 1\. 、2\.  等序号：

1. 将光标定位在 1 上，按 Ctrl \+ v。

2. 按 j 向下选中 3 行，再按 l 向右选中 3 列（刚好框住 1\. 、2\. 、3\.  这个矩形区域）。

3. 按 d 或 x，选中的矩形块内容会被瞬间全部删除，只保留水果名称。

---

**🔍 核心操作速查表**

|操作按键|功能描述|备注|
|---|---|---|
|`d` 或 `x`|删除（剪切）选中的区域|删除后可按 `p` 粘贴|
|`y`|复制（Yank）选中的区域|最常用的复制方式|
|`c`|修改（Change）选中的区域|删除选中内容并进入插入模式|
|`>` / `<`|批量缩进|选中代码块后按 `>` 向右整体缩进|
|`~`|切换大小写|将选中的英文字母批量反转大小写|

---

## 10\.8 grep

### 10\.8\.1 基本语法

**`grep`**（Global Regular Expression Print）是 Linux 中最强大且最常用的文本搜索工具。它就像一位高效的“文本侦探”，能够根据正则表达式或普通字符串，在文件或标准输入流中查找匹配模式，并将符合条件的行输出。

```Shell
grep [选项] "搜索模式" [文件/目录...]
```

如果不指定文件，`grep` 会从标准输入（如管道符传递的数据）读取内容。

### 10\.8\.2 核心常用选项

掌握以下几个高频选项，即可应对 80% 的日常搜索需求：

|选项|功能说明|
|---|---|
|\-i|忽略大小写（Case\-Insensitive）|
|\-v|反向匹配，显示不包含该模式的行|
|\-n|显示匹配行的行号|
|\-c|仅统计包含匹配模式的行数，不显示具体内容|
|\-r / \-R|递归搜索，遍历指定目录及其所有子目录|
|\-w|精确匹配整个单词，避免部分匹配（如搜 port 不会匹配 support）|
|\-l|仅显示包含匹配项的文件名（常用于多文件搜索）|
|\-E|启用扩展正则表达式（等同于 egrep，支持 \`|
|\-F|禁用正则，按纯文本字符串匹配（等同于 fgrep，性能更高）|

**上下文控制（排查报错神器）**

- `-A NUM`：显示匹配行及其后 NUM 行（After）

- `-B NUM`：显示匹配行及其前 NUM 行（Before）

- `-C NUM`：显示匹配行及其前后各 NUM 行（Context）

---

### 10\.8\.3 实战应用场景

**场景 1：系统进程排查（过滤自身干扰）**

在使用 `ps` 命令查找特定进程时，`grep` 的结果往往会把自己也包含进去。可以通过正则表达式巧妙排除：

```Shell
ps aux | grep "[n]ginx"
```

*原理：**`[n]ginx`** 会匹配 "nginx"，但 **`grep`** 自身的进程名是 **`[n]ginx`**，从而完美避开了自我匹配。*

**场景 2：日志分析与错误排查**

- 忽略大小写搜索报错：

```Shell
grep -i "error" /var/log/nginx/error.log
```

- 查看报错上下文：当发现一个关键错误（如 `critical`）时，查看其前后 3 行日志，帮助理解错误发生的背景：

```Shell
grep -C 3 "critical" /var/log/syslog
```

- 过滤常规日志：只看报错和警告，排除掉大量的常规 `INFO` 日志：

```Shell
grep -v "INFO" application.log
```

- 实时监控日志：结合 `tail -f` 实时追踪并高亮显示异常信息：

```Shell
tail -f /var/log/app.log | grep --color=auto "Exception"
```

**场景 3：代码与配置搜索**

- 递归搜索代码：在整个项目目录中查找包含 `TODO` 注释的 Python 文件，并显示行号：

```Shell
grep -rn "TODO" --include="*.py" ./src/
```

- 快速验证配置文件：在 `/etc` 目录下查找哪些配置文件包含了 `listen` 关键字，并仅输出文件名：

```Shell
grep -rl "listen" /etc/
```

- 过滤空行和注释行：查看纯净的配置文件内容：

```Shell
grep -v -E "^$|^#" config.conf
```

**场景 4：高级正则表达式匹配**

使用 `-E`（扩展正则）可以匹配复杂的格式：

- 匹配 IP 地址：

```Shell
grep -Eo "([0-9]{1,3}\.){3}[0-9]{1,3}" access.log
```

- 匹配多个关键字（逻辑或）：

```Shell
grep -E "ERROR|WARN|FAIL" app.log
```

- 匹配特定格式（如日期 YYYY\-MM\-DD）：

```Shell
grep -E "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])" logs.txt
```

**场景 5：结合其他命令进行数据处理**

- 统计访问量 Top 10 的 IP：

```Shell
grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" access.log | sort | uniq -c | sort -nr | head -10
```

- 批量替换文件内容（结合 `sed`）：

```Shell
grep -rl "old_string" /path/to/dir | xargs sed -i 's/old_string/new_string/g'
```

---

**💡 性能优化与最佳实践**

- 纯文本搜索用 `-F`：如果你只是搜索一个普通的字符串（不需要正则），加上 `-F` 选项可以跳过正则引擎的解析，显著提升搜索性能。

- 限制搜索范围：在递归搜索时，善用 `--include="*.js"` 和 `--exclude="*.min.js"` 来过滤文件类型，避免在无用文件上浪费时间。

- 注意 macOS 差异：macOS 默认使用的是 BSD 版本的 `grep`，部分选项（如 `--color`）可能与 Linux 的 GNU `grep` 不一致。若在 macOS 上遇到兼容性问题，建议通过 `brew install grep` 安装 GNU 版本（命令为 `ggrep`）。

## 10\.9 sftp

SFTP（SSH File Transfer Protocol）是一种基于 SSH 的安全文件传输协议，它对所有文件内容和命令进行加密，确保在传输过程中数据无法被破译。在 Linux 系统中，通常无需额外安装服务端（OpenSSH 自带），直接使用命令行即可进行安全的文件传输和管理。

- **连接到远程服务器**

使用 sftp 命令加上用户名和主机地址即可建立连接。连接成功后，命令行提示符会变为 sftp\>。

基本连接：sftp username@hostname（例如：sftp root@192\.168\.1\.100）

指定端口：如果服务器未使用默认的 22 端口，可使用 \-P 参数指定（例如：sftp \-P 2222 user@hostname）

使用密钥连接：通过 \-i 参数指定私钥文件进行免密或安全认证（例如：sftp \-i transfer\-key user@hostname）

注：首次连接时，系统会提示确认服务器指纹（Are you sure you want to continue connecting），输入 yes 即可。

- **目录浏览与切换**

进入 sftp\> 交互界面后，可以对本地和远程目录进行操作：

查看远程目录内容：`ls`

查看本地目录内容：`lls`

显示当前远程路径：`pwd`

显示当前本地路径：`lpwd`

切换远程目录：`cd /path/to/remote/dir`

切换本地目录：`lcd /path/to/local/dir`

- **文件与目录传输**

SFTP 提供了灵活的上传和下载命令，支持单个文件及整个目录的递归传输：

上传文件：`put local_file [remote_file]`（将本地文件上传到远程当前目录或指定路径）

上传目录：`put -r local_dir/`（使用 \-r 参数递归上传整个文件夹）

下载文件：`get remote_file [local_file]`（将远程文件下载到本地当前目录或指定路径）

下载目录：`get -r remote_dir/`（使用 \-r 参数递归下载整个文件夹）

- **远程文件与目录管理**

除了传输，SFTP 还支持直接在远程服务器上进行文件管理：

创建远程目录：`mkdir dir_name`

删除远程文件：`rm file_name`

删除远程目录：`rmdir dir_name`（注意：目录必须为空才能删除）

重命名远程文件：`rename old_name new_name`

修改远程文件权限：`chmod number path`

更改远程文件所有者：`chown user path`

- **批量执行与退出**

退出 SFTP 会话：输入 exit、quit 或按下 Ctrl \+ D 均可安全退出。

批量执行脚本：可以将多条 SFTP 命令写入一个文本文件（如 batch\.txt），然后使用 \-b 参数批量执行（例如：sftp \-b batch\.txt user@hostname）。

**💡 进阶建议**

大文件传输：对于大文件传输，推荐结合 rsync 命令使用，效率更高。

图形化工具：如果不习惯命令行，可以使用 FileZilla、WinSCP 等图形化客户端工具，它们底层同样基于 SFTP 协议。

## 10\.10 rsync

**rsync**（Remote Sync）是 Linux 系统中用于数据同步和备份的强大工具。它最大的特点是支持增量传输，即只传输两个文件之间修改过的部分，而不是每次都完整复制，这使得它在大量文件或频繁更新的场景下效率极高。

### **10\.10\.1\. 核心常用选项**

`rsync` 的强大在于其丰富的选项组合，以下是最常用的核心参数：

- `-a` \(archive\)：归档模式，等价于 `-rlptgoD`。它会递归同步目录，并保留几乎所有元数据（权限、时间戳、符号链接、属主等），是备份场景的首选。

- `-v` \(verbose\)：详细输出模式，在同步过程中显示文件列表和传输详情。

- `-z` \(compress\)：在传输时对文件进行压缩，减少网络带宽占用，非常适合远程同步。

- `-P` \(progress \+ partial\)：等价于 `--progress --partial`。不仅显示实时传输进度条，还能保留未传输完的部分文件，支持大文件的断点续传。

- `--delete`：镜像同步。删除目标路径中存在，但源路径中没有的多余文件，使目标与源完全一致。

- `--exclude=PATTERN`：排除符合指定模式的文件或目录（如 `--exclude=*.log` 过滤日志文件）。

- `-n` \(dry\-run\)：模拟运行。仅显示会执行的操作而不实际修改文件，常用于验证命令是否正确，防止误操作。

### **10\.10\.2\. 实战用法示例**

> **本地文件/目录同步**
> 
> 

- 同步目录内容：将 `source_dir` 目录下的所有内容同步到 `target_dir`（注意源路径末尾的 `/` 表示同步目录内的内容）：

```Shell
rsync -av /home/user/source_dir/ /tmp/target_dir/
```

- 同步目录本身：如果不加 `/`，则会将 `source_dir` 这个目录整体同步到目标路径下：

```Shell
rsync -av /home/user/source_dir /tmp/target_dir/
```

- 排除特定文件：同步时过滤掉所有的 `.log` 文件：

```Shell
rsync -av --exclude='*.log' /home/user/source_dir/ /tmp/target_dir/
```

> **远程同步（基于 SSH 协议）**
> 
> 

远程同步的格式为 `user@remote_host:remote_path`，默认通过 SSH 的 22 端口进行：

- 本地推送到远程（上传）：

```Shell
rsync -avzP /home/user/source_dir user@192.168.1.100:/data/backup
```

- 从远程拉取到本地（下载）：

```Shell
rsync -avzP user@192.168.1.100:/var/log /tmp/remote_logs
```

- 指定非默认 SSH 端口：如果远程服务器的 SSH 端口是 2222，需使用 `-e` 选项指定：

```Shell
rsync -avzP -e "ssh -p 2222" /home/user/file.txt user@192.168.1.100:/tmp/
```

> **镜像同步与增量备份**
> 
> 

- 完全镜像同步：使目标目录与源目录保持绝对一致，删除目标端的冗余文件：

```Shell
rsync -av --delete /home/user/source_dir/ /tmp/target_dir/
```

- 增量更新：仅同步源目录中新增或比目标端更新的文件，跳过目标端较新的文件：

```Shell
rsync -avh --update /home/user/source_dir/ /tmp/target_dir/
```

### **10\.10\.3\. 安全与进阶建议**

- 防范误删风险：`--delete` 选项非常强大但也极具破坏性。如果在目标路径写错的情况下使用，可能会导致重要数据被清空。建议在首次使用或执行关键同步前，加上 `-n` 参数进行模拟测试：

```Shell
rsync -av --delete -n /home/user/source_dir/ /tmp/target_dir/
```

- 限制传输带宽：如果在生产环境同步，为避免占满网络带宽影响其他业务，可以使用 `--bwlimit` 限制速率（单位 KB/s）：

```Shell
rsync -avz --bwlimit=10000 /path/to/source/ user@remote:/path/to/dest/
```

- 定时自动同步：结合 Linux 的 `crontab` 定时任务，可以轻松实现自动化备份。例如每天凌晨 0 点执行同步：

```Shell
0 0 * * * rsync -av /path/to/source/ /path/to/destination/
```

## 10\.11 scp

scp（Secure Copy）是基于 SSH 协议的安全文件传输工具，用于在本地主机和远程主机之间加密复制文件或目录。与 rsync 的增量同步不同，scp 每次都会完整复制文件，非常适合偶尔的文件传输或简单的备份操作。

### **10\.11\.1 核心常用选项**

- `-r` \(recursive\)：递归复制，用于传输整个目录及其子目录。

- `-P` \(Port\)：指定远程 SSH 端口号（注意是大写 `P`，默认端口为 22）。

- `-p` \(preserve\)：保留原文件的修改时间、访问时间和权限属性（注意是小写 `p`）。

- `-i` \(identity file\)：指定用于身份验证的 SSH 私钥文件路径。

- `-C` \(compress\)：启用压缩传输，适合大文件且网络带宽受限的场景。

- `-l` \(limit\)：限制传输带宽，单位为 Kbit/s，防止占满网络。

- `-v` \(verbose\)：详细模式，输出传输过程中的调试信息，常用于排查连接问题。

- `-q` \(quiet\)：静默模式，不显示传输进度条和警告信息。

### **10\.11\.2 实战用法示例**

> **上传文件/目录（本地 → 远程）**
> 
> 

- 上传单个文件：将本地文件上传到远程服务器的指定目录：

```Shell
scp local_file.txt user@192.168.1.100:/remote/path/
```

- 上传并重命名：在上传的同时指定目标文件名：

```Shell
scp ./config.yml root@server:/etc/myapp/new_config.yml
```

- 递归上传目录：使用 `-r` 参数上传整个文件夹：

```Shell
scp -r ./myproject root@server:/var/www/
```

- 保留属性上传：结合 `-r` 和 `-p` 参数，确保目录结构和文件权限完全一致：

```Shell
scp -rp ./website root@server:/var/www/html/
```

> **下载文件/目录（远程 → 本地）**
> 
> 

- 下载单个文件：将远程文件下载到本地当前目录：

```Shell
scp root@192.168.1.100:/var/log/syslog ./
```

- 递归下载目录：将远程服务器的整个日志目录下载到本地：

```Shell
scp -r root@server:/var/log/nginx ~/nginx-logs/
```

> **指定端口与密钥认证**
> 
> 

- 指定非标准 SSH 端口：如果远程服务器使用 2222 端口：

```Shell
scp -P 2222 ./file.txt user@remote:/path/
```

- 使用私钥免密传输：结合 `-i` 参数指定密钥文件：

```Shell
scp -i ~/.ssh/id_rsa ./file.txt user@remote:/path/
```

### **10\.11\.3 安全与进阶建议**

- 避免使用 root 用户：出于安全考虑，建议优先使用普通用户进行传输，避免直接使用 root 权限：

```Shell
scp file.txt deploy@host:/path/  *# 推荐做法*
```

- 保护私钥文件权限：确保用于认证的私钥文件权限设置为 `600`，防止被其他用户读取：

```Shell
chmod 600 ~/.ssh/id_ed25519
```

- **大文件传输防中断**：在使用 `scp` 传输超大文件时，如果终端休眠或网络波动，传输可能会终止。建议在 `tmux` 或 `screen` 会话中执行，以维持后台会话。

- **注意覆盖风险**：`scp` 在复制同名文件时会默认直接覆盖，且没有任何警告提示。在执行传输前，请务必核对目标路径是否正确。

## 10\.12 ftp

ftp（File Transfer Protocol）是用于在网络上进行文件传输的标准协议客户端工具。与 SFTP 和 SCP 不同，标准 FTP 协议以明文传输所有数据（包括用户名和密码），安全性较低，目前主要用于访问传统的公共资源或旧版服务器。

### 10\.12\.1 连接与登录

在终端输入 `ftp` 加上主机地址即可建立连接，连接成功后命令行提示符会变为 `ftp>`。

- 基本连接：`ftp hostname` 或 `ftp IP地址`（例如：`ftp 192.168.1.100`）

- 匿名登录：许多公共 FTP 服务器支持匿名访问，用户名通常为 `anonymous`，密码可输入邮箱地址或直接按回车。

- 常用启动选项：

    - `-d`：启用调试模式，显示客户端与服务器之间传递的所有命令和响应，便于排错。

    - `-i`：关闭交互提示，在批量传输文件时不会对每个文件进行确认询问。

    - `-n`：禁止初始连接时的自动登录，通常用于脚本中手动控制登录流程。

### 10\.12\.2 目录浏览与切换

进入 `ftp>` 交互界面后，可以使用以下命令管理本地和远程目录：

- 查看远程目录内容：`ls`（简短列表）或 `dir`（详细列表）

- 查看本地目录内容：`lls`

- 显示当前远程路径：`pwd`

- 切换远程目录：`cd /path/to/remote/dir`

- 切换本地目录：`lcd /path/to/local/dir`

### 10\.12\.3 文件传输操作

FTP 传输前务必设置正确的传输模式，否则可能导致文件损坏：

- 设置传输模式：

    - `binary`（或 `bin`）：二进制模式，原样传输文件，适合图片、压缩包、程序等非文本文件。

    - `ascii`（或 `asc`）：ASCII 模式，会进行字符转换，仅适合纯文本文件。

- 下载文件：`get remote_file [local_file]`（从远程下载文件到本地，可指定本地保存路径或重命名）

- 批量下载：`mget *.txt`（下载匹配通配符的多个文件，建议配合 `-i` 选项关闭逐个确认提示）

- 上传文件：`put local_file [remote_file]`（将本地文件上传到远程当前目录）

- 批量上传：`mput *.log`（上传匹配通配符的多个本地文件）

### 10\.12\.4 远程文件与目录管理

- 创建远程目录：`mkdir dir_name`

- 删除远程目录：`rmdir dir_name`（注意：目录必须为空才能删除）

- 删除远程文件：`delete file_name`

- 批量删除远程文件：`mdelete *.tmp`

- 重命名远程文件：`rename old_name new_name`

### 10\.12\.5 会话控制与退出

- 断开连接但保留 ftp 程序：`close`

- 断开连接并完全退出 ftp 程序：`bye` 或 `quit`

- 临时执行本地 Shell 命令：在命令前加 `!`（例如：`!ls` 会在本地执行 ls 命令），输入 `exit` 可返回 ftp 交互界面。

### 💡 安全与进阶建议

- 安全警告：由于 FTP 是明文传输，切勿用于传输包含密码、密钥等敏感信息的文件。在条件允许时，应优先使用基于 SSH 的 `sftp` 或 `scp` 协议。

- 防火墙与被动模式：如果在 FTP 交互过程中遇到列表正常但无法传输文件的情况，可能是防火墙阻止了数据连接。可以在交互模式下输入 `passive` 命令来切换到被动模式，以解决此问题。

- 批量自动化：可以将多条 FTP 命令写入一个文本文件（如 `ftp_commands.txt`），然后使用 `-s` 参数批量自动执行（例如：`ftp -s:ftp_commands.txt hostname`）。

## 10\.13 ssh

**ssh**（Secure Shell）是一种加密的网络协议，用于在不安全的网络上为远程登录或执行命令提供安全的通信通道。它是 Linux/Unix 系统管理的核心工具，允许用户通过远程终端与服务器建立加密连接并执行命令。

### 10\.13\.1 核心常用选项

`ssh` 命令支持丰富的选项，以下是最常用的核心参数：

- `-p` \(port\)：指定远程 SSH 服务器监听的端口号。默认为 22，若修改了默认端口则必须指定。

- `-i` \(identity file\)：指定用于身份验证的私钥文件路径，常用于免密登录场景。

- `-l` \(login name\)：指定登录远程主机的用户名。

- `-v` \(verbose\)：显示详细的连接和验证过程日志，非常适合用于排查连接失败的问题。

- `-C` \(compress\)：启用数据压缩传输，减少网络带宽占用，在弱网环境下可显著提升响应速度。

- `-f` \(fork\)：在后台运行 SSH 会话，常用于执行离线任务或建立持久化隧道。

- `-N` \(no command\)：禁止执行远程命令，仅用于端口转发等建立隧道的场景。

- `-L` \(local forward\)：进行本地端口转发，将本地端口请求转发到远程目标主机。

- `-R` \(remote forward\)：进行远程端口转发，将远程主机的端口请求转发到本地。

- `-D` \(dynamic forward\)：启用动态端口转发（SOCKS 代理），通过远程设备转发网络请求。

### 10\.13\.2 实战用法示例

> **基础登录与远程执行**
> 
> 

- 基本登录：使用 `用户名@主机地址` 格式（最常用）：

```Shell
ssh root@192.168.1.100
```

- 使用 `-l` 参数登录：将用户名和主机地址分开写：

```Shell
ssh -l admin 192.168.1.105
```

- 指定非标准端口：如果远程服务器端口改为 12345：

```Shell
ssh -p 12345 admin@192.168.1.105
```

- 直接执行远程命令：无需进入交互式终端，直接在本地查看远程服务器的系统版本：

```Shell
ssh admin@192.168.1.105 "cat /etc/os-release"
```

> **密钥认证与免密登录**
> 
> 

- 指定私钥登录：使用 `-i` 参数指定本地私钥路径：

```Shell
ssh -i ~/.ssh/mykey admin@192.168.1.105
```

- 配置免密登录流程：

    1. 在本地生成密钥对：`ssh-keygen -t rsa`

    2. 将公钥复制到远程服务器：`ssh-copy-id user@hostname`

    3. 之后再次使用 `ssh user@hostname` 即可免密码登录。

> **端口转发与代理（进阶）**
> 
> 

- 本地端口转发：访问本地 8080 端口等同于访问远程设备的 80 端口（常用于访问内网 Web 服务）：

```Shell
ssh -L 8080:localhost:80 admin@192.168.1.100
```

- 反向端口转发：让远程设备通过其 9090 端口访问本地 90 端口的服务：

```Shell
ssh -R 9090:localhost:90 admin@192.168.1.100
```

- 建立 SOCKS 代理：将本地 1080 端口作为 SOCKS 代理，配置浏览器或系统代理为 `127.0.0.1:1080` 即可通过远程设备上网：

```Shell
ssh -D 1080 admin@192.168.1.100
```

> **持久化隧道与后台运行**
> 
> 

- 建立后台持久化隧道：结合 `-f` 和 `-N` 选项，在后台建立仅用于转发的隧道，避免频繁断开重连：

```Shell
ssh -fN -L 8080:localhost:80 admin@192.168.1.100
```

### 10\.13\.3 连接异常排查与安全建议

- **排查连接失败**：若连接失败，使用 `-v` 选项查看详细日志定位问题（如 `ssh -v admin@192.168.1.105`）。

    - 提示 `Connection refused`：检查远程 SSH 服务状态（`systemctl status sshd`）或防火墙是否开放对应端口。

    - 提示 `Host key verification failed`：远程主机密钥变更导致，可删除本地 `~/.ssh/known_hosts` 文件后重新连接。

    - 提示 `Permission denied`：检查密码是否正确，或确认 `/etc/ssh/sshd_config` 中 `PasswordAuthentication` 是否设为 `yes`。

- **防止连接闲置断开**：编辑本地 `~/.ssh/config` 文件，添加 `ServerAliveInterval 60`，表示每 60 秒发送一次心跳包，防止因网络闲置导致 SSH 自动断开。

- **私钥权限保护**：确保用于认证的私钥文件权限设置为 `600`（`chmod 600 私钥文件`），防止因权限过宽导致密钥认证失败。

## 10\.14 lsof

**lsof**（List Open Files）是 Linux 系统中用于监控进程与打开文件关系的强大命令行工具。在 Linux “一切皆文件”的设计理念下，它不仅用于查看常规文件，还能检测网络连接、设备文件、目录等资源。

### **10\.14\.1 基本语法**

`lsof` 的基本语法格式为 `lsof [options] [filename]`。由于它需要访问核心内存和各种系统文件，通常必须以 `root` 用户身份运行才能获取完整信息。

执行 `lsof` 后，输出结果包含以下核心字段：

- COMMAND：进程的名称。

- PID：进程标识符。

- USER：进程所有者。

- FD：文件描述符。例如 `cwd`（当前工作目录）、`txt`（程序代码或共享库）、`mem`（内存映射文件）；数值加字母（如 `10u`）表示打开该文件的描述符编号及模式（`u` 为读写模式）。

- TYPE：文件类型。如 `REG`（常规文件）、`DIR`（目录）、`CHR`（字符设备）、`IPv4`（网际协议套接字）等。

- DEVICE：指定磁盘的名称或设备号。

- SIZE/OFF：文件的大小或文件偏移量。

- NODE：索引节点（文件在磁盘上的标识）。

- NAME：打开文件的确切名称或路径。

### **10\.14\.2 常用命令示例**

> **按进程或用户筛选**
> 
> 

- 查看特定进程打开的文件：使用 `-p` 参数指定进程 ID。

```Shell
lsof -p 1234
```

- 查看特定用户打开的文件：使用 `-u` 参数指定用户名。

```Shell
lsof -u username
```

- 按进程名筛选：使用 `-c` 参数显示 COMMAND 列中包含指定字符的进程。

```Shell
lsof -c nginx
```

- 获取整个系统当前打开的句柄总数。

```Shell
lsof | wc -l
```

> *注：由于 **`lsof`** 需要访问核心内存和各种文件，通常需要 **`root`** 权限才能获取完整的系统级统计结果。*
> 
> 

- 统计特定进程打开的句柄数。

```Shell
lsof -p 1234 | wc -l
```

> *补充说明：如果不加 **`-p`** 参数，**`lsof`** 默认会列出该进程及其所有线程打开的文件。如果需要严格只统计进程级别（排除线程），可以加上 **`-a -K`** 参数组合。*
> 
> 

- 统计系统中占用句柄最多的进程（Top N）。

```Shell
lsof -n | awk '{print $2}' | sort | uniq -c | sort -nr

*lsof -n：列出所有打开的文件，-n 参数表示不将 IP 地址转换为域名，能显著提升执行速度。*
*awk '{print $2}'：提取输出结果的第二列，即进程 ID（PID）。*
*sort | uniq -c：对 PID 进行排序并统计每个 PID 出现的次数（即打开的句柄数）。*
*sort -nr：按照统计出的次数进行数字倒序排列，句柄最多的进程会显示在最前面。*
```

---

> **按文件或目录筛选**
> 
> 

- 查看打开指定文件的进程：直接在命令后指定文件路径。

```Shell
lsof /bin/bash
```

- 查看目录下被打开的文件：使用 `+d` 仅搜索指定目录，或使用 `+D` 递归搜索目录下的所有子目录（耗时较长）。

```Shell
lsof +d /var/log
lsof +D /var/log
```

---

> **网络与端口排查**
> 
> 

- 查看所有网络连接：使用 `-i` 参数列出所有符合条件的网络进程。

```Shell
lsof -i
```

- 查看特定端口占用：结合端口号排查冲突。

```Shell
lsof -i :8080
```

- 组合筛选：结合 `-a` 参数表示“与”逻辑。例如，查找用户 root 打开的所有网络连接。

```Shell
lsof -a -u root -i
```

### **10\.14\.3 典型实战应用场景**

#### **场景一：排查端口占用冲突**

当启动服务提示端口被占用时，可通过 `lsof -i :端口号` 找到占用进程的 PID，随后使用 `kill -9 <PID>` 强制结束该进程。

#### **场景二：恢复误删文件**

如果在 Linux 中误删了文件，只要该文件仍被某个进程打开，就可以通过 `lsof | grep deleted` 找到其 PID 和 FD，然后利用 `/proc/<PID>/fd/<FD>` 将文件完整拷贝恢复。

`lsof | grep deleted` 是 Linux 系统中一个非常经典的排查命令组合。它主要用于查找已经被删除（通过 `rm` 等命令），但由于仍有进程持有该文件的句柄（File Descriptor），导致磁盘空间未被真正释放的文件。

**💡 为什么会出现这种情况？**

在 Linux 中，当你使用 `rm` 删除一个文件时，系统只是移除了该文件的目录项（dentry）。如果此时仍有进程正在读写这个文件（即文件描述符未关闭），内核就不会释放该文件占用的 inode 和数据块。这就导致了一个常见的故障现象：使用 `df -h` 查看时磁盘空间显示已满（100%），但使用 `du -sh` 统计目录时，却找不到对应的大文件。

---

**🔍 命令输出解读**

执行该命令后，通常会看到类似如下的输出：

```Shell
COMMAND   PID   USER   FD   TYPE DEVICE   SIZE/OFF    NODE NAME
java     3456   root   23w  REG  202,1 2147483648   12345 /var/log/app/access.log (deleted)
```

关键信息包括：

- COMMAND / PID：占用该文件的进程名称和进程 ID。

- FD \(File Descriptor\)：文件描述符，例如 `23w` 表示 23 号描述符，`w` 代表写入模式。

- SIZE/OFF：该已删除文件实际占用的磁盘空间大小（单位为字节）。

- NAME：文件原路径，末尾带有 `(deleted)` 标记，表明文件已被删除但句柄未释放。

---

**🛠️ 如何处理与释放空间？**

找到这些“幽灵文件”后，可以根据业务需求采取以下策略来释放磁盘空间：

1. 优雅重启服务（推荐用于核心业务）

如果占用文件的是日志服务、数据库或 Web 服务等核心进程，直接强杀可能导致数据丢失。建议通过发送重载信号或重启服务来关闭旧的文件句柄：

- Nginx: `nginx -s reopen`

- Java/Log4j: `kill -USR1 <PID>`

- 通用服务: `systemctl restart <service_name>`

2. 强制终止进程（适用于非核心进程）

如果确认该进程可以安全停止，可以使用 `kill` 命令强制结束，空间会立即释放：

```Shell
kill -9 <PID>
```

> *注意：**`kill -9`** 是强制终止，可能会导致未保存的数据丢失，请务必在确认不影响业务后使用。*
> 
> 

3. 临时截断释放空间（无需重启进程）
在生产环境中，如果进程绝对不能中断，你可以通过清空 `/proc` 下对应的文件描述符来立即释放空间。这不会关闭进程的文件描述符，而是将文件内容截断为 0：

```Shell
echo "" > /proc/<PID>/fd/<FD>
*# 例如：echo "" > /proc/3456/fd/23*
```

---

**🚨 附加场景：误删文件恢复**

除了排查磁盘空间，这个命令还能用于误删文件的紧急恢复。只要文件被删除后仍有进程持有其句柄（黄金窗口期），你就可以通过 `/proc/<PID>/fd/<FD>` 将文件完整拷贝回来：

```Shell
cp /proc/<PID>/fd/<FD> /path/to/recovered_file
```

#### **场景三：排查资源泄漏与卸载失败**

当怀疑应用程序耗尽了文件描述符，或在卸载文件系统（umount）失败时，可以使用 `lsof` 统计打开的文件数目或检查挂载点，找出占用资源的进程并妥善处理。

## 10\.15 历史操作记录

### **使用 ****`history`**** 命令（最常用）**

直接输入 `history` 会列出所有历史命令。如果记录太多，可以配合 `tail` 只看最近的几条：

```Shell
history | tail -n 20   *# 查看最近 20 条命令*
```

### **快捷键搜索（极力推荐 ⚡）**

这是日常操作中最快、最优雅的方式，无需离开当前输入行：

- `Ctrl + r`：进入反向搜索模式。开始输入你记得的命令片段，终端会自动匹配最近一次执行过的该命令。按 `Enter` 直接执行，或按 `右方向键` 将其放到命令行进行编辑。

- `Ctrl + g`：如果在 `Ctrl + r` 搜索时按错了或想退出，按此键取消搜索。

### **方向键与前缀匹配**

- `↑` / `↓` 方向键：逐条翻阅上一条/下一条命令。

- 输入前缀 \+ `↑`：比如你先输入 `git`，然后按 `↑` 键，终端只会在以 `git` 开头的历史命令中切换，过滤掉其他无关命令，非常高效。

### **结合 ****`grep`**** 精准查找**

如果你只记得命令中包含某个关键词，但不确定完整内容：

```Shell
history | grep "关键词"
```

### **按编号执行历史命令**

`history` 输出的每一行前面都有编号（如 `1024 ls -la`）。你可以直接用 `!` 加上编号来执行：

```Shell
!1024    *# 直接执行编号为 1024 的命令*
!!       *# 执行上一条命令（等同于按 ↑ 然后回车）*
!$       *# 代表上一条命令的最后一个参数*
```

**💡 进阶小贴士：让历史记录更好用**

默认情况下，Linux 可能只保存 500 或 1000 条历史，且不同终端窗口之间不共享。你可以在 `~/.bashrc` 或 `~/.zshrc` 中加入以下配置来优化：

```Shell
*# 增加历史记录保存上限*
export HISTSIZE=10000
export HISTFILESIZE=20000

*# 忽略重复的连续命令（如连续按两次 ls）*
export HISTCONTROL=ignoredups

*# 让多个终端窗口实时共享历史记录*
shopt -s histappend
PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"
```

> *修改后记得执行 **`source ~/.bashrc`** 使其生效。*
> 
> 

## 10\.16 文件压缩

### tar \+ gzip（最常用，推荐）

这是日常备份和网络传输中最推荐的格式，能够很好地平衡压缩速度与压缩率。

- 压缩命令：`tar -czvf 压缩包名.tar.gz 要压缩的文件或目录`

- 解压命令：`tar -xzvf 压缩包名.tar.gz`

- 参数详解：

    - `-c` \(create\)：创建新的归档文件。

    - `-z` \(gzip\)：调用 gzip 算法进行压缩或解压。

    - `-v` \(verbose\)：显示详细的处理过程。

    - `-f` \(file\)：指定归档文件的名称（该参数必须紧跟文件名）。

    - `-x` \(extract\)：从归档文件中提取内容。

- 示例：将 `test/` 目录压缩为 `test.tar.gz`：`tar -czvf test.tar.gz test/`

### tar \+ bzip2（高压缩率）

适合大文件或需要长期存储的场景，压缩率高于 gzip，但速度相对较慢。

- 压缩命令：`tar -cjvf 压缩包名.tar.bz2 要压缩的文件或目录`

- 解压命令：`tar -xjvf 压缩包名.tar.bz2`

- 参数说明：将 `-z` 替换为 `-j`，表示使用 bzip2 算法。

### tar \+ xz（极限压缩）

提供极高的压缩率，但压缩和解压过程较慢，且需要消耗较多内存和 CPU 资源。

- 压缩命令：`tar -cJvf 压缩包名.tar.xz 要压缩的文件或目录`

- 解压命令：`tar -xJvf 压缩包名.tar.xz`

- 参数说明：使用大写 `-J` 表示调用 xz 算法。

### zip / unzip（跨平台兼容）

如果需要与 Windows 系统进行文件交互，`zip` 是最合适的选择。

- 压缩命令：`zip -r 压缩包名.zip 要压缩的文件或目录`

- 解压命令：`unzip 压缩包名.zip`

- 参数说明：`-r` 表示递归处理，即压缩整个目录及其子目录。

- 示例：将 `test/` 目录压缩为 `test.zip`：`zip -r test.zip test/`

### 单文件压缩（gzip / bzip2 / xz）

如果只需要压缩单个文件而不涉及目录打包，可以直接使用这些命令。

- 压缩命令：`gzip 文件名`、`bzip2 文件名` 或 `xz 文件名`

- 解压命令：`gunzip 文件名.gz`、`bunzip2 文件名.bz2` 或 `unxz 文件名.xz`

- ⚠️ 注意事项：使用这种方式压缩后，原始文件会被替换（删除），仅保留压缩后的文件，`gzip -k 文件名`（保留原文件）。

### 💡 实用进阶技巧

- 解压到指定目录：在解压时加上 `-C` 参数，例如 `tar -xzvf test.tar.gz -C /opt/`，可将文件解压到 `/opt/` 目录下。

- 排除特定文件：在备份时排除日志等不需要的文件，使用 `--exclude` 参数，例如 `tar -czvf backup.tar.gz --exclude='*.log' /home/user/`。

- 查看压缩包内容（不解压）：使用 `tar -tzf 压缩包名.tar.gz` 或 `unzip -l 压缩包名.zip` 即可预览内部文件列表。

## 10\.17 文件创建

### `touch` — 创建空文件

`touch` 是最简单、最常用的创建文件命令。如果文件不存在，则创建一个 0 字节的空文件；如果文件已存在，则只更新其时间戳，不会清空内容。

```Bash
*# 创建单个空文件*
touch test.txt

*# 一次创建多个文件*
touch file1.txt file2.txt file3.txt

*# 使用花括号简写*
touch {a,b,c}.txt

*# 指定路径创建*
touch /home/user/demo.log

*# 创建隐藏文件（以 . 开头）*
touch .hiddenfile
```

> 💡 `touch` 还支持设置指定时间戳：`touch -t 202609041200.00 test.txt`
> 
> 

---

### `>` — 创建或清空文件

单独使用 `>` 可以快速创建一个空文件。但如果文件已存在，会清空原有内容，这一点需要特别注意。

```Bash
*# 创建空文件（已存在则清空）*
> newfile.txt

*# 带内容创建*
echo "Hello Linux" > newfile.txt
```

---

### `echo` — 创建文件并写入内容

`echo` 适合快速向文件中写入一行文本。使用 `>` 为覆盖写入，使用 `>>` 为追加写入。

```Bash
*# 覆盖写入（文件不存在则创建）*
echo "Hello World" > hello.txt

*# 追加写入（不会覆盖已有内容）*
echo "第二行内容" >> hello.txt

*# 写入变量内容*
name="Linux"
echo "Welcome to $name" > welcome.txt
```

---

### `cat` — 交互式创建文件（适合多行内容）

`cat` 配合重定向可以交互式地输入多行内容，输入完成后按 `Ctrl + D` 保存退出。

```Bash
*# 交互式输入内容*
cat > test.txt
第一行内容
第二行内容
第三行内容
（按 Ctrl + D 保存退出）

*# 使用 Here Document 一次性写入多行*
cat > test.txt << EOF
第一行
第二行
第三行
EOF

*# 追加内容*
cat >> test.txt
（输入内容后按 Ctrl + D）
```

---

### `printf` — 格式化写入

`printf` 比 `echo` 更精确，支持换行符 `\n`、制表符 `\t` 等格式控制。

```Bash
*# 写入多行内容*
printf "Line 1\nLine 2\nLine 3\n" > formatted.txt

*# 带格式输出*
printf "姓名: %s\n年龄: %d\n" "张三" 25 > info.txt
```

---

### `vim` / `nano` — 文本编辑器

适合需要编辑复杂内容的场景。打开一个不存在的文件时会自动创建。

**vim / vi：**

```Bash
vim test.txt
*# 按 i 进入插入模式 → 输入内容 → 按 Esc → 输入 :wq 保存退出*
```

**nano（更简单）：**

```Bash
nano test.txt
*# 直接输入内容 → Ctrl + O 保存 → Enter 确认 → Ctrl + X 退出*
```

---

### `dd` — 创建指定大小的文件

`dd` 可以从特殊设备文件读取数据来创建指定大小的文件，常用于测试。

```Bash
*# 创建一个 10MB 的空文件*
dd if=/dev/zero of=test.dat bs=1M count=10

*# 创建一个 1KB 的随机数据文件*
dd if=/dev/urandom of=random.dat bs=1K count=1
```

---

### `cp` — 通过复制创建文件

通过复制已有文件来创建新文件。

```Bash
cp source.txt newfile.txt
```

---

### 总结速查表

|需求|推荐命令|示例|
|---|---|---|
|创建空文件|touch|touch file\.txt|
|创建并写入单行|echo|echo "内容" \> file\.txt|
|交互式写入多行|cat|cat \> file\.txt|
|格式化写入|printf|printf "行1\\n行2\\n" \> file\.txt|
|编辑复杂内容|vim / nano|vim file\.txt|
|创建指定大小文件|dd|dd if=/dev/zero of=f bs=1M count=10|
|快速清空文件|\>|\> file\.txt|

> 日常使用中，`touch` 创建空文件、`echo` 写入内容、`vim/nano` 编辑文件这三种方式最为常见，掌握它们基本就能应对绝大多数场景。
> 
> 

---

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux系统监控-CPU]]
- [[Linux系统监控-网络]]

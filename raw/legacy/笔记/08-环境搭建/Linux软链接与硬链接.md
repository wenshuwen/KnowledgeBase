---
type: note
tags: [Linux] [文件系统]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Linux 软链接与硬链接

> 📌 来源：[[Test-测试经验总结-原文]] ｜ LINUX章-软链接&硬链接 小节

在 Linux 文件系统中，软链接（Symbolic Link，也叫符号链接）和硬链接（Hard Link）是两种不同的文件引用方式。理解它们的核心在于理解 Linux 底层的 inode（索引节点） 机制。

简单来说：硬链接是同一个文件的“多个名字”，而软链接是一个指向另一个文件路径的“快捷方式”。

## 9\.1 核心区别对比

|特性|硬链接 \(Hard Link\)|软链接 \(Symbolic Link\)|
|---|---|---|
|底层本质|与原文件共享同一个 inode|有独立的 inode，内容存储的是目标文件的路径|
|跨文件系统|❌ 不能跨分区/文件系统|✅ 可以跨分区/文件系统|
|链接目录|❌ 不能对目录创建硬链接（防循环）|✅ 可以对目录创建软链接|
|删除原文件后|硬链接依然有效（只要还有≥1 个硬链接，数据就不丢）|软链接失效（变成断链/Dangling）|
|文件大小|与原文件完全一致|存储的是路径字符串的长度|
|相对/绝对路径|不涉及路径概念|支持相对路径和绝对路径|
|创建命令|`ln 源文件 硬链接名`|`ln -s 源文件 软链接名`|

## 9\.2 实际操作演示

```Shell
*# 1. 创建一个原文件
echo "Hello Linux" > original.txt

# 2. 创建硬链接
ln original.txt hard_link.txt

# 3. 创建软链接
ln -s original.txt soft_link.txt

# 4. 查看 inode 编号 (关键验证)
ls -li original.txt hard_link.txt soft_link.txt
# 输出示例：
# 1234567 -rw-r--r-- 2 user user 12 ... original.txt      <-- inode 相同，链接数为 2
# 1234567 -rw-r--r-- 2 user user 12 ... hard_link.txt     <-- inode 相同，链接数为 2
# 1234568 lrwxrwxrwx 1 user user 12 ... soft_link.txt -> original.txt <-- inode 不同，以 l 开头

# 5. 删除原文件
rm original.txt

# 6. 验证结果
cat hard_link.txt   # 正常输出: Hello Linux
**cat soft_link.txt   # 报错: No such file or directory (断链)*
```

## 9\.3 常见使用场景

**💡 什么时候用软链接？（最常用）**

- 版本管理/路径映射：比如 `/usr/local/bin/python` 软链接到 `/usr/bin/python3.9`，升级时只需改软链接。

- 跨分区共享数据：在 `/home` 分区建个文件夹，软链接到 `/opt` 分区。

- 桌面快捷方式：Windows 的 `.lnk` 概念在 Linux 中就是软链接。

- 库文件管理：`libssl.so` \-\> `libssl.so.1.1` \-\> `libssl.so.1.1.1f`。

**💡 什么时候用硬链接？**

- 防误删备份：给重要文件建个硬链接，即使不小心 `rm` 了原文件，数据还在。

- 节省空间：多个大文件内容完全一样，用硬链接只占一份磁盘空间（比 `cp` 省空间）。

- 快照机制：某些备份工具（如 `rsnapshot`）利用硬链接实现增量备份，秒级完成。

**⚠️ 避坑指南**

- 不要对目录建硬链接：Linux 禁止普通用户这么做，因为会破坏文件系统的树状结构，导致 `fsck` 无法修复。

- 软链接的路径陷阱：如果用相对路径创建软链接，移动软链接后，它可能就会断链。建议尽量用绝对路径创建软链接。

- 复制 vs 链接：`cp` 是复制数据（占双倍空间），`ln` 只是加个指针（几乎不占空间）。

- 查看链接数：用 `stat 文件名` 或 `ls -l` 看第二列的数字，那就是硬链接计数。

**总结**：日常使用 99% 的情况用软链接 \(ln \-s\)；只有在明确需要“多入口、防删除、省空间”且在同一分区时，才考虑硬链接。

---

---

## 相关笔记
- [[08-环境搭建]]
- [[Linux用户权限管理]]
- [[Linux系统监控-磁盘]]

---
title: macOS命令行与无头浏览器踩坑
type: concept
domain: 环境与工具
created: 2026-09-13
updated: 2026-09-13
sources: [raw/notes/2026-09-13 面试助手工程化与会话经验会话要点.md]
tags: [tooling, pitfall, git]
confidence: high
status: active
publish: false
---

# macOS命令行与无头浏览器踩坑

做 Web 端验证与工程化时反复踩到的环境坑，全部实测复现过。共同点：**失败方式是静默的**——返回空结果、假阳性或 0 字节输出，而不是报错。

## 命令行

| 坑 | 现象 | 正确做法 |
|---|---|---|
| BSD grep 的 BRE 不支持 `\|` 交替 | `grep "a\|b"` **静默返回 0 条**，极易误判"没有匹配" | 多模式用 `grep -E "a\|b"`，或逐个 `grep -cF` |
| `git add` 路径校验是整体的 | 任一路径不存在 → **整条命令失败、一个文件都不暂存** | 删除过的文件不要留在 add 列表；提交前 `git status` 复核 |
| 后台进程随调用回收 | `(cmd &)` 起的服务在当前 shell 调用结束后被杀，后续客户端拿到连接失败页 | 长驻服务用任务管理方式启动，而不是 shell 后台符 |

## 无头浏览器（Chrome headless）

| 坑 | 现象 | 正确做法 |
|---|---|---|
| 沙箱受限 | `sandbox initialization failed` → GPU 进程退出 → `--dump-dom` 输出 **0 字节** | 加 `--no-sandbox`（配套 `--disable-gpu --disable-dev-shm-usage`） |
| 移动端视口造假 | 强制 `document.body.style.width` 后测溢出，**`@media` 不生效**，全是假阳性 | 用真实视口 `--headless=new --window-size=W,H`；元素宽度不触发媒体查询 |
| 异步测量时机 | 页面初始化是异步的，加载完就 dump 拿不到结果 | 探针插在初始化调用**之前**（否则被吞掉的告警抓不到），测量挂 `setTimeout`，结果写进 DOM 再取回 |
| 进程逃逸 | 停掉任务外壳 ≠ 杀掉浏览器子进程，残留进程空转 | 调试实例统一带独立 `--user-data-dir`，收尾按特征串 `pkill` 并用 `pgrep` 复核清零 |

## 通用判断
这类坑的共同排查思路：**先怀疑"结果为空/结果异常"是采集方式错了，而不是被测对象真没问题**。换一种采集手段交叉验证，比在原手段上反复调参快。

## 相关
- [[自动化测试分层架构与Fixture作用域]] —— 浏览器自动化在分层里的位置
- [[受限目录下的Git外置版本库方案]] —— 受限环境下的 Git 处置
- [[产物校验的Fail-Open陷阱]] —— 无头验证要拦截的静默劣化

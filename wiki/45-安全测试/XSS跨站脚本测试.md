---
title: XSS跨站脚本测试
type: concept
domain: 安全测试
created: 2026-09-10
updated: 2026-09-10
sources: [raw/legacy/笔记/02-测试技能/XSS跨站脚本测试.md]
tags: [security-testing, interview, pitfall]
confidence: high
status: active
publish: true
interview:
  cat: security-testing
  kind: knowledge
  level: 中级
---

# XSS 跨站脚本测试

## 一句话
恶意脚本被注入页面并被**别人的浏览器**执行。测试的关键不是"脚本能不能弹窗"，而是**payload 有没有按你预期的上下文逃逸出去**。

## 三种类型

| 类型 | 触发条件 | 特征 |
|---|---|---|
| **反射型** | 输入直接回显在当前响应里 | 需要诱导点击，一次性 |
| **存储型** | 输入被持久化，他人访问时触发 | 危害最大，无需诱导 |
| **DOM 型** | 前端 JS 从 DOM/URL 读数据后动态写入页面 | **请求响应里看不到 payload**，必须看 DOM |

**DOM 型是最容易漏的**：抓包看响应体完全正常，payload 是在浏览器端被 JS 拼进去的。验证必须用浏览器实际执行，不能只看 HTTP 响应。

## 按输出上下文调整 payload

同一段恶意代码，放在不同位置需要不同写法：

| 输出位置 | payload 形态 |
|---|---|
| HTML 标签之间 | `<script>alert(1)</script>` |
| HTML 标签属性内 | `"><svg/onload=alert(1)>` |
| JS 字符串内 | `';alert(1);//` |
| 属性值内（无引号闭合） | `" onfocus=alert(1) autofocus="` |
| `href` / `src` 中 | `javascript:alert(1)` |

**探测第一步**：输入 `<test>"'<test>`，看响应里哪些字符被原样输出、哪些被编码——这决定了后面用哪套 payload。

## 绕过过滤
HTML 实体编码、Unicode 编码、大小写混合（`<ScRiPt>`）、双重编码。有 WAF 时先用探测串确认拦截规则，再针对性绕。

## 修复方向
**输出编码必须与上下文相关**（HTML 编码 ≠ JS 编码 ≠ URL 编码，用错等于没编）；配 `Content-Security-Policy`；Cookie 设 `HttpOnly` 让脚本偷不到。

## 相关
- [[Web安全测试地图]]
- [[CSRF跨站请求伪造测试]]
- [[CRLF注入测试]]
- [[面试助手题库索引]]

---
title: CRLF注入测试
type: concept
domain: 安全测试
created: 2026-09-10
updated: 2026-09-10
sources: [raw/legacy/笔记/02-测试技能/CRLF注入测试.md]
tags: [security-testing, interview, pitfall]
confidence: high
status: active
publish: true
interview:
  cat: security-testing
  kind: knowledge
  level: 高级
---

# CRLF 注入测试

## 一句话
用户输入被拼进 HTTP 响应头且未过滤时，注入 `\r\n` 就能**伪造出额外的头，甚至凭空造出第二个响应体**——进而变成响应拆分、缓存投毒、XSS 或请求走私。

这是最容易被忽略的一类注入，因为它不发生在页面上，而发生在**协议层的头部**。

## 触发条件

任何"用户输入被写进 HTTP 响应头"的场景：

- `Location`（重定向目标）
- `Set-Cookie`
- 自定义 Header
- 任何把参数值回显到头里的逻辑

## 注入形式（第一道门槛就是编码）

| 形式 | 写法 |
|---|---|
| URL 编码 | `%0d%0a` |
| Unicode | `\u000d\u000a` |
| 双重 URL 编码 | `%250d%250a` |

**只试一种编码是不够的**——服务端可能只过滤了一次解码，双重编码能绕过。

## 三种利用形态

**1. Open Redirect**

```
/redirect?lang=en%0d%0aLocation:%20https://evil.com
```
若响应里出现两个 `Location` 头、或最终跳到了 evil.com，即存在漏洞。

**2. 借 CRLF 实现 XSS**

```
/redirect?lang=en%0d%0aContent-Type:%20text/html%0d%0a%0d%0a<script>alert(1)</script>
```
注入一个空行（`%0d%0a%0d%0a`）就**结束了头部、开启响应体**，后面的内容被浏览器当 HTML 执行。这条链路值得记住：**CRLF 可以用来绕过 XSS 的所有输出编码防护**，因为它根本不经过页面输出逻辑。

**3. 请求走私**

当 `Header` 名称或值由用户控制时，在 token 里注入 `test\r\nUser-Agent: injected\r\n\r\nGET /smuggled HTTP/1.1\r\nHost: example.com`，服务端可能把**一个请求解析成两个**，第二个是攻击者构造的。后续可导致 SSRF、缓存污染或绕过安全控制。

## 修复方向
对用户输入做严格白名单校验；**禁止把用户输入直接写进 HTTP 头**；用框架内置的安全重定向方法；对 `\r\n` 过滤或编码。

## 与其他漏洞的关系
CRLF 和 [[SSRF服务端请求伪造测试]] 常在同一处出现（服务端取 URL 后回显），而它又是 [[XSS跨站脚本测试]] 的一条绕过路径。**测 SSRF 入口时顺手试 CRLF，成本极低。**

## 相关
- [[Web安全测试地图]]
- [[SSRF服务端请求伪造测试]]
- [[XSS跨站脚本测试]]
- [[面试助手题库索引]]

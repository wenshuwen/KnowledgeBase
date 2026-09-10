---
type: note
tags: [安全测试] [HTTP]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# CRLF 注入测试

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 安全测试章-CRLF注入 小节

攻击者在输入中注入 `\r\n`（回车换行符），操纵 HTTP 响应头结构，可导致 HTTP 响应拆分、缓存投毒、XSS 或 Open Redirect。在 HTTP 头或请求的 URL 中注入`\r\n`，来插入额外的 HTTP 头或分割 HTTP 请求，从而进行请求走私等攻击。

> **测试详解与示例：**
> 
> 

**场景 1： 语言切换接口 ****`/redirect?lang=en`****，服务端将 ****`lang`**** 值写入 Set\-Cookie 或 Location 头。**

1. 在参数中注入 CRLF 编码序列：

    - URL 编码：`%0d%0a`

    - Unicode：`\u000d\u000a`

    - 双重 URL 编码：`%250d%250a`

2. Open Redirect 测试：

```Plain Text
/redirect?lang=en%0d%0aLocation:%20https://evil.com
```

若响应中出现两个 Location 头或重定向到 evil\.com，则存在漏洞。

3. XSS via CRLF 测试：

```Plain Text
/redirect?lang=en%0d%0aContent-Type:%20text/html%0d%0a%0d%0a<script>alert(1)</script>
```

若响应体被执行为 HTML，则可通过 CRLF 实现 XSS。

4. 缓存投毒测试： 注入 `Cache-Control: no-store` 或篡改 `X-Cache` 头，影响 CDN/代理缓存行为。

- 关键检测点： 任何用户输入被放入 HTTP 响应头的场景（Redirect、Set\-Cookie、自定义 Header）。

- 修复建议： 对用户输入进行严格白名单校验；禁止将用户输入直接写入 HTTP 头；使用框架内置的安全重定向方法；对 `\r\n` 进行过滤或编码。

---

**场景 2: 在一个 HTTP 请求中，****`Header`****的名称或值由用户控制。**

```HTTP
GET /status HTTP/1.1
Host: example.com
Authorization: Bearer [用户输入的token]
```

1. 输入测试：攻击者在 token 参数中输入`test\r\nUser-Agent: injected header!\r\n\r\nGET /smuggled HTTP/1.1\r\nHost: ``example.com`。

2. 观察结果：

    - 存在漏洞：原本的一个请求会被服务器解析为两个请求，第二个请求是攻击者精心构造的`/smuggled`请求。

    - 利用方式：这可能导致服务端请求伪造（SSRF）、缓存污染或绕过安全控制。

---

## 相关笔记
- [[02-测试技能]]
- [[SQL注入测试]]
- [[SSRF服务端请求伪造测试]]

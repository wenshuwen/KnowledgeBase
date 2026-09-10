---
title: CSRF跨站请求伪造测试
type: concept
domain: 安全测试
created: 2026-09-10
updated: 2026-09-10
sources: [raw/legacy/笔记/02-测试技能/CSRF跨站请求伪造测试.md]
tags: [security-testing, interview, pitfall]
confidence: high
status: active
publish: true
interview:
  cat: security-testing
  kind: knowledge
  level: 中级
---

# CSRF 跨站请求伪造测试

## 一句话
攻击者**不需要知道你的密码**，只要让你用已登录的浏览器去访问一个恶意页面，浏览器会自动带上 Cookie，请求就以你的身份发出去了。

和 [[XSS跨站脚本测试]] 的关系：XSS 是"偷到你的身份"，CSRF 是"借用你的身份"。**修复 XSS 能顺带堵住一部分 CSRF，但 CSRF 有自己的防线。**

## 测试步骤

1. 登录目标站，抓取敏感操作（改邮箱、改密码、转账）的正常请求
2. **检查请求里有没有有效的 Anti-CSRF Token**
3. 构造恶意页面并自动提交：

```html
<form action="https://target.com/api/user/email" method="POST">
    <input type="hidden" name="new_email" value="hacker@evil.com"/>
</form>
<script>document.forms[0].submit();</script>
```

4. 用已登录的浏览器打开该页面
5. 若操作成功执行且无 Token 校验失败提示 → 存在 CSRF

## 关键检测点

- 敏感操作**是否验证 CSRF Token**（有些接口只在前端传、后端不校验）
- Token 是否与 Session 绑定、**是否一次性**（复用的 Token 价值大减）
- `Referer` / `Origin` 头校验是否可被绕过
- **GET 请求是否执行了状态变更**——这是最严重的一种。`<img src="https://bank.com/change_password?new_pass=attacker123">` 一行就能改密码

## 修复方向
Synchronizer Token Pattern（服务端生成、与会话绑定、一次性）；校验 `Referer`/`Origin`；敏感操作二次确认；Cookie 设 `SameSite=Strict/Lax`。

**SameSite 是现代浏览器性价比最高的一道默认防线**，但它不是万能的——老旧浏览器不生效，跨站顶级导航场景仍会放行。

## 测试视角的落点
CSRF 的用例设计要点是**区分请求方法**：把所有"会改变状态"的接口列出来，检查其中有没有用 GET 的。这是纯规则检查，不需要复杂构造——但漏掉就是漏掉。

## 相关
- [[Web安全测试地图]]
- [[XSS跨站脚本测试]]
- [[越权访问与IDOR]]
- [[面试助手题库索引]]

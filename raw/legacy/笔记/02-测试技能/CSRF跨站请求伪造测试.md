---
type: note
tags: [安全测试] [Web安全]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# CSRF 跨站请求伪造测试

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 安全测试章-CSRF 小节

利用用户已登录的身份凭证，诱导用户在不知情的情况下向目标站点发送恶意伪造的请求，执行非预期操作（如转账、改密码）。

**场景 1： 修改邮箱接口 ****`POST /api/user/email`****，参数 ****`new_email=`****`hacker@evil.com`**

- **测试步骤：**

    - 登录目标网站，抓取修改邮箱的正常请求。

    - 检查请求中是否存在有效的 Anti\-CSRF Token。

    - 构造恶意 HTML 页面：

    ```HTML
    <form action="https://target.com/api/user/email" method="POST">
        <input type="hidden" name="new_email" value="hacker@evil.com"/>
    </form>
    <script>document.forms[0].submit();</script>
    ```

    - 用已登录目标网站的浏览器打开该恶意页面。

    - 若邮箱被成功修改且无 Token 验证失败提示，则存在 CSRF。

- **关键检测点：**

    - 敏感操作是否验证 CSRF Token

    - Token 是否与 Session 绑定、是否一次性

    - Referer/Origin 头校验是否可被绕过

    - GET 请求是否执行了状态变更操作

- **修复建议：** 实施 Synchronizer Token Pattern；验证 Referer/Origin；敏感操作二次确认；SameSite Cookie 属性设为 Strict/Lax。

    ---

**场景 2：修改密码请求****`GET /change_password?new_pass=123456`**

- 正常操作：用户登录银行网站后，修改密码的请求是`GET /change_password?new_pass=123456`。

- 构建攻击页面：攻击者创建一个恶意网页，内含一个自动提交的表单或一个图片链接，其`src`指向密码修改接口：`<img src="``https://bank.com/change_password?new_pass=attacker123``">`。

- 诱导点击：诱骗已登录银行网站的用户访问这个恶意页面。

- 观察结果：

    - 存在漏洞：用户的密码会被修改为`attacker123`，因为浏览器会自动携带该网站的 Cookie 发送请求。

    - 修复建议：使用 Token 验证机制。在关键操作中，除 Cookie 外还需提交一个随机 Token，攻击者无法获取此 Token，从而无法伪造请求。

---

## 相关笔记
- [[02-测试技能]]
- [[XSS跨站脚本测试]]
- [[越权访问与IDOR]]

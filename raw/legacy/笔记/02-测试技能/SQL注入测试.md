---
type: note
tags: [安全测试] [数据库]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# SQL 注入测试

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 安全测试章-SQL注入 小节

用户输入被拼接到 SQL 语句中且未做参数化处理，攻击者通过特殊字符改变 SQL 语义，实现数据泄露、篡改甚至系统命令执行。核心逻辑：攻击者将恶意的 SQL 代码插入到 Web 表单的输入域或页面请求的查询字符串中，欺骗数据库服务器执行该恶意命令。

> **测试详解与示例：**
> 
> 

以一个登录功能为例，其后台 SQL 语句可能为：

```SQL
SELECT * FROM users WHERE username = '[用户名]' AND password = '[密码]'
```

1. 输入测试：在用户名框中输入 `admin' --`（注意`--`后有一个空格），密码随意。

2. 查看后台 SQL：此时，SQL 语句变为：

```SQL
SELECT * FROM users WHERE username = 'admin' -- ' AND password = '任意密码'
```

3. 观察结果：

    - 存在漏洞：由于`--`是 SQL 中的注释符，`AND password = '任意密码'`这段条件被注释掉了。如果数据库中存在`admin`用户，此语句就会返回该用户数据，攻击者无需密码即可登录系统。

    - 修复建议：使用参数化查询（PreparedStatement），将 SQL 结构与数据分离，从根本上防止注入。

---

> ***登录接口：SELECT \* FROM users WHERE username='$input' and password = '$pass'***
> 
> 

- **测试步骤：**

    - 错误探测： 输入 `'` 或 `"`，观察是否返回数据库错误信息。

    - 布尔盲注： 输入 `' AND '1'='1` （正常）vs `' AND '1'='2` （异常），对比响应差异。

    - 时间盲注： 输入 `' AND SLEEP(5)--`，观察响应是否延迟 5 秒。

    - 联合查询： 输入 `' UNION SELECT NULL,NULL,NULL--`，逐步确定列数并提取数据。

    - 经典 Payload 示例：

    ```SQL
    -- 绕过登录
    ' OR '1'='1' --
    -- 提取版本信息
    ' UNION SELECT @@version,NULL--
    -- 读取文件(MySQL)
    ' UNION SELECT LOAD_FILE('/etc/passwd'),NULL--
    ```

- **关键检测点：** 所有用户输入点（包括 HTTP Header 如 User\-Agent、Cookie）、排序字段、LIMIT 子句、JSON/XML 解析入口。

- **修复建议：** 始终使用参数化查询/预编译语句；最小权限原则；WAF 作为辅助防线。

---

## 相关笔记
- [[02-测试技能]]
- [[越权访问与IDOR]]
- [[CRLF注入测试]]

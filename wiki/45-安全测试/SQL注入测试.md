---
title: SQL注入测试
type: concept
domain: 安全测试
created: 2026-09-10
updated: 2026-09-10
sources: [raw/legacy/笔记/02-测试技能/SQL注入测试.md]
tags: [security-testing, interview, pitfall]
confidence: high
status: active
publish: true
interview:
  cat: security-testing
  kind: knowledge
  level: 中级
---

# SQL 注入测试

## 一句话
用户输入被拼进 SQL 语句且未参数化时，特殊字符能改变 SQL 语义。测试的核心动作是**判断输入有没有被当成代码执行**——而不是背 payload。

## 测试手法，由浅入深

| 手法 | 输入 | 判据 |
|---|---|---|
| **错误探测** | `'` 或 `"` | 是否返回数据库错误信息（有报错 = 有回显 = 好定位） |
| **布尔盲注** | `' AND '1'='1` vs `' AND '1'='2` | 两次响应是否不同（无报错时靠差异判断） |
| **时间盲注** | `' AND SLEEP(5)--` | 响应是否延迟 5 秒（完全无回显时的兜底） |
| **联合查询** | `' UNION SELECT NULL,NULL,NULL--` | 逐步确定列数后提取数据 |
| **注释截断** | `admin' -- `（`--` 后必须有空格） | 密码条件被注释掉，无需密码登录 |

**注释截断是最经典的验证**：原语句 `WHERE username='$u' AND password='$p'`，输入 `admin' -- ` 后变成 `WHERE username='admin' -- ' AND password='...'`，密码条件整段失效。

## 输入点不止表单

容易被漏掉的注入位置：

- **HTTP Header**：`User-Agent`、`Referer`、`X-Forwarded-For`
- **排序与分页**：`ORDER BY` 后面的字段名无法参数化，常被忽略
- **LIMIT 子句**
- **JSON / XML 解析入口**

**只测表单输入框是新手最常见的漏测。**

## 修复方向
参数化查询（预编译语句）是唯一根本解法——把 SQL 结构与数据分离。最小权限原则和 WAF 都只是辅助防线：WAF 可以被编码绕过，权限收窄只能限制危害范围。

## 相关
- [[Web安全测试地图]]
- [[XSS跨站脚本测试]]
- [[越权访问与IDOR]]
- [[面试助手题库索引]]

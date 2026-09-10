---
title: 接口鉴权机制-Token与Cookie与Session
type: concept
domain: 接口测试
created: 2026-09-10
updated: 2026-09-10
sources: [raw/legacy/笔记/01-测试理论/Token与Cookie与Session.md]
tags: [api-testing, interview, checklist]
confidence: high
status: active
publish: true
interview:
  cat: api-testing
  kind: knowledge
  level: 高级
---

# 接口鉴权机制：Token / Cookie / Session

## 一句话
HTTP 是无状态的，服务端要靠这三样东西"记住"你是谁。**它们的区别不在实现细节，而在状态存在谁那边**——这个根本差异决定了扩展性、注销难度和安全风险。

## 三种机制

| 机制 | 状态存在哪 | 本质 |
|---|---|---|
| **Cookie** | 客户端（浏览器） | 服务端发下来、浏览器每次自动带上的一小段文本，容量约 4KB、明文可篡改 |
| **Session** | 服务端（内存/Redis/DB） | 真正的状态在服务端，客户端只拿一个 SessionID 当"暗号" |
| **Token（JWT）** | 客户端，但服务端不存 | 自包含的签名凭证，服务端只验签名即可，**无需查库** |

## 核心对比

| 维度 | Cookie | Session | Token (JWT) |
|---|---|---|---|
| 状态类型 | 客户端状态 | 服务端状态 | **无状态** |
| 安全性 | 低（明文易篡改/劫持） | 中（敏感数据在服务端） | 高（签名防篡改） |
| XSS 防护 | 需 `HttpOnly` | 天然防护 | 需谨慎存储 |
| CSRF 防护 | 需 `SameSite` + 双重 Cookie | 需 CSRF Token | **不使用 Cookie，天然免疫** |
| 扩展性 | 差 | 差（集群需共享存储） | **好（无状态，天然分布式）** |
| 注销 | 删 Cookie | 删 Session | **难——需黑名单或短过期** |
| 传输方式 | 浏览器自动携带 | 自动携带 SessionID | 前端**手动**放进 `Authorization` 头 |
| 跨域 / 移动端 | 受同源策略限制 / ❌ | 同左 | 极佳 / ✅ |

## 三个必须纠正的认知

**一、"Session 在服务端所以安全"是错的。** Session 只是存储方式，它依然要靠 SessionID 标识用户，而这个 ID **通常还是通过 Cookie 传递的**——所以 Session 架构同样面临 CSRF 风险，标准解法是额外的 CSRF Token。

**二、Token 的 payload 是 Base64 编码，不是加密。** 任何人都能解开看内容。**所以绝不能把密码等敏感信息放进 Token。** 签名只保证"没被改过"，不保证"看不见"。

**三、Token 一旦签发难以主动作废。** 这是它最大的工程代价——用户登出、密码修改、账号封禁都需要额外机制（黑名单、短过期 + 刷新令牌轮换）才能及时生效。面试里能主动说出这个 trade-off 是加分项。

## 测试视角的落点

**先确认被测系统用哪种鉴权，再设计用例**——鉴权方式决定了必测项完全不同：

- **Cookie 体系** → 必测 CSRF（见 [[CSRF跨站请求伪造测试]]）、`HttpOnly` 与 `SameSite` 是否设置、Cookie 劫持
- **Session 体系** → 必测会话超时、集群间 Session 是否共享、登出后 SessionID 是否真正失效
- **Token 体系** → 必测**签名篡改**（改 payload 后签名是否失效）、算法混淆（`alg: none`）、过期策略、刷新令牌竞态
- **通用** → 无凭证访问、改他人凭证、凭证在最外层被剥离后接口是否仍然放行

## 相关
- [[接口测试知识地图]]
- [[HTTP协议要点与状态码]]
- [[HTTP与HTTPS的核心差异]]
- [[CSRF跨站请求伪造测试]]
- [[Web安全测试地图]]
- [[自动化测试分层架构与Fixture作用域]]
- [[面试助手题库索引]]

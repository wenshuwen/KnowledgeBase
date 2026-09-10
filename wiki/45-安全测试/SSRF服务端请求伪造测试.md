---
title: SSRF服务端请求伪造测试
type: concept
domain: 安全测试
created: 2026-09-10
updated: 2026-09-10
sources: [raw/legacy/笔记/02-测试技能/SSRF服务端请求伪造测试.md]
tags: [security-testing, interview, root-cause]
confidence: high
status: active
publish: true
interview:
  cat: security-testing
  kind: knowledge
  level: 高级
---

# SSRF 服务端请求伪造测试

## 一句话
服务端提供"从指定 URL 取资源"的功能却不校验目标地址，攻击者就能**让服务器替他发请求**——而服务器在内网里，能碰到攻击者碰不到的东西。

SSRF 的危害等级比多数 Web 漏洞高，因为它把攻击面从"公网可达"扩展到了"整个内网 + 云元数据"。

## 高危功能点（测试入口清单）

- URL 预览 / 链接分享解析
- 图片抓取 / 头像上传 / **PDF 生成**（很隐蔽，本质是服务端去取图片）
- Webhook 回调地址配置
- XML/JSON 外部实体引用（XXE）
- 导入远程资源（RSS、CSV、模板）
- SSO / OAuth 回调验证
- 云服务元数据接口调用

**找 SSRF 入口的通用方法**：搜代码/接口里所有"用户填了个地址，服务端去访问"的地方。

## 逐级探测 payload

| 级 | Payload | 目的 |
|---|---|---|
| 1 | `http://127.0.0.1:80/` | 探测本地回环 |
| 2 | `http://169.254.169.254/latest/meta-data/` | **云元数据服务**（AWS/阿里云） |
| 3 | `http://192.168.1.1:8080/admin` | 探测内网 Web 后台 |
| 4 | `file:///etc/passwd` | 伪协议读本地文件 |
| 5 | `http://internal-redis:6379/` | 探测内部服务端口 |

## 危害等级差异很大

| 利用方向 | 危害 |
|---|---|
| 内网端口扫描 | 中（只是信息收集） |
| 读取本地文件 | 高（敏感文件泄露） |
| **攻击内网服务**（Gopher 协议打 Redis） | **极高，可实现 RCE** |
| **窃取云元数据**（`/iam/security-credentials/`） | **极高，可接管云账号** |

面试里如果只答"能探测内网"，深度是不够的——**能打通云元数据直接接管账号**才是 SSRF 被列为高危的原因。

## 修复方向
白名单（推荐，只允许预批准的域名/IP）优于黑名单（易绕过）；**限制伪协议**只留 `http`/`https`；服务端禁止重定向（防跳转绕过）+ 设超时；**统一访问入口**——不让用户传完整 URL，改成传资源 ID 由服务端映射到固定路径，这是最彻底的解法。

## 相关
- [[Web安全测试地图]]
- [[CRLF注入测试]]
- [[越权访问与IDOR]]
- [[面试助手题库索引]]

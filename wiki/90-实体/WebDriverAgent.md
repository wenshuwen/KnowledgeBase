---
title: WebDriverAgent
type: entity
domain: 实体
created: 2026-10-05
updated: 2026-10-05
sources: [raw/notes/2026-10-05 移动端App自动化闭环方案会话要点.md]
tags: [automation-testing, interview, tooling]
confidence: medium
status: active

publish: true
interview:
  cat: automation-testing
  kind: knowledge
  level: 高级
---

# WebDriverAgent

| 项 | 内容 |
|---|---|
| 定位 | iOS 侧自动化的**唯一入口**：它把 Apple 的 XCTest/XCUIApplication 能力包成 HTTP 服务，供 Appium 等客户端驱动 |
| 类型 | 框架 / 设备端代理程序（一个 XCUITest target） |
| 官方地址 | `https://github.com/appium/WebDriverAgent`（Appium 维护的上游分支；另有各厂商分叉） |
| 当前使用版本 | 未建立（本页为方案推演阶段的知识整理，尚未实施） |

## 我为什么关注它

因为 iOS 自动化的**绝大多数失败都不是脚本写错**，而是落在 WDA 这一层：
签名过期、证书未信任、会话崩溃后拉不起来。理解这一层，才知道哪些失败是"再试一次能好"、
哪些是"必须有人做点什么"。

## 关键能力

- **把 XCUITest 变成 HTTP 服务**：客户端（Appium 等）通过 HTTP 发指令，WDA 在设备上调用 Apple 的 UI 自动化 API。Appium 在 iOS 上不是另一套引擎，而是 XCUITest 外面套了一层。
- **可脱离 Mac、但不可脱离主机**：在 Mac 上构建安装一次之后，设备可以交给 Windows / Linux 上的 Agent 使用。脱离的是 **Mac**，不是主机。
- **支持预装与外部托管**：Appium 的 XCUITest 驱动提供 `usePreinstalledWDA`（设备已预装）与 `webDriverAgentUrl`（外部已运行）两种模式。非 macOS 主机**必须**走这两种之一，因为非 macOS 上无法用 xcodebuild 构建 WDA。

## 踩过的坑

> ⚠️ 待验证：以下三条来自公开文档与社区资料的一致描述，**本机未实际验证**。

- **签名有效期**：免费 Apple ID 签出的 WDA 构建 **7 天过期**，届时需重新签名并重新信任；且最多签 3 台设备。付费开发者账号（99 美元/年）解除这两个限制。
- **首次必须人工信任**：设备上要在「设置 → 通用 → VPN 与设备管理」里信任开发者证书，否则会话起不来。
- **无人值守的死穴**：WDA 会话会崩溃或过期，重启机制只在**设备无锁屏密码**时能生效；有密码时会停在锁屏页面等人解锁。所以无人值守机型通常要去掉密码（代价是失去 Face ID / Apple Pay 等）。

## 上手最小示例

```bash
# 用 Mac 把 WDA 构建到设备（Sonic 部署文档给出的形式）
xcodebuild -project <WebDriverAgent.xcodeproj 路径> \
  -scheme WebDriverAgentRunner \
  -destination 'id=<设备 UDID>' test
```

```yaml
# 设备已预装 WDA 时，Appium 侧的连接方式（非 macOS 主机的唯一路径）
platformName: ios
appium:automationName: xcuitest
appium:platformVersion: "<版本>"
appium:udid: "<设备 UDID>"
appium:usePreinstalledWDA: true
```

> 以上为可跑通形态的**结构示意**，版本号、Bundle ID 后缀等取值需按实际环境确认，属**待人工复核**内容。

## 相关

- [[移动端App自动化的三条技术路线]]
- [[移动端自动化闭环的七阶段]]

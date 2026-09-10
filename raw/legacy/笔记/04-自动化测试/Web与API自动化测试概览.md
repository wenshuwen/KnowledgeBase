---
type: note
tags: [自动化测试] [Playwright] [Pytest]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Web 与 API 自动化测试框架

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 自动化测试章：Web 自动化 + API 自动化 框架概览（原文较短，合并为一篇）

**Pytest \+ Playwright \+ Excel \(数据驱动\) \+ Allure \(报告\) \+ Po 模式 \(Page Object\) \+ 关键字驱动 \(核心\)**

- 分层架构设计 \(PO 模式 \+ 关键字封装\)：

    - Base 层: 封装底层驱动方法（如点击、输入、发送请求）。

    - Page/API 层: 对应具体的页面元素或接口定义。

    - Case 层: 纯业务逻辑测试用例，不包含具体实现细节。

    - Data 层: 测试数据与代码分离（YAML/JSON）。

- Po 模式核心作用是：依赖注入（Dependency Injection），即将 Playwright 的 Page 对象（浏览器页面实例）传递给当前页面对象，以便后续操作。

- Browser \(session\): 启动 Chromium/Firefox 进程非常耗时（几秒）。整个测试跑几百个用例，只需要启动 1 次浏览器进程。

- Page \(function\): 创建一个新的无痕上下文（Context）和页面（Page）非常快（毫秒级）。每个用例拥有一个全新、干净、无 Cookie、无缓存的页面，确保用例之间绝对隔离（A 用例登录了，不会影响到 B 用例）。

## **2\. Api 自动化**

**Pytest \+ Requests \+ YAML/Excel \(数据驱动\) \+ Allure**

---

---

## 相关笔记
- [[04-自动化测试]]
- 自动化相关分类入口见 [[04-自动化测试]]

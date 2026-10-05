---
title: 自动化测试分层架构与Fixture作用域
type: concept
domain: 自动化测试
created: 2026-09-10
updated: 2026-10-05
sources: [raw/legacy/笔记/04-自动化测试/Web与API自动化测试概览.md, raw/notes/2026-10-05 移动端App自动化闭环方案会话要点.md]
tags: [automation-testing, interview, framework, best-practice]
confidence: high
status: active
publish: true
interview:
  cat: automation-testing
  kind: skill
  level: 高级
---

# 自动化测试分层架构与 Fixture 作用域

## 一句话
框架设计的两个核心决策：**代码怎么分层**（改动影响面）和 **fixture 作用域怎么定**（性能与隔离的平衡）。这两件事定了，框架就定了。

## 技术栈组合

- **Web 自动化**：Pytest + Playwright + Excel（数据驱动）+ Allure（报告）+ PO 模式 + 关键字驱动
- **API 自动化**：Pytest + Requests + YAML/Excel（数据驱动）+ Allure

## 四层架构

| 层 | 职责 | 关键约束 |
|---|---|---|
| **Base 层** | 封装底层驱动方法（点击、输入、发请求） | 只做原子操作，不含业务 |
| **Page / API 层** | 对应具体页面元素或接口定义 | 元素定位、接口路径只在这里出现 |
| **Case 层** | 纯业务逻辑的测试用例 | **不含任何实现细节**——这是分层是否成功的判据 |
| **Data 层** | 测试数据与代码分离（YAML/JSON/Excel） | 同一用例换数据即可复用 |

**PO 模式的本质是依赖注入**：把 Playwright 的 Page 对象注入到页面对象里，让页面对象持有操作入口。这样 Case 层只调业务方法，不碰定位器——UI 改版时只改 Page 层。

## Fixture 作用域：性能与隔离的平衡点

这是最容易被写错、也最能体现设计水平的一处：

| Fixture | 作用域 | 为什么 |
|---|---|---|
| **Browser** | `session` | 启动 Chromium/Firefox 进程要**几秒**。几百个用例只启动 1 次 |
| **Page** | `function` | 新建无痕上下文 + 页面只要**毫秒级**。每个用例一个全新、无 Cookie、无缓存的页面 |

**收益**：性能上省掉几百次进程启动，隔离上保证 A 用例的登录状态绝不会污染 B 用例。

**反过来做会怎样**：把 Browser 设成 function，测试套件慢到不可接受；把 Page 设成 session，用例之间互相污染，偶发失败（flaky）开始出现且极难定位。

## 测试视角的落点

- **判断分层是否合格**：随便改一个页面的元素定位，如果只改了一个文件就够，分层是对的
- **判断 fixture 是否合理**：跑一次全量，如果耗时集中在 setup 阶段，多半是重资源 fixture 的作用域写小了
- **数据驱动的边界**：适合参数组合多的接口用例；不适合流程强依赖、步骤间有状态传递的场景

## 与其他领域的关系
- API 自动化里最麻烦的一块是**鉴权态的处理**（登录一次拿到 Token，在多个用例间复用还是每次重登），见 [[接口鉴权机制-Token与Cookie与Session]]
- 依赖没就绪时需要桩服务，见 [[Mock接口桩的设计模式]]
- **移动端的四层是另一套**：驱动层 → 定位/页面对象层 → 流程编排层 → 断言与证据层。它多出一个 Web/API 端没有的维度——**事件注入走哪条通道**（无障碍 / 调试注入），这个通道选择直接决定方案可行性，见 [[移动端App自动化的三条技术路线]]；移动端的"用例层"对应的是**闭环阶段**，划分方式见 [[移动端自动化闭环的七阶段]]

## 相关
- [[接口鉴权机制-Token与Cookie与Session]]
- [[Mock接口桩的设计模式]]
- [[面试助手题库索引]]

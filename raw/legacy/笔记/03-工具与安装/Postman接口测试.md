---
type: note
tags: [接口测试] [工具] [Postman]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Postman 接口测试工具

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 测试工具章-Postman 小节

## **3\.1 核心概念**

Postman 是一款功能强大的 API 开发和测试工具，支持 HTTP/HTTPS、WebSocket、gRPC 等主流通信协议。其核心功能覆盖接口设计、测试、监控、文档生成等全生命周期管理。

**核心构成要素**

|组件|说明|
|---|---|
|Workspace（工作空间）|组织项目和团队成员的最高层级|
|Collection（集合）|将相关接口请求分组管理，便于复用和批量测试|
|Folder（文件夹）|集合内按模块进一步细分组织|
|Environment（环境）|存储一组变量，用于不同环境（开发/测试/生产）切换|

## **3\.2 接口测试流程**

**步骤 1：安装与启动**

访问 Postman 官网（[https://www\.postman\.com/downloads/](https://www.postman.com/downloads/)）下载对应操作系统的安装包。安装后登录（或选择“Skip Sign In”跳过），创建或进入工作区。

**步骤 2：创建集合（Collection）**

集合用于组织和管理所有相关的 API 请求。

- 点击左侧边栏的「Collections」→「\+ New Collection」

- 输入集合名称（如“用户管理 API”）

- 可添加描述信息，点击「Save」保存

**步骤 3：创建请求（Request）**

- 点击左上角的「New」按钮，选择「Request」

- 输入请求名称（如“获取用户信息”）

- 选择或创建集合，点击「Save」保存

**步骤 4：配置请求参数**

这是接口测试的核心环节，包括以下配置项：

① 请求方法（Method）与 URL

- 从下拉菜单中选择 HTTP 方法：GET / POST / PUT / DELETE / PATCH 等

- 在地址栏输入完整的接口 URL

② Params（查询参数）

- 用于 GET 请求中传递查询参数，以 `?key1=value1&key2=value2` 格式拼接在 URL 末尾

- 可在 Params 标签页以键值对形式添加，Postman 会自动拼接到 URL

③ Authorization（鉴权）

- 配置身份验证方式，如 Bearer Token、Basic Auth、OAuth 2\.0 等

- 集合或文件夹级别配置后，子级可「Inherit auth from parent」继承

④ Headers（请求头）

- 添加请求头信息，如 `Content-Type: application/json`

- 常用 Headers：Content\-Type、Authorization、Accept 等

⑤ Body（请求体）

- 用于 POST、PUT、PATCH 等需要提交数据的请求

- 支持多种格式：form\-data、x\-www\-form\-urlencoded、raw、binary、GraphQL

**步骤 5：编写测试脚本（Tests）**

在 Tests 标签页编写 JavaScript 断言，验证响应结果是否符合预期：

```JavaScript
*// 1. 验证状态码为 200
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// 2. 验证响应体包含某字段
pm.test("Response contains user data", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
});

// 3. 验证响应时间小于 500ms
pm.test("Response time is less than 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
**});*
```

**步骤 6：发送请求与查看响应**

点击「Send」按钮发送请求，下方响应区展示：

- Status：状态码（200/400/500 等）

- Time：响应耗时

- Body：响应内容（JSON、HTML、Text 等）

- Headers：响应头信息

- Test Results：测试脚本执行结果

**步骤 7：批量运行（Collection Runner）**

- 点击集合右上角的「Run」按钮

- 选择环境变量、迭代次数、延迟时间等

- 点击「Run」批量执行所有请求

- 适用于回归测试和 CI/CD 集成。

## **3\.3 参数配置对照表**

> **请求方法（Method）配置**
> 
> 

|方法|用途|参数位置|是否需 Body|
|---|---|---|---|
|GET|获取资源|URL（Params）|否|
|POST|创建资源|Body|是|
|PUT|完整更新资源|Body|是|
|PATCH|部分更新资源|Body|是|
|DELETE|删除资源|URL（Params）|否|

> **参数类型（Params）配置对照表**
> 
> 

|参数类型|配置位置|格式示例|适用场景|
|---|---|---|---|
|Query Params（查询参数）|Params 标签页 或 URL 中|?id=123\&type=new|GET 请求过滤、分页、排序|
|Path Variables（路径参数）|URL 中使用 : 占位|/user/:id → /user/123|RESTful 资源定位|
|Headers（请求头）|Headers 标签页|Content\-Type: application/json|传递元数据、认证信息|

> **Body 请求体格式配置对照表**
> 
> 

|格式|配置路径|Content\-Type|适用场景|
|---|---|---|---|
|none|Body → none|无|GET/DELETE 无 Body 请求|
|form\-data|Body → form\-data|multipart/form\-data（自动）|文件上传、混合表单数据|
|x\-www\-form\-urlencoded|Body → x\-www\-form\-urlencoded|application/x\-www\-form\-urlencoded（自动）|适用于普通表单提交的 POST 请求。|
|raw \- JSON|Body → raw → 选择 JSON|application/json（自动）|RESTful API 最常用格式|
|raw \- Text/XML/HTML|Body → raw → 选择对应类型|根据选择自动设置|非 JSON 文本数据|
|binary|Body → binary|需手动设置|图片等二进制文件上传|
|GraphQL|Body → GraphQL|application/json|GraphQL 查询|

> **授权（Authorization）类型配置**
> 
> 

|授权类型|配置方式|适用场景|
|---|---|---|
|No Auth|无需配置|公开接口|
|Bearer Token|输入 Token 值|JWT 认证|
|Basic Auth|输入用户名/密码|基础认证|
|API Key|选择位置（Header/Query）\+ 输入 Key|API Key 认证|
|OAuth 2\.0|配置授权流程参数|第三方授权登录|

> **变量类型配置对照表**
> 
> 

|变量类型|作用范围|配置位置|引用方式|
|---|---|---|---|
|全局变量（Global）|整个工作空间|右上角齿轮 → Global|\{\{variableName\}\}|
|环境变量（Environment）|当前选中环境|右上角齿轮 → Manage Environments|\{\{variableName\}\}|
|集合变量（Collection）|当前集合内|集合编辑 → Variables 标签页|\{\{variableName\}\}|
|局部变量（Local）|当前脚本内|脚本中定义|使用 pm\.variables 访问|

> **断言（Tests）常用方法对照表**
> 
> 

|断言类型|代码示例|说明|
|---|---|---|
|状态码断言|pm\.response\.to\.have\.status\(200\);|验证 HTTP 状态码|
|响应体包含字段|pm\.expect\(jsonData\)\.to\.have\.property\('msg'\);|验证 JSON 包含某字段|
|字段值相等|pm\.expect\(jsonData\.msg\)\.to\.eql\("成功"\);|验证字段具体值|
|响应体包含字符串|pm\.expect\(pm\.response\.text\(\)\)\.to\.include\("成功"\);|验证响应体包含某文本|
|响应体不包含|pm\.expect\(pm\.response\.text\(\)\)\.to\.not\.include\("错误"\);|验证响应体不包含某文本|
|响应时间断言|pm\.expect\(pm\.response\.responseTime\)\.to\.be\.below\(500\);|验证响应耗时|

> **Pre\-request Script 常用操作**
> 
> 

|操作|代码示例|说明|
|---|---|---|
|设置环境变量|pm\.environment\.set\("key", "value"\);|请求前动态设置变量|
|获取当前时间戳|pm\.environment\.set\("timestamp", new Date\(\)\.getTime\(\)\);|生成动态时间参数|
|打印日志|console\.log\("调试信息"\);|控制台调试|

---

## **3\.4 实践与进阶技巧**

> **使用环境变量管理多环境**
> 
> 

创建开发、测试、生产三套环境变量，通过 `{{base_url}}` 等方式引用，实现一键切换环境：

```Plain Text
*开发环境：base_url = https://dev.api.example.com
测试环境：base_url = https://test.api.example.com
**生产环境：base_url = https://api.example.com*
```

> **参数化批量测试**
> 
> 

在 Collection Runner 中导入 CSV 或 JSON 数据文件，实现数据驱动测试。

> **调试技巧**
> 
> 

- 使用 Console 面板（View → Show Postman Console）查看详细请求/响应日志

- 点击 Code 按钮可生成 cURL、Python、Java 等语言的代码片段

- 使用 Bulk Edit 批量编辑参数

> **测试用例设计规范**
> 
> 

- 命名规范：采用 `模块_功能_状态` 的格式（如 `user_login_success`）

- 覆盖正常值、边界值、异常值等测试场景

- 验证状态码、响应头、响应体等关键要素

---

## **3\.5 性能测试流程**

性能测试面板：选中目标集合，点击概览（Overview）选项卡中的 Run 按钮，在弹出的 Runner 窗口中切换到 Performance 选项卡。

> **核心参数配置对照表**
> 
> 

在 Performance 选项卡中，你需要配置以下关键参数来定义压测模型：

|参数模块|配置项|详细说明与选项|
|---|---|---|
|负载模型|Load profile|决定虚拟用户数量在测试期间的变化趋势：<br>• Fixed（固定）：在整个测试期间保持最大虚拟用户数不变。<br>• Ramp up（递增）：从初始负载逐渐增加到最大虚拟用户数。<br>• Spike（尖峰）：从基础负载瞬间增加到最大值，然后迅速降回基础负载。<br>• Peak（峰值）：从基础负载增加到最大值，保持一段时间稳定后，再降回基础负载。|
|并发与时长|Virtual users|设置虚拟用户数量。每个虚拟用户会按顺序循环执行集合中的请求。数值越高，API 承受的负载越大。<br>\(注：最大可模拟的虚拟用户数受限于你当前电脑的 CPU 和内存等系统资源\)|
||Test duration|设置性能测试的总持续时间（以分钟为单位）。|
|数据驱动|Data file|（可选）上传 CSV 或 JSON 格式的数据文件。可为每个虚拟用户提供自定义变量值，使压测更贴近真实的多用户场景。|
|通过条件|Pass test if|（可选）设置测试通过的阈值。可选择指标（如平均响应时间、p95 响应时间、错误率、每秒请求数等），并设定条件（如小于、大于）和具体数值。|

---

> **执行与结果分析**
> 
> 

- 启动测试：配置完成后，点击 Run 按钮。Postman 会实时展示性能指标图表。

- 监控资源：在测试过程中，如果系统资源达到阈值，Postman 会发出应用内警告并自动停止测试。建议先使用 10 到 20 个虚拟用户进行小规模测试，观察资源占用情况。

- 分析结果：测试结束后，重点查看以下核心指标来评估 API 性能：

    - Average / Median / Min / Max Response Time：平均、中位数、最小和最大响应时间。

    - p90 / p95 / p99：百分位响应时间（如 95% 的请求响应时间低于该值）。

    - Requests per second \(RPS\)：吞吐量，即每秒处理的请求数。

    - Error %：错误率，反映高并发下 API 的稳定性。

---

> **进阶压测技巧**
> 
> 

- 脚本动态负载：利用 `Pre-request Script` 在每次请求前生成动态参数（如递增的订单号、随机时间戳），避免缓存带来的虚假高性能。

- 链式状态传递：对于需要登录态的接口，在 `Tests` 脚本中提取 Token 并写入环境变量，供后续请求复用，从而构建完整的业务链路压测。

- 脱离 UI 限制：Postman UI 在高并发、长时间运行下可能存在资源瓶颈。对于高强度的压力测试，建议将集合导出为 JSON 文件，使用官方命令行工具 Newman 来执行压测，并可轻松集成到 CI/CD 流水线中。

---

## **3\.6 常见问题排查**

|问题|可能原因|解决方案|
|---|---|---|
|401 未授权|Token 过期或无效|重新获取 Token，更新环境变量|
|参数为空|参数未正确传递|检查 Params/Body 配置，查看 F12 抓包对比|
|Content\-Type 不匹配|Header 与 Body 格式不一致|确保 Content\-Type 与 Body 所选格式一致|

---

## 相关笔记
- [[03-工具与安装]]
- [[JMeter使用详解]]
- [[SoapUI使用指南]]

---
type: note
tags: [抓包] [工具] [Fiddler]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Fiddler 抓包与弱网测试

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 测试工具章-Fiddler 小节（含弱网/防重放/安全/性能场景）

Fiddler 是一款免费的 HTTP/HTTPS 调试代理工具，由 Telerik 公司开发。它作为代理服务器运行，能够捕获所有客户端和服务器之间的 HTTP/HTTPS 通信，允许你查看、分析甚至修改通信内容。对于软件测试工程师而言，Fiddler 的核心价值包括：接口测试与分析、前后端问题定位、性能测试辅助、安全测试支持、模拟测试环境等。

## **📥 安装与基础配置**

### **下载安装**

- Windows：访问 [Telerik 官网](https://www.telerik.com/fiddler) 下载 Fiddler Classic（免费版），双击安装程序按提示完成安装。

- macOS / Linux：下载 Fiddler Everywhere（跨平台版），从 App Store 或官网获取。

### **HTTPS 证书配置（关键步骤）**

首次运行 Fiddler 后，必须配置根证书才能解密 HTTPS 流量：

- 打开 Tools → Options → HTTPS

- 勾选以下选项：

    - `Capture HTTPS CONNECTs`（捕获 HTTPS 连接）

    - `Decrypt HTTPS traffic`（解密 HTTPS 流量）

    - `Ignore server certificate errors`（忽略证书错误）

- 点击 Actions → Trust Root Certificate，安装 Fiddler 根证书

- 弹出提示时点击 "Yes" 信任 Fiddler 根证书

- 依次点击"Yes" → "是" → "确定"完成证书安装

- 重启 Fiddler 使配置生效

### **允许远程连接（用于手机抓包）**

- 打开 Tools → Options → Connections

- 勾选 "Allow remote computers to connect"（允许远程设备连接）

- 如需减少干扰，可取消勾选 `Act as system proxy on startup`

- 记住默认端口号 8888

- 重启 Fiddler

### **手机代理配置**

- 确保手机和电脑在同一局域网

- 在手机 WiFi 设置中配置代理：

    - 代理服务器：电脑的局域网 IP（如 `192.168.1.100`）

    - 端口：`8888`

- 手机浏览器访问 `http://192.168.1.100:8888`，下载并安装 Fiddler 根证书

    - Android：设置 → 安全 → 加密与凭据 → 安装证书

    - iOS：设置 → 已下载的描述文件 → 安装

### 验证抓包

- 状态栏显示 Capturing 表示正在抓包

- 点击 Capturing 可快速切换抓包状态

- 快捷键 F12 可快速开启/停止抓包

---

## **🔧 核心功能速览**

### **会话列表与查看请求**

- 左侧会话列表每一行代表一个网络请求，包含 Method、URL、Status Code、Body 等信息

- 选中请求后，右侧 Inspectors 面板查看详情：

    - 上半部分：请求详情（Headers、Body、JSON 等）

    - 下半部分：响应详情（TextView、JSON、Raw 等）

### **过滤请求（Filters）**

右侧 Filters 面板可以过滤特定请求：

- `Show only the following Hosts`：只显示指定域名的请求

- `Hide the following Hosts`：隐藏指定主机

- 可按进程、状态码等条件过滤

### **清空与保存会话**

- 清空所有会话：Ctrl \+ X

- 保存会话：File → Save → All Sessions，保存为 SAZ 格式

|功能|说明|操作路径|
|---|---|---|
|会话列表|查看所有捕获的请求（状态码、协议、URL、响应大小等）|主界面左侧|
|Inspectors|查看/修改请求头和响应体的详细内容|右侧面板|
|Filters|按域名、进程、状态码等过滤请求|右侧 Filters 标签|
|AutoResponder|模拟服务器响应，无需后端服务|右侧 AutoResponder 标签|
|Composer|手动构造和发送 HTTP 请求|右侧 Composer 标签|
|断点|拦截请求/响应进行修改|F11（请求前）/ F12（响应后）|
|FiddlerScript|自定义规则脚本|Rules → Customize Rules（Ctrl\+R）|

---

## **🌐 测试场景一：弱网测试**

弱网测试用于模拟地铁、电梯、偏远地区等网络不佳场景，验证 App 在延迟、低速、丢包等情况下的表现。

### **快速开启（内置模式）**

直接点击菜单 Rules → Performance → Simulate Modem Speeds，即可模拟 56K 调制解调器速度（上传约 3\.3KB/s，下载约 6\.6KB/s），立即生效。

- 快捷键：Ctrl \+ M 快速切换

- 勾选后访问网站会发现网络明显变慢

### **自定义弱网参数（推荐）**

- 按 Ctrl\+R 打开 FiddlerScript（CustomRules\.js）

- 按 Ctrl \+ F 搜索 `m_SimulateModem`或找到到 `OnBeforeRequest` 函数中的弱网配置代码段，修改延迟参数：

```JavaScript
if (m_SimulateModem) {
    *// 上传：每 1KB 延迟 300ms（约 3.3KB/s）*
    oSession["request-trickle-delay"] = "300";
    *// 下载：每 1KB 延迟 150ms（约 6.6KB/s）*
    oSession["response-trickle-delay"] = "150";
}
```

- 保存后，重新勾选 Rules → Performance → Simulate Modem Speeds（修改脚本后会自动取消勾选）

### **不同网络环境参考配置**

|网络类型|request\-trickle\-delay（上行延迟）|response\-trickle\-delay（下行延迟）|说明|
|---|---|---|---|
|2G|3000ms|1500ms|极慢，测试极端场景|
|3G|200ms|100ms|中等速度|
|4G|50ms|20ms|较快，接近正常|
|极差网络|5000ms|3000ms|模拟信号极弱|

> 计算公式：延迟\(ms\) = 1000 ÷ 目标速率\(KB/s\)。例如模拟 50KB/s 下载速度，延迟 = 1000/50 = 20ms。
> 
> 

### **高级：随机延迟 \+ 丢包模拟**

在 FiddlerScript 中添加自定义函数：

```JavaScript
static function randInt(min, max) {
    return Math.round(Math.random() * (max - min) + min);
}

*// 在 OnBeforeRequest 中添加*
if (m_SimulateModem) {
    *// 随机延迟 100ms ~ 3000ms*
    var delay = randInt(100, 3000);
    oSession["request-trickle-delay"] = delay.toString();
    oSession["response-trickle-delay"] = delay.toString();
    
    *// 20% 概率模拟丢包*
    if (randInt(1, 10) > 8) {
        oSession["x-breakresponse"] = "模拟网络丢包";
    }
    
    // 丢包率 5%（二选一）
    if (Math.random() < 0.05) {
        oSession["ui-color"] = "red";
        oSession.Abort(); // 丢弃请求
    }
}
```

### **弱网测试关注点**

- 页面加载时间是否可接受

- Loading 动画/骨架屏是否正常显示

- 超时机制和重试机制是否合理

- 网络切换（WiFi → 4G → 无网）时的表现

- 异常提示文案是否友好

- 大流量页面（如商品详情页）的加载表现

---

## **🔄 测试场景二：防重放测试（Replay 重放攻击）**

防重放测试用于验证接口是否能防止同一请求被重复提交，常见于支付、签到、领券、转账等场景。

### **方法一：快速重放（单次）**

1. 在 Fiddler 中捕获目标请求（如"签到"接口）

2. 选中该请求，按快捷键 R 或右键 → Replay → Reissue Requests

3. 观察服务器是否正确拦截重复请求

### **方法二：多次重放（模拟并发）**

1. 选中目标请求，按 Shift \+ R 或右键 → Replay → Reissue Sequentially

2. 在弹出框中输入重放次数（如 20）

3. 点击 OK，Fiddler 会依次发送 20 次相同请求

4. 检查响应结果：

    - ✅ 安全：仅第 1 次返回成功，其余返回"已签到/已领取"

    - ❌ 存在漏洞：多次返回成功，说明存在重放漏洞

### **方法三：高级重放（Fiddler Everywhere）**

1. 选中请求，按 Alt \+ R 打开 Advanced Replay

2. 配置参数：

    - Number of Repeats：重放次数（最大 100000）

    - Repeat Behavior：Sequential（顺序执行）或 Parallel（并发执行）

3. 点击 Start 开始重放

### **方法四：结合断点做并发测试**

1. 设置断点拦截目标请求：Rules → Automatic Breakpoints → Before Requests

2. 在客户端触发请求，Fiddler 会拦截住

3. 选中被拦截的请求，按住 Shift 点击 Replay 按钮

4. 输入并发数量，然后点击 Go Release 放行所有请求

5. 观察是否存在并发问题（如签到奖励重复发放）

### **防重放测试常见场景**

|场景|测试方法|预期结果|
|---|---|---|
|每日签到|重放签到请求 20 次|仅第 1 次成功|
|领取优惠券|重放领券请求|仅能领取 1 张|
|转账/支付|重放支付请求|仅扣款 1 次|
|短信验证码发送|重放发送请求|有频率限制|
|积分兑换|并发重放兑换请求|仅兑换 1 次|

---

## **🛡️ 测试场景三：接口安全测试**

### **1\.** **请求参数篡改**

1. 捕获目标请求，按 F11 设置请求前断点

2. 在 Inspectors 中修改请求参数（如将金额从 `100` 改为 `0.01`，或将数量改为负数）

3. 点击 Run to Completion 放行请求

4. 检查服务器是否正确校验

### **2\.** **响应内容篡改**

1. 按 F12 设置响应后断点

2. 修改响应体内容（如将 `{"success": false}` 改为 `{"success": true}`）

3. 观察客户端是否正确处理

### **3\.** **使用 AutoResponder 模拟异常响应**

1. 打开右侧 AutoResponder 标签

2. 添加规则，例如：

    - 匹配条件：URL 包含 `api/user`

    - 响应：返回本地文件 `C:\mock\error_500.json`

3. 启用规则后，所有匹配的请求都会返回模拟的 500 错误

---

## **📊 测试场景四：接口性能测试**

### **1\.** **使用 Statistics 分析性能**

1. 选中一个或多个请求

2. 点击底部 Statistics 标签

3. 查看关键指标：

    - 总请求数、总数据传输量

    - 平均响应时间

    - 各状态码统计

### **2\.** **使用 Timeline 分析耗时**

1. 选中请求后查看 Timeline 标签

2. 关注各阶段耗时：DNS 查询 → TCP 连接 → HTTPS 握手 → 服务器处理 → 数据传输

### **3\.** **使用 Reissue and Verify 回归测试**

1. 先录制一组"正常"请求作为基线

2. 修改后端代码后，选中这些请求按 V 键（Reissue and Verify）

3. Fiddler 会自动对比新旧响应，标记出差异（状态码变化、响应体变化等）

---

## **💡 实用技巧汇总**

- 快速过滤：在左下角命令行输入 `bpu 关键词` 设置断点，输入 `bpafter 关键词` 设置响应后断点

- 清除会话：按 Ctrl \+ X 清空当前会话列表

- 保存会话：File → Save All Sessions 保存为 `.saz` 文件，方便后续分析

- 导出请求：右键请求 → Copy → Just Headers / Just Body

- 模拟不同 HTTP 状态码：访问 `http://localhost:8888/404` 可模拟 404 响应，`http://localhost:8888/500` 模拟 500 响应

> ⚠️ 注意事项：使用 Fiddler 抓包时请遵守相关法律法规，不要在公共网络环境下运行，避免泄露敏感信息。测试完成后记得关闭代理设置和 Fiddler，恢复正常网络。
> 
> 

---

## 相关笔记
- [[03-工具与安装]]
- [[Docker使用指南]]
- [[Postman接口测试]]

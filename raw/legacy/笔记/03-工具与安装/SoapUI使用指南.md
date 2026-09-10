---
type: note
tags: [接口测试] [工具] [SoapUI]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# SoapUI 使用指南

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 测试工具章-SoapUI 小节

## **工具简介**

**SoapUI** 是 SmartBear 开发的一款功能强大的开源 API 测试工具，广泛应用于 Web 服务和 REST API 的测试。它不仅支持 SOAP 协议，还支持 REST、HTTP、JMS 等多种协议。SoapUI 提供免费的开源版本（Open Source）和功能更全面的付费专业版（Pro）。

核心功能包括：

- SOAP 和 RESTful Web 服务测试

- 可视化 WSDL/Swagger 解析与请求构建

- 功能测试、负载测试、安全测试

- 数据驱动测试

- Mock 服务模拟

## **安装前准备**

### **2\.1 Java 环境要求**

SoapUI 基于 Java 开发，运行前需要安装 JDK 或 JRE。

|操作系统|推荐 JDK 版本|最低内存|
|---|---|---|
|Windows 10/11|JDK 11 \(x64\)|4GB RAM|
|macOS Monterey\+|JDK 8 \(ARM64\)|4GB RAM|
|Ubuntu 20\.04 LTS|OpenJDK 11|2GB RAM|

**配置 JAVA\_HOME 环境变量：**

- Windows：系统属性 → 高级 → 环境变量 → 新增系统变量 `JAVA_HOME`，指向 JDK 根目录

- Linux/macOS：在 `~/.bashrc` 或 `~/.zshrc` 中添加：

- bash

- export JAVA\_HOME=/usr/lib/jvm/java\-11\-openjdk\-amd64export PATH=$JAVA\_HOME/bin:$PATH

> 注意：如果使用 SoapUI 的安装包（带 JRE 的版本），系统自带的 Java 环境并非必需。但如果使用独立发行版，则必须提前安装 Java。
> 
> 

---

### **2\.2 下载 SoapUI**

访问 SoapUI 官方网站：[https://www\.soapui\.org/downloads/soapui/](https://www.soapui.org/downloads/soapui/) 

根据操作系统选择对应版本下载：

- Windows：`.exe` 安装包

- macOS：`.dmg` 安装包

- Linux：`.sh` 脚本或 `.tar.gz` 压缩包

---

## **安装步骤**

### **3\.1 Windows 系统安装**

1. 运行安装程序：双击下载的 `.exe` 文件，建议以管理员身份运行（右键 → “以管理员身份运行”）

2. 安装向导：

    - 点击“下一步”继续

    - 选择安装目录（或保留默认）

    - 选择要安装的组件：

        - SOAP UI：默认必选

        - Source：源代码（可选）

        - Hermes JMS：JMS 测试支持（按需）

        - Tutorials：教程文档（按需）

    - 接受许可协议

    - 选择开始菜单文件夹位置

    - 勾选“创建桌面图标”（推荐）

3. 完成安装：点击“完成”，SoapUI 将自动启动

---

### **3\.2 macOS 系统安装**

1. 打开下载的 `.dmg` 文件

2. 将 SoapUI 图标拖拽到“应用程序”文件夹中

3. 首次启动时，如果系统提示安全警告，需在“系统偏好设置 → 安全性与隐私”中允许运行

---

### **3\.3 Linux 系统安装**

**方式一：使用 \.sh 脚本安装**

```Shell
# 给予执行权限
chmod +x SoapUI-x64-5.x.x.sh

# 运行安装脚本
./SoapUI-x64-5.x.x.sh
```

**方式二：使用 \.tar\.gz 压缩包 **

```Shell
# 解压
tar -xvzf soapui-<version>-bin.tar.gz

# 进入目录
cd soapui-<version>/bin

# 启动
./soapui.sh
```

---

## **验证安装**

安装完成后，启动 SoapUI 查看主界面是否正常显示。主界面包含以下主要区域：

- 菜单栏：文件、编辑、视图、工具、帮助等

- 工具栏：常用功能快捷按钮

- 项目浏览器（左侧）：显示项目、测试套件、测试用例

- 编辑器区域（中央）：编辑请求、响应等

- 日志窗口（底部）：显示执行日志

---

## **基本使用指南**

### **5\.1 创建工作区（Workspace）**

首次使用 SoapUI 时，建议先创建工作区来管理项目：

1. 点击 “File” → “New Workspace”

2. 输入工作区名称

3. 选择保存路径，点击“保存”

---

### **5\.2 创建 SOAP 项目**

1. 点击 “File” → “New SOAP Project”

2. 输入项目名称

3. 在 “Initial WSDL” 字段输入 WSDL 的 URL 或点击 “Browse” 选择本地 WSDL 文件

4. 勾选 “Create sample requests” 创建示例请求

5. 点击 “OK”

> WSDL 解析成功后，左侧导航树将自动生成接口定义、绑定操作和可调用方法列表。
> 
> 

---

### **5\.3 创建 REST 项目**

1. 点击 “File” → “New REST Project”

2. 输入 REST API 的 URI 地址

3. 或导入 Swagger/OpenAPI 规范文件

4. 点击 “OK” 完成创建

---

### **5\.4 创建测试套件（TestSuite）**

右键点击项目 → “New Test Suite” → 命名测试套件

测试套件用于组织一个或多个测试用例。

---

### **5\.5 创建测试用例（TestCase）**

右键点击测试套件 → “Add Test Case” → 命名测试用例

---

### **5\.6 添加测试步骤**

在测试用例中，可以添加多种测试步骤：

- SOAP Request：发送 SOAP 请求

- REST Request：发送 REST 请求

- Groovy Script：执行 Groovy 脚本

- JDBC Request：数据库测试

- Property Transfer：属性传递

**添加 SOAP 请求步骤：**

1. 在测试用例中右键 → “Add Step” → “SOAP Request”

2. 选择对应的操作（Operation）

3. 在请求编辑器中填写或修改 XML 请求体

4. 点击运行按钮发送请求

---

### **5\.7 添加断言（Assertion）**

断言用于验证 API 响应是否符合预期。

添加方法：

1. 在请求编辑器中点击 “Assertions” 选项卡

2. 点击 “Add” 按钮

3. 选择断言类型：

    - HTTP 状态码断言：验证状态码（如 200 OK）

    - Contains 断言：验证响应是否包含特定字符串

    - XPath 匹配断言：验证 XML 节点值

    - 响应时间断言：验证响应时间阈值

    - Schema 合规性断言：验证 XML/JSON 结构合规

    - 脚本断言：使用 Groovy 脚本自定义验证逻辑

4. 配置断言条件，点击 “OK”

---

### **5\.8 执行测试**

- 运行单个测试用例：点击测试用例的绿色运行按钮

- 运行整个测试套件：点击测试套件的运行按钮

- SoapUI 会实时显示请求/响应详情和断言结果

---

## **高级功能**

### **6\.1 数据驱动测试**

1. 在测试用例中添加 “DataSource” 步骤

2. 选择数据源类型（CSV、Excel、数据库等）

3. 配置列映射

4. 在请求中使用占位符：`${DataSource#columnName}`

5. 添加 “DataSource Loop” 步骤遍历所有数据行

---

### **6\.2 负载测试**

1. 右键点击测试用例 → “New LoadTest”

2. 配置参数：

    - Threads：模拟的并发用户数（最多 9999）

    - Strategy：负载策略（Simple、Burst 等）

    - Limit：限制条件（持续时间或运行轮次）

3. 点击运行按钮执行负载测试

4. 可添加负载测试断言实现自动化验证

---

### **6\.3 Mock 服务**

当真实服务不可用时，可使用 Mock 服务模拟。

创建步骤：

1. 右键点击接口 → “Generate MockService”

2. 配置监听端口（如 8088）

3. 添加响应模板

4. 点击绿色播放按钮启动 Mock 服务

---

### **6\.4 Groovy 脚本**

SoapUI 支持 Groovy 脚本，可用于：

- 动态生成测试数据

- 处理复杂的验证逻辑

- 模拟特定测试场景

- 提取和传递属性值

---

## **常见问题与优化**

### **7\.1 安装问题**

|问题|解决方案|
|---|---|
|安装失败/无法启动|检查是否已安装 JDK/JRE|
|权限不足|以管理员身份运行安装程序|
|进度条卡住|关闭杀毒软件实时防护后重试|
|提示 \.NET Framework 缺失|通过 Windows 功能启用 \.NET 3\.5|
|macOS 启动无响应|修改 vmoptions\.txt，添加 \-Dsoapui\.browser\.disabled=true|
|1603 错误代码|清理临时文件夹后重试|

---

### **7\.2 启动后优化**

调整内存配置：

1. 找到 SoapUI 安装目录下的 `soapui.vmoptions` 文件

2. 编辑文件，增加内存设置：

3. text

4. \-Xms512m\-Xmx2048m

配置代理（如需通过代理访问）：

- “工具” → “选项” → “网络” → 设置代理服务器

---

### **7\.3 版本兼容性**

- 确保 JDK 架构与 SoapUI 架构匹配（64 位 SoapUI 需搭配 64 位 Java）

- 官方推荐使用 JDK 8 或 JDK 11 LTS 版本

---

## **参考资源**

- 官方网站：[https://www\.soapui\.org/](https://www.soapui.org/)

- 下载页面：[https://www\.soapui\.org/downloads/soapui/](https://www.soapui.org/downloads/soapui/)

- 官方文档：[https://www\.soapui\.org/docs/](https://www.soapui.org/docs/)

---

## 相关笔记
- [[03-工具与安装]]
- [[Postman接口测试]]
- [[Mock接口桩]]

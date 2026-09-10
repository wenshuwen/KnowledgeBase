---
type: note
tags: [AI] [知识库] [RAG]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# AI 知识库搭建（私有化方案）

> 📌 来源：[[Test-测试经验总结-原文]] ｜ AI章-知识库 小节（私有化搭建/OpenCode&Hermes/应用场景）

## **6\.1 私有化知识库搭建方案**

### **方案总览与选型**

|**方案**|**技术栈**|**上手难度**|**适合场景**|
|---|---|---|---|
|A\. Dify \+ Ollama（推荐）|Docker Desktop \+ Dify \+ Ollama|中|个人/团队，需要 Agent 编排和 API 接入|
|B\. AnythingLLM 桌面版|纯 Windows 安装包|低|个人使用，追求最快上手，不想碰 Docker|
|C\. RAGFlow \+ Ollama|Docker \+ RAGFlow|高|文档量大、表格/扫描件多，对检索质量要求高|
|D\. MaxKB \+ Ollama|Docker \+ MaxKB|低|小团队内部使用、需要权限管理和标准API|

> *方案共用同一个推理底座**** Ollama****（本地大模型运行时），区别只在知识库应用层。*
> 
> 

- **硬件要求**

|**配置档位**|**规格**|**可运行模型**|**体验**|
|---|---|---|---|
|入门|16GB 内存，无独显|Qwen2\.5 3B / 7B（CPU 量化版）|可用，速度较慢|
|推荐|32GB 内存 \+ RTX 3060 12G|Qwen2\.5 7B / 14B 量化版|流畅|
|高配|RTX 4090 24G|Qwen2\.5 32B / DeepSeek\-R1 蒸馏版|高质量回答|

> *纯 CPU 也能跑，7B 量化模型在 16GB 内存机器上约 5\-10 token/s，做知识库问答完全够用。*
> 
> 

- **向量数据库选型**

|数据库|特点|适用规模|
|---|---|---|
|Milvus|百亿级向量秒级检索，分布式架构，索引类型丰富|中大规模生产环境|
|Chroma|轻量嵌入式，开箱即用，Python 原生|小规模/快速原型|
|FAISS|Meta 开源，纯检索库，性能极高|需要深度定制的场景|
|Elasticsearch \+ 向量插件|全文检索 \+ 向量检索混合|需要关键词\+语义混合检索|

> *对于测试用例设计场景，文档量通常在几千到几万篇，Chroma（轻量起步）或 Milvus（生产级）都是合适的选择。*
> 
> 

---

### **第一步：安装 Ollama（方案共用的底座）**

- 访问 `https://ollama.com/download` 下载 Windows 版安装包，双击安装（默认装到 `C:\Users\<你>\AppData\Local\Programs\Ollama`）。

- 安装完成后系统托盘出现 Ollama 图标，服务默认监听 `127.0.0.1:11434`。

- 拉取模型（PowerShell 中执行）：

```Shell
# 对话模型：中文能力强的 7B（约 4.7GB）
ollama pull qwen2.5:7b

# Embedding 模型：中文检索效果好的 bge-m3（约 1.2GB）
ollama pull bge-m3

# 可选：重排模型，提升检索精度
ollama pull bge-reranker-v2-m3
```

- 验证：

```Shell
ollama list          # 查看已装模型
ollama run qwen2.5:7b "你好"   # 测试对话
```

- **让 Docker 容器能访问 Ollama**：设置环境变量后重启 Ollama

```Shell
# 以管理员身份打开 CMD 执行
setx OLLAMA_HOST "0.0.0.0:11434" /M

[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:11434", "User")
```

> *模型文件存放在 **`C:\Users\<你>\.ollama\models`**，磁盘紧张可迁移到其他盘（设置 **`OLLAMA_MODELS`** 环境变量）。*
> 
> 

---

### **方案 A：Dify \+ Ollama（推荐，功能最全）**

**a\.** **安装 Docker Desktop**

- 以管理员身份打开 PowerShell，执行：

```Shell
wsl --install
```

> *重启电脑后，下载安装 Docker Desktop（**`https://www.docker.com/products/docker-desktop/`**），安装时确认勾选 "Use WSL 2 based engine"，安装完成后打开 Docker Desktop，等待右下角图标变为绿色（Engine running）。*
> 
> 

- 设置 → Resources → WSL Integration：确认内存分配（建议 ≥ 8GB，纯 CPU 跑 7B 模型时 Ollama 走宿主机，不占容器资源），重启 Docker 生效。

- 前往 Git 官网下载 Windows 版安装包，一路默认安装即可。装完后在 PowerShell 中执行 `git --version` 确认安装成功。

---

**b\.** **部署 Dify**

```Shell
git clone https://github.com/langgenius/dify.git
cd dify\docker
copy .env.example .env
docker compose up -d
```

> *首次拉取镜像约 10\-20 分钟。完成后访问 **`http://localhost`** 初始化管理员账号。*
> 
> 

- **初始化 Dify：**浏览器访问 `http://localhost/install`，首次进入设置管理员账号（用户名、密码、邮箱），完成后即可登录 Dify 后台。

---

**c\.** **接入本地模型**

Dify 页面右上角「**设置 → 模型供应商 → Ollama**」：

- LLM：名称 `qwen2.5:7b`，地址 `http://host.docker.internal:11434`

- Text Embedding：名称 `bge-m3`，地址同上

- Rerank：名称 `bge-reranker-v2-m3`，地址同上

> *`host.docker.internal`** 是 Docker Desktop 访问宿主机（Ollama）的固定地址，这是 Windows 上最常见的坑，写 **`localhost`** 是不通的。*
> 
> 

---

**d\.** **创建知识库**

- 「**知识库 → 创建知识库**」，上传文档（支持 PDF/Word/TXT/Markdown/网页链接），扫描版 PDF 需先做 OCR 处理。

- 分段设置（决定检索质量的关键参数）：

    - 分段标识符：默认 `\n\n`

    - 最大 chunk 长度：**500 tokens**（中文文档建议 400\-600）

    - 重叠长度：**50 tokens**（避免语义被切断）

    - 索引方式：高质量模式（用 bge\-m3 向量化）

    - 检索设置：向量检索 \+ 开启 Rerank

- 配置分段策略：

|参数|推荐值|说明|
|---|---|---|
|分段模式|自动（通用）|按段落和标题自动切分|
|分段最大长度|500\-800 tokens|太短信息不完整，太长检索精度下降|
|分段重叠长度|50\-100 tokens|避免上下文断裂|

- 建议开启「问答模式（Q\&A）」：Dify 会先用 LLM 把每段文档改写成"问题\-答案"对再入库，检索命中率明显更高（消耗一次本地推理时间）。

---

**e\.** **创建 Agent 应用**

- 「**工作室 → 创建应用 → Agent**」。

- 编排提示词，绑定刚才的知识库，添加工具（如联网搜索关闭、代码解释器按需）。

- 发布后即可在 Web UI 对话；「访问 API」页面提供 OpenAI 风格的 REST API，供其他系统调用。

> *Dify 本身内置了完整的 Agent 编排和工作流能力，支持可视化拖拽搭建复杂的多步骤 AI 流程（如意图识别 → 知识检索 → 条件分支 → 生成回答），无需额外对接即可在平台内完成 Agent 场景搭建。*
> 
> 

---

### **方案 B：AnythingLLM 桌面版（零门槛桌面版）**

> **方案优势**
> 
> 

- 零命令行、零Docker依赖，双击安装即用，3分钟完成部署

- 内置LanceDB向量库，无需额外配置中间件

- 支持多工作区隔离，不同项目知识库互不干扰

- 提供标准OpenAI兼容API，可直接对接Coze、Dify、扣子等Agent平台，也支持MCP协议对接Claude Code、Cursor等编程Agent

- 最低8GB内存即可运行，无显卡也能正常使用

> **部署步骤**
> 
> 

- 访问 `https://anythingllm.com/desktop` 下载 Windows 安装包，双击安装。

- 首次启动向导：

    - LLM 偏好：选 **Ollama**，地址 `http://127.0.0.1:11434`，模型选 `qwen2.5:7b`

    - Embedding：选 Ollama 的 `bge-m3`

    - 向量数据库：默认内置 **LanceDB**（无需安装任何数据库）

- 左侧「工作区」上传文档 → 自动解析入库 → 直接对话。

- 它自带 **Developer API**（设置 → API Keys 生成密钥），也可以作为服务端被其他程序调用，即可用标准OpenAI接口格式对接外部Agent工具。

- 缺点：编排能力和检索调优不如 Dify/RAGFlow

> **适配Agent工具**
> 
> 

Coze、Dify、扣子等低代码Agent平台，Claude Code、Cursor、Cline等编程Agent，自定义Python/Node\.js脚本

---

### **方案 C：RAGFlow（文档解析最强）**

> **方案优势**
> 
> 

- 文档解析能力行业领先，支持复杂表格、图表、多栏排版PDF的精准识别，解析准确率比同类方案高30%以上

- 支持BM25\+语义双路检索\+交叉编码器重排序，技术文档、合同等专业资料问答准确率更高

- 拖拽式流程设计器，50\+预置组件，可自定义完整RAG工作流

- 提供完整API和Web应用发布能力，可嵌入企业内部门户，也可作为工具接入任意Agent平台

- 支持单文件最大1GB，批量上传32个文件，适合大规模文档处理

> **部署步骤**
> 
> 

当你的资料以扫描件 PDF、复杂表格、合同为主时选它。

1. 环境准备：安装Docker Desktop和WSL2，建议硬件配置16GB以上内存、50GB以上可用磁盘

2. 拉取代码：克隆RAGFlow官方仓库，进入docker目录，修改`.env`文件启用内置嵌入模型

3. 启动服务：执行`docker compose up -d`，等待所有容器状态变为healthy，浏览器访问`http://localhost`*`:80`*即可进入可视化界面

4. 配置使用：添加Ollama本地模型，创建知识库上传文档，即可创建对话应用或生成API接口，模型供应商同样配置 Ollama（`http://host.docker.internal:11434`），上传文档后选择解析模板（通用/书籍/法律/简历/表格等），RAGFlow 会做深度版面分析，表格能按单元格对齐解析——这是它对比 Dify 内置解析的最大优势。

```Shell
# 需要至少 4 核 CPU + 16GB 内存（RAGFlow 较吃资源）
git clone https://github.com/infiniflow/ragflow.git
cd ragflow\docker

# 编辑 .env 确认 RAGFLOW_IMAGE 为 slim 或 full 版
docker compose up -d
```

> **适配Agent工具**
> 
> 

所有支持OpenAI兼容接口的Agent平台，企业级自研Agent系统，需要高精度文档检索的专业场景

---

### **方案 D：MaxKB（适合复杂文档场景）**

> **方案优势**
> 
> 

- 一行Docker命令完成部署，资源占用低，2核4GB内存即可流畅运行

- 完整的可视化后台，支持用户权限管理、知识库分类、对话日志追溯

- 支持高级工作流编排，可自定义检索逻辑、提示词模板

- 提供标准RESTful API，可直接对接飞书、钉钉、企业微信机器人，也可作为工具节点接入Coze、Dify等Agent平台

- 双层检索架构，中文问答准确率高于同类轻量方案

> **部署步骤**
> 
> 

1. 安装Docker Desktop：官网下载Windows版，安装后启动，确认左下角显示Engine running

2. 部署MaxKB：打开PowerShell，执行命令`docker run -d --name=maxkb --restart=always -p 8080:8080 -v C:/maxkb:/var/lib/postgresql/data -v C:/python-packages:/opt/maxkb/app/sandbox/python-packages ``registry.fit2cloud.com/maxkb/maxkb`，等待镜像下载完成

3. 登录后台：浏览器访问`http://localhost:8080`，默认账号`admin`，密码`MaxKB@123..`，首次登录修改密码

4. 配置使用：在系统管理\-模型设置中添加Ollama本地模型或云端模型API，创建知识库上传文档，即可创建应用对外提供服务

> **适配Agent工具**
> 
> 

飞书/钉钉/企业微信机器人，Coze、Dify、FastGPT等Agent平台，企业内部自研业务系统

---

### **方案 E：local\-knowledge\-base（接口最丰富）**

> **方案优势**
> 
> 

- 可视化界面：Vue 3 \+ Element Plus 管理后台，支持文档上传、知识图谱可视化编辑

- API接口：同时提供 REST API、OpenAI兼容端点 和 MCP Server 三种接口

- 多租户隔离：每台电脑独立API密钥，权限隔离

- 部署方式：Python原生运行，无需Docker

> **部署步骤**
> 
> 

```Shell
# 后端
cd knowledge-base/backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（另一个终端）
cd knowledge-base/frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173` 使用界面，API文档在 `http://127.0.0.1:8000/docs`

> **适配Agent工具**
> 
> 

需要对接多种Agent工具（支持MCP协议）、多租户隔离、技术团队二次开发

---

### **知识库构建流程**

这是整个系统最关键的环节，直接决定了 Agent 回答的质量：

> **文档整理与预处理**
> 
> 

将你的知识内容按类别组织：

```Plain Text
knowledge_base/
├── 需求文档/          # PRD、MRD 等
│   ├── 项目A_需求v1.2.pdf
│   └── 项目B_功能清单.xlsx
├── 功能模块/          # 模块说明、接口文档
│   ├── 用户模块_设计说明.md
│   └── 支付模块_API文档.pdf
├── 业务流程/          # 流程图、SOP
│   ├── 订单流程_泳道图.png
│   └── 退款流程_说明.docx
└── 测试规范/          # 测试标准、历史用例
    ├── 测试用例编写规范.md
    └── 历史缺陷库.xlsx
```

---

> **文档分块策略**
> 
> 

分块（Chunking）质量直接影响检索效果：

- 按语义分块：以段落、章节为单位，保持语义完整性（推荐）

- 按固定长度分块：如 512 tokens 一块，设置 50\-100 tokens 的重叠

- 按文档结构分块：利用标题层级自动切分（RAGFlow 的 DeepDoc 支持此功能）

> *⚠️ 对于需求文档，建议保留文档标题 \+ 章节标题作为元数据，检索时可以按模块/功能过滤。*
> 
> 

---

> **向量化与入库**
> 
> 

```Python
*# 示例：使用 BGE-M3 嵌入模型 + Chroma 存储*
from chromadb import Client
from sentence_transformers import SentenceTransformer

*# 加载嵌入模型（中文推荐 BGE-M3 或 text2vec-large-chinese）*
model = SentenceTransformer("BAAI/bge-m3")

*# 文档分块后向量化并存储*
chunks = split_documents(docs)  *# 你的分块逻辑*
embeddings = model.encode(chunks)
collection.add(documents=chunks, embeddings=embeddings, metadatas=metas)
```

---

### **Agent 工具接入**

> **对接Agent工具的通用说明**
> 
> 

所有方案均支持两种主流对接方式：

1. OpenAI兼容接口：在知识库平台生成API Key后，将接口地址和Key填入Agent工具的自定义模型配置中，即可作为Agent的知识检索工具使用

2. MCP协议：AnythingLLM、RAGFlow均支持MCP协议，可直接配置到Claude Code、Cursor等编程Agent中，Agent可自主判断是否需要检索知识库，无需手动触发

知识库跑起来后，通过以下方式对外提供服务（可同时启用）：

- **MCP 接入（WorkBuddy / Claude Desktop / Cursor）**：把 Dify 的知识库检索 API 包一层 FastMCP，注册到工具的 MCP 配置中。

- **REST API**：Dify / RAGFlow / AnythingLLM 自带 API \+ API Key，供 Dify、Coze 类平台或其他业务系统直接调用。

- **OpenAI 兼容接口**：用 LiteLLM 代理包装后，任何支持"自定义模型地址"的工具都能把你的知识库当成一个模型使用。

> *网络打通要点：跨设备访问时确保 Windows 防火墙放行端口（如 80/11434），跨网络用 Tailscale 组网，不要直接暴露公网。*
> 
> 

---

### **常见问题与调优**

|**问题**|**原因与解决**|
|---|---|
|容器连不上 Ollama|地址必须写 [http://host\.docker\.internal:11434](http://host.docker.internal:11434)，且 Ollama 已设置 OLLAMA\_HOST=0\.0\.0\.0:11434 并重启 Ollama|
|回答驴唇不对马嘴|检索环节问题：调小 chunk（300\-400）、开启 Q\&A 模式、加 Rerank；先在知识库的"召回测试"里验证命中率|
|回答编造内容|提示词中明确"仅根据检索到的资料回答，检索不到就说不知道"，并降低模型的 temperature 到 0\.2 以下|
|内存不足卡死|换 3B 模型，或用 qwen2\.5:7b\-instruct\-q4\_K\_M 量化版；WSL2 内存上限调低给系统留余量|
|模型下载慢|使用镜像加速：设置 OLLAMA\_HOST 同级的环境变量 HTTPS\_PROXY，或从 ModelScope 下载 GGUF 后 ollama create 导入|
|文档更新|Dify 支持单个文档重新索引；大批量更新建议写脚本走 API，避免全量重建|
|镜像拉取超时|Docker Desktop → Settings → Docker Engine 中添加国内镜像加速源|
|80 端口被占用|修改 `.env` 中的 `EXPOSE_NGINX_PORT` 为其他端口（如 8080）|
|服务运行卡顿|Docker Desktop 内存分配调至 12GB\+，或使用更小的模型（如 `qwen2.5:4b`）|
|知识库检索不到内容|检查 Embedding 模型是否正确配置，尝试调整分段大小和重叠长度|

### **备份与维护**

- **必备份目录**：Dify 的 `docker/volumes/`（含向量库和 Postgres）、Ollama 的 `~/.ollama/models`、原始文档源目录

- **备份命令示例**：`robocopy D:\dify\docker\volumes E:\backup\dify /E /COPYALL`

- **定期升级**：`git pull && docker compose pull && docker compose up -d`（升级前先备份 volumes）

---

### **实施选型建议**

**第 1 天**：装 Ollama \+ AnythingLLM，快速体验效果、验证硬件是否够用

**第 2\-3 天**：部署 Dify，导入真实文档，调优分段和检索参数

**第 1 周内**：包一层 MCP/REST API，接入日常使用的 Agent 工具

**后续**：按需加权限隔离（多知识库 \+ 应用级访问控制）、Rerank 模型、文档自动同步管道

- 个人使用、快速验证需求：优先选AnythingLLM桌面版，零门槛上手

- 小团队内部使用、需要权限管理和标准API：选MaxKB，部署简单资源占用低

- 有大量复杂格式文档、对检索准确率要求高：选RAGFlow，文档解析和检索能力最强

## **6\.2 OpenCode \& Hermes**

> **核心原理：Hermes 的双重身份**
> 
> 

Hermes Agent 在 MCP 体系中有两个身份：

- MCP Client：连接外部工具（GitHub、数据库、文件系统等）

- MCP Server：把自身的能力（记忆、会话、知识库、Skill）暴露给其他 AI 客户端

OpenCode 则是一个纯 MCP Client——它只能连接外部 MCP Server，不能反过来被别人调用。所以互补的方式就是：

```Plain Text
OpenCode（MCP Client）──调用──→ Hermes（MCP Server）
    │                              │
    │  获得 Hermes 的记忆、知识、     │  管理记忆、Skill、
    │  会话历史、用户偏好等能力        │  知识库、Obsidian Vault
    │                              │
    └── 专注代码编写和工程任务       └── 专注知识管理和个人助理
```

---

> **具体实现步骤**
> 
> 

**第一步：启动 Hermes MCP Server**

Hermes 内置了 `mcp serve` 子命令，一条命令就能把自己暴露为 MCP 服务器：

```Shell
*# 启动 Hermes MCP Server（默认 stdio 模式）*
hermes mcp serve

*# 加 -v 输出详细日志，方便调试*
hermes mcp serve -v
```

启动后，Hermes 会通过标准输入输出（stdio）提供以下能力给调用方：

- 读取会话记忆：`MEMORY.md` 和 `USER.md` 中的持久化信息

- 搜索历史会话：通过 SQLite FTS5 全文检索过往对话

- 查询知识库：Obsidian Vault 中的笔记和 LLM Wiki 页面

- 调用 Skill：已固化的可复用操作经验

**第二步：在 OpenCode 中配置接入**

OpenCode 的 MCP 配置统一放在项目根目录的 `opencode.json` 中。有两种接入方式：

- **方式一：stdio 模式（推荐，本地直连）**

```JSON
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "hermes": {
      "type": "local",
      "command": ["hermes", "mcp", "serve"],
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

> *这种方式下，OpenCode 启动时会自动拉起一个 Hermes 子进程，通过 stdio 管道通信，无需手动启动 Hermes，也无需开放端口。*
> 
> 

- **方式二：remote 模式（HTTP/SSE，适合远程或共享场景）**

如果你希望 Hermes 长期运行在后台（比如跑在一台服务器上，多个 OpenCode 实例共用），可以用 SSE 模式：

```Shell
*# 先启动 Hermes MCP Server（SSE 模式，监听端口）*
hermes mcp serve --transport sse --port 9119
```

然后在 OpenCode 配置中：

```JSON
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "hermes": {
      "type": "remote",
      "url": "http://localhost:9119/sse",
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

**第三步：验证连接**

配置完成后，在 OpenCode 中验证：

```Shell
*# 进入 OpenCode 后，输入斜杠命令*
/mcps
```

如果 `hermes` 显示为 `connected`，说明接入成功。你也可以在对话中直接测试：

```Plain Text
使用 hermes 工具搜索一下我之前关于"退款流程"的讨论记录
```

---

> **互补使用的实际场景**
> 
> 

接入后，两个工具各自发挥所长：

- **场景一：测试用例设计（知识在 Hermes，编码在 OpenCode）**

```Plain Text
工作流：
1. 在 Hermes 中积累需求文档、业务流程、历史缺陷（通过 Obsidian Skill + LLM Wiki）
2. 在 Hermes 中记录你的测试偏好（写入 MEMORY.md / USER.md）
3. 在 OpenCode 中编写测试代码时，通过 hermes MCP 工具：
   - 查询相关需求文档 → 确保覆盖完整
   - 获取历史缺陷模式 → 补充回归测试
   - 读取测试规范 → 保持用例格式一致
```

- **场景二：代码审查 \+ 知识回溯**

```Plain Text
工作流：
1. 在 OpenCode 中做代码审查，发现一个可疑的支付逻辑
2. 调用 hermes 工具搜索历史会话："之前讨论过的支付模块边界条件"
3. Hermes 返回之前的讨论记录和决策依据
4. 结合代码和知识，给出更精准的审查意见
```

- **场景三：个人偏好跨工具同步**

```Plain Text
Hermes 中设置：
> 记住：我偏好 pytest 框架，测试函数命名用 test_<功能>_<场景>_<预期> 格式
> 记住：我们项目用 tabs 缩进，不用 spaces

→ 这些偏好自动写入 USER.md
→ OpenCode 通过 hermes MCP 读取后，生成的测试代码自动遵循这些规范
```

---

> **关于写入对话记忆和个人偏好**
> 
> 

这是你问题的核心关切。完全可以，而且 Hermes 天然支持。

- **写入机制**

Hermes 的记忆写入有两种触发方式：

- 自动写入：当你在对话中纠正 Hermes、告诉它新约定、或说"记住这个"，它会自动更新 `MEMORY.md` 和 `USER.md`

- 显式指令：直接说"记住：xxx"或"以后都按 xxx 来做"

```Plain Text
*# 在 Hermes 对话中*
> 记住：我们项目的测试用例必须包含正向、异常、边界值三类场景
> 记住：我习惯用中文写测试用例描述，断言用英文
> 记住：支付模块的超时阈值是 30 秒，不是 60 秒
```

这些内容会被持久化到 `~/.hermes/MEMORY.md` 和 `~/.hermes/USER.md`，每次新会话自动加载。

- **从 OpenCode 侧触发写入**

通过 Hermes MCP Server 暴露的工具，OpenCode 也可以间接触发记忆写入：

```Plain Text
在 OpenCode 中：
> 使用 hermes 工具，把"退款接口新增了 retry_count 参数"这条信息记录到记忆中

→ Hermes 收到请求 → 更新 MEMORY.md → 下次会话自动携带这条知识
```

- **个人偏好层**

|文件|内容类型|示例|
|---|---|---|
|USER\.md|你是谁、偏好风格|"我是 QA 工程师，偏好简洁回答"|
|MEMORY\.md|项目约定、踩坑记录|"支付超时阈值 30s"、"用 tabs 不用 spaces"|
|skills/|固化的操作经验|"测试用例生成 SKILL\.md"——成功路径自动沉淀|

---

> **注意事项**
> 
> 

- 上下文消耗：每个 MCP Server 的工具描述都会占用 OpenCode 的上下文窗口，Hermes 暴露的工具较多时需要注意。建议在 Hermes MCP Server 侧用 `allowed_tools` 做白名单过滤，只暴露你需要的能力

- 配置生效：Hermes 侧修改 MCP 配置后需要重启或用 `/reload-mcp` 热重载；OpenCode 侧修改 `opencode.json` 后重启即可

- 安全隔离：Hermes 默认不会把系统环境变量传递给 MCP 子进程，敏感信息需要显式配置

- stdio 模式优先：如果是单机使用，stdio 模式比 SSE 更安全（不开放端口）且更简单（无需手动管理进程）

---

> **总结**
> 
> 

整个方案的核心就一句话：`hermes mcp serve` 把 Hermes 变成 MCP Server，OpenCode 在 `opencode.json` 里配置连接它。Hermes 负责知识管理和记忆持久化，OpenCode 负责代码编写和工程任务，两者通过 MCP 协议实时互通，共享知识库和用户偏好。

## **6\.3 知识库应用场景**

---

## 相关笔记
- [[07-AI与测试]]
- [[AIRAG检索增强生成]]
- [[AIMCP模型上下文协议]]

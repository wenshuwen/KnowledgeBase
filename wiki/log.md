# 操作日志（append-only）

> 只追加，不修改历史条目。格式固定，便于 `grep "^## \[" wiki/log.md | tail -10` 快速回看。
>
> 条目格式：
> ```
> ## [YYYY-MM-DD] 操作类型 | 标题
> 简述。
> ```
> 操作类型：`ingest` | `query` | `lint` | `schema` | `refactor`

---

## [2026-09-10] schema | 知识库初始化
建立三层目录骨架（raw / wiki / meta），写入 WIKI-SCHEMA.md v0.1，建立 index.md 与 log.md。
基于 16 题需求澄清结论：经验图谱优先、单源精读、中文文件名 + 英文标签、分层索引、每周体检 + 本地 Git。

## [2026-09-10] ingest | 知识库搭建会话归档
来源：本次搭建会话（用户口述"归档下当前会话的经验总结"，属对话回填渠道，要点经双方共同经历，无需二次确认）。
原料落盘 `raw/notes/2026-09-10 知识库搭建会话要点.md`。
新建 4 页：[[知识库搭建记录]]、[[编译式wiki与RAG的选型对比]]、[[需求澄清的五维度框架]]、[[llm-wiki 编译式知识库]]。
索引已同步；标签体系新增 `knowledge-management`。
脱敏检查：无需脱敏（内容不涉及项目名、域名、业务数据、凭据）。
产出：本库首批页面，规模 0 → 4 页。

## [2026-09-10] schema | 面试助手渲染契约 v0.2
新增第 8 节：`publish` + `interview{cat,kind,level,q}` 字段、cat 十二类枚举、kind 与站点渲染组件映射、面试内容目录归属规则（8.5）。
新增视图标签 `interview`；6 个模板追加两个字段；新建 `meta/templates/interview-block.md`。
新增目录 `raw/interview/`（每日抓取流水）、`raw/legacy/`（旧库原料）、`wiki/75-面试助手/`（索引与专题）。

## [2026-09-10] ingest | 旧库原料导入 + 面试助手入口页
旧 Obsidian 库（`~/WorkBuddy/知识库/`）导入 `raw/legacy/`：67 篇，1.4M，含 Linux 11 篇、AI 与测试 9 篇、安全测试 8 篇、工具 7 篇、数据库 5 篇、测试理论 5 篇、知识地图 2 篇。
排除项：`.obsidian/`、`.workbuddy/`、`copilot/skills/`（插件技能非知识）、vault 元文件（首页/README/总目录/流水账）。
新建 [[面试助手题库索引]] 作为站点入口页。
脱敏检查：旧库内容为通用技术知识，未发现项目名与凭据。
规模 4 → 5 页。

## [2026-09-10] ingest | 首批面试内容编译（性能方向）
按单源精读从 `raw/legacy/` 编译 3 页，形成互相成网的小集群：
- [[性能瓶颈的分层模型]]（concept / performance-testing / knowledge）—— 七层模型与健康阈值
- [[性能瓶颈定位的分层排查路径]]（concept / performance-testing / question）—— 四步排查顺序 + 优化五方向
- [[Redis缓存的五类经典问题]]（concept / database-linux / knowledge）—— 五类问题对照 + 测试用例落点
三页均挂到 [[面试助手题库索引]]，出链密度 2–3 条，无孤页。
规模 5 → 8 页。

## [2026-09-10] schema | 构建脚本 build_kb.py 上线
`~/WorkBuddy/2026-09-02-22-53-01/interview-assistant/build_kb.py` 跑通：wiki/ → kb.json。
已验证：publish:false 构建期过滤（正文完全不出现在产物中）、非法 cat 拦截并入待修清单、重复构建版本号一致（内容哈希）。
产物版本 kb-2026.09.10-66a190c7，4 条上站。

## [2026-09-10] schema | 站点上线 + 自动化串联
- 面试助手改造后重新部署到线上，链接未变：https://eeb7d1439d2842308f03504430561fbc.app.workbuddy.link
- 线上校验：index.html 200900 字节与本地一致；kb.json 版本 kb-2026.09.10-66a190c7，4 条内容；新增代码 6 处全部命中
- 项目目录 `/Users/tigerwen/WorkBuddy/2026-09-02-22-53-01/` 纳入版本控制（元数据外置于 `.git-interview-assistant`，因该目录禁止 git 就地写 config）
- 每日自动化「测试工程师面试助手 · 每日复习 + 知识库同步」改为每晚 20:00 执行三段：抓取素材落 `raw/interview/` → 精选 1–2 页单源精读编译进 wiki → 重建 kb.json → 提交两个仓库 → 重新部署
- skill `test-knowledge-wiki` 补入「站点产物联动」与「渲染契约字段速查」两节

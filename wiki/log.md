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

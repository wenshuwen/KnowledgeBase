# interview 块填写规则

`interview` 块是**站点渲染契约**，缺失则页面只在知识库内存在、不上站。规则定义见 `WIKI-SCHEMA.md` 第 8 节。

## 最小示例

```yaml
---
title: 压测时 TPS 上不去如何排查
type: concept
domain: 性能测试
created: 2026-09-10
updated: 2026-09-10
sources: [raw/interview/2026-09-10.md]
tags: [performance-testing, interview, root-cause]
confidence: high
status: active

publish: true
interview:
  cat: performance-testing
  kind: question
  level: 高级
  q: 压测时 TPS 上不去，你会怎么排查？
---

# 压测时 TPS 上不去如何排查

（正文 = 答案与展开）
```

## 字段速查

| 字段 | 必填 | 取值 | 说明 |
|---|---|---|---|
| `publish` | 否 | `true` / `false` | 默认 `true`。`false` 会被构建脚本丢弃，**不会出现在 kb.json 里** |
| `interview.cat` | 是 | 见 8.2 枚举 | 站点一级分类 |
| `interview.kind` | 是 | `question` / `knowledge` / `skill` / `pitfall` | 决定站点用哪种卡片渲染 |
| `interview.level` | 否 | `初级` / `中级` / `高级` | 默认不填则不显示难度标 |
| `interview.q` | 仅 `question` | 一句话题干 | 题干要口语化，模拟面试官提问 |

## cat 枚举

`theory` `api-testing` `performance-testing` `automation-testing` `ai-testing` `ai-agent-testing` `python` `ai-tools` `env-setup` `database-linux` `scenario` `cicd`

## 三条容易犯的错

1. **漏填 `interview.cat` 或 `kind`** → 页面会被构建脚本记进「待修清单」，不上站。不是报错，是静默跳过，所以要养成跑构建看日志的习惯。
2. **`publish: false` 却以为能靠前端隐藏** → 违背第 8.4 条硬性要求。过滤只发生在构建脚本里，前端拿不到未发布内容。
3. **把 `q` 写成正文标题** → `q` 是站点卡片上的题干，正文标题 `# xxx` 是页面自身的标题。两者可以相同，但不要偷懒省略 `q`。

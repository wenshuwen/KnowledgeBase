---
title: 选型：{{A}} vs {{B}}
type: decision
domain: {{领域}}
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
sources: []
tags: [best-practice, tooling]
confidence: medium
status: active

publish: true                        # false 则不进站点构建（过滤只在构建脚本里做）
interview:                           # 整块缺失 = 该页不上站；填写则进面试助手
  cat: {{分类，见 WIKI-SCHEMA 8.2}}
  kind: {{question|knowledge|skill|pitfall}}
  level: {{初级|中级|高级}}
  q: {{仅 kind=question 需要，题干}}
---

# 选型：{{A}} vs {{B}}

## 结论先行
{{一句话给出决策，以及决策的适用前提。例如："在 X 前提下选 A；如果 Y 条件成立则改选 B。"}}

## 背景与约束
{{真实约束：团队规模、已有技术栈、时间、预算、维护能力。没有约束的选型结论没有复用价值。}}

## 对比维度

| 维度 | {{A}} | {{B}} | 权重 |
|---|---|---|---|
| 学习成本 | | | |
| 稳定性 | | | |
| 可维护性 | | | |
| 生态与社区 | | | |
| 与现有栈契合度 | | | |

## 决策依据
{{按权重解释为什么这么选。稳定性与可维护性优先于实现速度。}}

## 事后验证
{{用了一段时间后的真实反馈：选对了吗？哪里和预期不符？}}
> 未验证时可留空，但 lint 会盯这个字段。

## 相关
- [[]]
- [[]]

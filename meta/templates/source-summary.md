---
title: 精读：{{文章/文档标题}}
type: source-summary
domain: {{领域}}
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
sources: [raw/clippings/{{文件名}}.md]
tags: []
confidence: medium
status: active

publish: true                        # false 则不进站点构建（过滤只在构建脚本里做）
interview:                           # 整块缺失 = 该页不上站；填写则进面试助手
  cat: {{分类，见 WIKI-SCHEMA 8.2}}
  kind: {{question|knowledge|skill|pitfall}}
  level: {{初级|中级|高级}}
  q: {{仅 kind=question 需要，题干}}
---

# 精读：{{标题}}

| 项 | 内容 |
|---|---|
| 来源 | {{作者 / 站点}} |
| 原始链接 | {{URL}} |
| 原文位置 | `raw/clippings/{{文件名}}.md` |
| 作者立场 | {{官方文档 / 独立作者 / 厂商软文}} |

## 核心主张
- {{论点 1}}
- {{论点 2}}

## 对我有用的部分
{{只记录能落到你工作上的部分。纯知识科普不必复述。}}

## 我不认同 / 存疑的部分
{{这一节强制填写。全盘接受说明没读进去。涉及事实分歧时降低 confidence 并标 needs-verification。}}

## 与我已有经验的连接
{{这条链接到库里既有页面，是本页融入图谱的关键。}}
- 印证了 [[]]
- 修正了 [[]]

## 相关
- [[]]

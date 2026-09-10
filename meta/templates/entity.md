---
title: {{工具/框架/平台名}}
type: entity
domain: {{领域}}
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
sources: []
tags: [tooling]
confidence: medium
status: active

publish: true                        # false 则不进站点构建（过滤只在构建脚本里做）
interview:                           # 整块缺失 = 该页不上站；填写则进面试助手
  cat: {{分类，见 WIKI-SCHEMA 8.2}}
  kind: {{question|knowledge|skill|pitfall}}
  level: {{初级|中级|高级}}
  q: {{仅 kind=question 需要，题干}}
---

# {{实体名}}

| 项 | 内容 |
|---|---|
| 定位 | {{一句话：它解决什么问题}} |
| 类型 | 工具 / 框架 / 平台 / 库 |
| 官方地址 | {{链接}} |
| 当前使用版本 | {{版本}} |

## 我为什么用它
{{真实理由，不是官网复述。如果是被迫用的，也照实写。}}

## 关键能力
- {{能力 1}}：{{对测试工作的直接意义}}
- {{能力 2}}：{{...}}

## 踩过的坑
- {{坑}} → {{怎么绕过}}

## 上手最小示例
```{{语言}}
{{≤30 行，能跑通的最小片段；完整版放 raw/files/ 并在这里链接}}
```

## 相关
- [[]]
- [[]]

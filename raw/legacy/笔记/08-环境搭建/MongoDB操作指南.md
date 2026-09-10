---
type: note
tags: [数据库] [MongoDB]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# MongoDB 基本操作

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 中间件章-MongoDB 小节

## **2\.1 数据库与集合管理**

> **数据库操作**
> 
> 

- 创建/切换数据库：`use <数据库名>`。注意：如果该数据库下没有任何内容，退出后数据库不会被持久化保存。

- 查看所有数据库：`show dbs` 或 `show databases`（仅显示非空数据库）。

- 删除当前数据库：`db.dropDatabase()`。

---

> **集合操作**
> 
> 

- 创建集合：

    - 隐式创建（推荐）：直接向不存在的集合插入文档，集合会自动创建。例如：`db.users.insertOne({name: "Alice"})`。

    - 显式创建：`db.createCollection("集合名称")`，通常用于创建有特殊选项（如固定大小）的集合。

- 查看当前数据库的所有集合：`show collections`。

- 删除集合：`db.集合名称.drop()`。

## **2\.2 文档增删改查（CRUD）**

### **增 \(Create\) \- 插入文档**

- **插入单条文档**：`db.集合名称.insertOne({字段: 值})`

```JavaScript
db.users.insertOne({ 
    name: "Bob", 
    age: 30, 
    hobbies: ["reading", "hiking"] 
})
```

- **插入多条文档**：`db.集合名称.insertMany([{...}, {...}])`

```JavaScript
db.users.insertMany([ 
    { name: "Charlie", age: 35 }, 
    { name: "David", age: 28 } 
])
```

---

### **查 \(Read\) \- 查询文档**

- **查询所有文档**：`db.集合名称.find()`

- **条件查询**：传入查询条件对象

```JavaScript
*// 查找 age 等于 30 的用户*
db.users.find({ age: 30 })
*// 查找 age 大于 28 的用户（$gt 为大于操作符）*
db.users.find({ age: { $gt: 28 } })
```

- **投影查询（指定返回字段）**：`1` 表示包含，`0` 表示排除

```JavaScript
*// 只返回 name 字段，隐藏默认的 _id 字段*
db.users.find({ age: { $gt: 28 } }, { name: 1, _id: 0 })
```

- **查询单条文档**：`db.集合名称.findOne({条件})`，返回第一个匹配的文档。

- 分页与排序：

    - `sort()`：`1` 为升序，`-1` 为降序。

    - `skip(n)`：跳过前 n 条。

    - `limit(n)`：限制返回 n 条。

```JavaScript
*// 按 age 降序排列，跳过前 10 条，取 10 条（常用于分页）*
db.users.find().sort({ age: -1 }).skip(10).limit(10)
```

- **隐式 AND 查询（最常用）**

当多个条件之间是“并且（AND）”的关系时，直接将多个条件写在同一个对象中即可，MongoDB 默认会将其作为 AND 处理。

```JavaScript
*// 查找年龄大于30，且性别为 "male" 的用户**
**db.users.find({ **
**    age: { $gt: 30 }, **
**    gender: "male" **
**})*
```

- **显式逻辑操作符 \( and, or, $ nor\)**

当需要组合更复杂的逻辑，或者同一个字段需要多个条件时，可以使用逻辑操作符：

```JavaScript
*// 查找年龄大于30，或者性别为 "male" 的用户**
**db.users.find({ **
**    $or: [ **
**        { age: { $gt: 30 } }, **
**        { gender: "male" } **
**    ] **
**})*
```

**$ and（与）**：显式声明“并且”关系（通常用于同一字段有多个限制条件时）。

```JavaScript
*// 查找年龄在 20 到 30 之间，且性别为 "male" 的用户
**db.users.find({ **
**    $and: [ **
**        { age: { $gte: 20 } }, **
**        { age: { $lte: 30 } }, **
**        { gender: "male" } **
**    ] **
**})*
```

- **数组多条件查询**

针对包含数组的字段，MongoDB 提供了专门的操作符

- **$ in：**匹配字段值在指定数组中的文档（相当于 SQL 的 `IN`）。

```JavaScript
*// 查找年龄为 30、35 或 40 的用户**
**db.users.find({ age: { $in: [30, 35, 40] } })*
```

- **$ all：**匹配数组中包含所有指定元素的文档。

```JavaScript
*// 查找标签同时包含 "mongodb" 和 "python" 的文章**
**db.articles.find({ tags: { $all: ["mongodb", "python"] } })*
```

- **$ elemMatch：**当需要数组中的同一个元素同时满足多个条件时使用。

```JavaScript
*// 查找成绩数组中，至少有一个元素是“数学”且“分数大于80”的学生**
**db.scores.find({ **
**    results: { **
**        $elemMatch: { **
**            subject: "math", **
**            score: { $gt: 80 } **
**        } **
**    } **
**})*
```

- **模糊匹配多条件 \( $ regex\)**

如果需要结合模糊搜索（类似 SQL 的 `LIKE`），可以使用 `$regex` 操作符：

```JavaScript
*// 查找姓名以 "张" 开头，且年龄大于 25 的用户（不区分大小写）**
**db.users.find({ **
**    $and: [ **
**        { name: { $regex: /^张/, $options: 'i' } }, **
**        { age: { $gt: 25 } } **
**    ] **
**})*
```

---

### **改 \(Update\) \- 更新文档**

- **更新单条文档**：`db.集合名称.updateOne(过滤条件, 更新操作)`

```JavaScript
*// 将第一个名为 "Bob" 的用户年龄更新为 31*
db.users.updateOne( 
    { name: "Bob" }, 
    { $set: { age: 31 } } 
)
```

- **更新多条文档**：`db.集合名称.updateMany(过滤条件, 更新操作)`

```JavaScript
*// 为所有年龄大于 30 的用户添加一个 tags 字段*
db.users.updateMany( 
    { age: { $gt: 30 } }, 
    { $set: { tags: ["senior"] } } 
)
```

- **替换整个文档**：`db.集合名称.replaceOne(过滤条件, 新文档)`。新文档会完全替换旧文档（除了 `_id` 字段）。

---

### **删 \(Delete\) \- 删除文档**

- **删除单条文档**：`db.集合名称.deleteOne({条件})`

```JavaScript
*// 删除第一个名为 "David" 的用户*
db.users.deleteOne({ name: "David" })
```

- **删除多条文档**：`db.集合名称.deleteMany({条件})`

```JavaScript
*// 删除所有年龄小于 25 的用户*
db.users.deleteMany({ age: { $lt: 25 } })
*// 清空整个集合（删除所有文档）*
db.users.deleteMany({})
```

---

## 相关笔记
- [[08-环境搭建]]
- [[PostgreSQL性能调优]]
- [[ElasticSearch使用指南]]

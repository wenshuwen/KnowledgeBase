---
type: note
tags: [接口测试] [Mock] [工具]
created: 2026-09-05
updated: 2026-09-05
source: Test-测试常用技能经验总结-原文
---

# Mock 接口桩实现（Flask）

> 📌 来源：[[Test-测试经验总结-原文]] ｜ 测试工具章-Mock 小节（Flask 实现接口测试桩）

## **5\.1 完整代码**

```Python
# 以下代码使用 Flask 框架实现了一个功能完善的接口测试桩，支持 5 种动态响应模式：
from flask import Flask, request, jsonify
import json
import random
import time
from datetime import datetime

app = Flask(__name__)

*# ==================== 方式一：基于请求参数动态返回 ====================*

@app.route('/api/user', methods=['GET', 'POST'])
def mock_user_api():
    """根据请求参数动态返回不同用户数据"""
    user_id = request.args.get('id', 'default')
    
    users_db = {
        '001': {'code': 200, 'data': {'id': '001', 'name': '张三', 'age': 25, 'role': 'admin'}},
        '002': {'code': 200, 'data': {'id': '002', 'name': '李四', 'age': 30, 'role': 'user'}},
        '003': {'code': 200, 'data': {'id': '003', 'name': '王五', 'age': 28, 'role': 'user'}},
    }
    
    if user_id in users_db:
        return jsonify(users_db[user_id])
    else:
        return jsonify({'code': 404, 'message': f'用户 {user_id} 不存在'})


*# ==================== 方式二：基于请求体内容动态返回 ====================*

@app.route('/api/order', methods=['POST'])
def mock_order_api():
    """根据请求体内容动态返回不同订单响应"""
    req_data = request.get_json()
    
    if not req_data:
        return jsonify({'code': 400, 'message': '请求体为空'}), 400
    
    order_type = req_data.get('type', 'normal')
    
    if order_type == 'normal':
        response = {
            'code': 200,
            'data': {
                'order_id': f'ORD{random.randint(10000, 99999)}',
                'status': 'created',
                'amount': req_data.get('amount', 0),
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    elif order_type == 'vip':
        response = {
            'code': 200,
            'data': {
                'order_id': f'VIP{random.randint(10000, 99999)}',
                'status': 'created',
                'amount': req_data.get('amount', 0) * 0.8,  *# VIP 8折*
                'discount': 0.2,
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    else:
        response = {'code': 400, 'message': f'不支持的订单类型: {order_type}'}
    
    return jsonify(response)


*# ==================== 方式三：模拟异常场景 ====================*

@app.route('/api/payment', methods=['POST'])
def mock_payment_api():
    """模拟支付接口 - 支持多种异常场景"""
    req_data = request.get_json() or {}
    scenario = req_data.get('scenario', 'success')
    
    if scenario == 'success':
        return jsonify({
            'code': 200,
            'data': {
                'transaction_id': f'TXN{random.randint(100000, 999999)}',
                'status': 'success',
                'message': '支付成功'
            }
        })
    elif scenario == 'timeout':
        time.sleep(5)  *# 模拟超时*
        return jsonify({'code': 504, 'message': '请求超时'})
    elif scenario == 'error':
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500
    elif scenario == 'insufficient_balance':
        return jsonify({
            'code': 4002,
            'message': '余额不足',
            'data': {'available_balance': 50.00}
        })
    else:
        return jsonify({'code': 400, 'message': f'未知场景: {scenario}'})


*# ==================== 方式四：通用动态响应接口 ====================*

@app.route('/api/mock', methods=['GET', 'POST', 'PUT', 'DELETE'])
def universal_mock():
    """
    通用 Mock 接口 - 完全由请求参数决定响应内容
    
    请求示例:
    {
        "status_code": 200,
        "delay": 0,
        "response": {"key": "value"}
    }
    """
    req_data = request.get_json() or {}
    
    status_code = req_data.get('status_code', 200)
    delay = req_data.get('delay', 0)
    response_body = req_data.get('response', {'message': 'mock success'})
    
    if delay > 0:
        time.sleep(delay)
    
    return jsonify(response_body), status_code


*# ==================== 方式五：基于规则引擎的动态响应 ====================*

MOCK_RULES = {
    '/api/weather': {
        'conditions': [
            {'match': {'city': '北京'}, 'response': {'code': 200, 'data': {'temp': 25, 'weather': '晴'}}},
            {'match': {'city': '上海'}, 'response': {'code': 200, 'data': {'temp': 28, 'weather': '多云'}}},
            {'match': {'city': '深圳'}, 'response': {'code': 200, 'data': {'temp': 32, 'weather': '雷阵雨'}}},
        ],
        'default': {'code': 200, 'data': {'temp': 20, 'weather': '未知'}}
    }
}

@app.route('/api/weather', methods=['GET', 'POST'])
def mock_weather():
    """基于规则引擎的天气接口 Mock"""
    if request.method == 'GET':
        city = request.args.get('city', '')
    else:
        req_data = request.get_json() or {}
        city = req_data.get('city', '')
    
    rules = MOCK_RULES.get('/api/weather')
    for rule in rules['conditions']:
        if city in rule['match'].values():
            return jsonify(rule['response'])
    
    return jsonify(rules['default'])


if __name__ == '__main__':
    print("=" * 50)
    print("接口测试桩服务启动中...")
    print("=" * 50)
    print("\n可用接口列表:")
    print("  GET/POST /api/user?id=xxx     - 用户查询接口")
    print("  POST     /api/order           - 订单创建接口")
    print("  POST     /api/payment         - 支付接口（支持异常模拟）")
    print("  ALL      /api/mock            - 通用动态Mock接口")
    print("  GET/POST /api/weather?city=xx - 天气查询接口")
    print("\n服务地址: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## **5\.2 启动方式**

```Shell
pip install flask
python mock_server.py
```

---

## **5\.3 测试调用**

### **1️⃣ 基于请求参数动态返回**

```Shell
*# 查询存在的用户*
curl http://localhost:5000/api/user?id=001
*# 返回: {"code": 200, "data": {"id": "001", "name": "张三", "age": 25, "role": "admin"}}*

*# 查询不存在的用户*
curl http://localhost:5000/api/user?id=999
*# 返回: {"code": 404, "message": "用户 999 不存在"}*
```

### **2️⃣ 基于请求体内容动态返回**

```Shell
*# 普通订单*
curl -X POST http://localhost:5000/api/order \
  -H "Content-Type: application/json" \
  -d '{"type": "normal", "amount": 100}'
*# 返回: {"code": 200, "data": {"order_id": "ORD12345", "amount": 100, ...}}*

*# VIP 订单（自动打8折）*
curl -X POST http://localhost:5000/api/order \
  -H "Content-Type: application/json" \
  -d '{"type": "vip", "amount": 100}'
*# 返回: {"code": 200, "data": {"order_id": "VIP67890", "amount": 80.0, "discount": 0.2, ...}}*
```

### **3️⃣ 模拟异常场景**

```Shell
*# 支付成功*
curl -X POST http://localhost:5000/api/payment \
  -H "Content-Type: application/json" \
  -d '{"scenario": "success"}'

*# 模拟超时（延迟5秒）*
curl -X POST http://localhost:5000/api/payment \
  -H "Content-Type: application/json" \
  -d '{"scenario": "timeout"}'

*# 模拟余额不足*
curl -X POST http://localhost:5000/api/payment \
  -H "Content-Type: application/json" \
  -d '{"scenario": "insufficient_balance"}'
```

### **4️⃣ 通用动态 Mock（最灵活）**

```Shell
*# 自定义任意响应*
curl -X POST http://localhost:5000/api/mock \
  -H "Content-Type: application/json" \
  -d '{
    "status_code": 200,
    "delay": 1,
    "response": {"custom_key": "custom_value", "list": [1, 2, 3]}
  }'
```

### **5️⃣ 规则引擎匹配**

```Shell
curl http://localhost:5000/api/weather?city=深圳
*# 返回: {"code": 200, "data": {"temp": 32, "weather": "雷阵雨"}}*
```

---

## **5\.4 核心设计思路**

|模式|适用场景|动态依据|
|---|---|---|
|请求参数匹配|根据 URL 参数返回不同数据|request\.args|
|请求体解析|根据 POST 内容返回不同响应|request\.get\_json\(\)|
|场景模拟|测试异常处理逻辑（超时/错误/余额不足）|scenario 字段|
|通用 Mock|快速构造任意响应，无需改代码|请求体中指定 status\_code / delay / response|
|规则引擎|多条件匹配，适合复杂业务场景|预定义规则表|

> 💡 进阶建议：如果需要更强大的功能（如录制回放、契约测试），可以考虑使用 WireMock、Mountebank 或 mitmproxy 等专业 Mock 工具。对于简单的接口测试桩场景，上述 Flask 方案已经足够灵活实用。
> 
> 

---

## 相关笔记
- [[03-工具与安装]]
- [[SoapUI使用指南]]
- [[Postman接口测试]]

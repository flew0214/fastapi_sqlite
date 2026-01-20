# FastAPI 聊天室后端

基于 FastAPI + SQLite 的实时聊天室后端 API。

## 🤖 AI 技术

本项目使用 **OpenCode** AI 助手辅助开发，通过自然语言描述需求，AI 自动生成代码。

### 开发 Prompt 示例

```
创建一个 fastapi 后端。数据库是 sqlite。功能是聊天室。
用户可以登录，然后可以发送消息，接受消息。参数可以设定 Limit.默认 5 条。
删除消息。并且 python 使用 venv 来实现。
```

## 🛠 技术框架

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.128.0 |
| ASGI 服务器 | Uvicorn 0.40.0 |
| 数据库 | SQLite + SQLAlchemy 2.0.45 |
| 数据验证 | Pydantic 2.12.5 |
| 密码加密 | Passlib 1.7.4 + bcrypt 4.0.1 |
| JWT 认证 | Python-JOSE 3.5.0 |
| Python 版本 | 3.12+ |

## 📐 实现原理

### 架构设计

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│   SQLite    │
│  (requests) │◀────│  (Uvicorn)  │◀────│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 核心模块

#### 1. 数据库模型 (`models.py`)
- **User 模型**: 存储用户信息（ID、用户名、密码哈希、创建时间）
- **Message 模型**: 存储聊天消息（ID、内容、用户ID、创建时间）

#### 2. Pydantic 模式 (`schemas.py`)
- 数据验证和序列化
- 请求/响应模型定义

#### 3. 认证机制 (`main.py`)
- **JWT Token 认证**: 使用 `python-jose` 生成和验证 JWT
- **密码加密**: 使用 `bcrypt` 进行密码哈希
- **OAuth2PasswordBearer**: FastAPI 标准认证方式

#### 4. API 端点
- 依赖注入获取数据库会话
- 依赖注入获取当前用户
- RESTful 风格的 CRUD 操作

### 数据库关系

```
users (1) ──────▶ (N) messages
一个用户可以有 N 条消息
一条消息属于一个用户
```

## 📚 接口文档

### 基础信息

- **Base URL**: `http://localhost:8000`
- **认证方式**: Bearer Token (JWT)
- **Content-Type**: application/json

---

### 1. 用户注册

**POST** `/register`

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

**成功响应 (200):**
```json
{
  "id": 1,
  "username": "testuser",
  "created_at": "2026-01-20T10:00:00"
}
```

**错误响应 (400):**
```json
{
  "detail": "Username already registered"
}
```

**示例:**
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

---

### 2. 用户登录

**POST** `/token`

**表单数据:**
- `username`: 用户名
- `password`: 密码

**成功响应 (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**示例:**
```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass"
```

---

### 3. 获取当前用户信息

**GET** `/users/me`

**请求头:**
- `Authorization`: `Bearer <token>`

**成功响应 (200):**
```json
{
  "id": 1,
  "username": "testuser",
  "created_at": "2026-01-20T10:00:00"
}
```

**示例:**
```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer <your-token>"
```

---

### 4. 发送消息

**POST** `/messages/`

**请求头:**
- `Authorization`: `Bearer <token>`

**请求体:**
```json
{
  "content": "Hello, world!"
}
```

**成功响应 (200):**
```json
{
  "id": 1,
  "content": "Hello, world!",
  "user_id": 1,
  "username": "testuser",
  "created_at": "2026-01-20T10:00:00"
}
```

**示例:**
```bash
curl -X POST http://localhost:8000/messages/ \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, world!"}'
```

---

### 5. 获取消息列表

**GET** `/messages/`

**请求头:**
- `Authorization`: `Bearer <token>`

**查询参数:**
- `limit` (可选): 返回消息数量，默认 5，最大 100

**成功响应 (200):**
```json
[
  {
    "id": 1,
    "content": "Hello, world!",
    "user_id": 1,
    "username": "testuser",
    "created_at": "2026-01-20T10:00:00"
  },
  {
    "id": 2,
    "content": "Welcome to chat!",
    "user_id": 2,
    "username": "user2",
    "created_at": "2026-01-20T10:01:00"
  }
]
```

**示例:**
```bash
# 获取最新 5 条消息（默认）
curl -X GET http://localhost:8000/messages/ \
  -H "Authorization: Bearer <your-token>"

# 获取最新 10 条消息
curl -X GET "http://localhost:8000/messages/?limit=10" \
  -H "Authorization: Bearer <your-token>"
```

---

### 6. 删除消息

**DELETE** `/messages/{message_id}`

**请求头:**
- `Authorization`: `Bearer <token>`

**路径参数:**
- `message_id`: 消息 ID

**成功响应 (200):**
```json
{
  "detail": "Message deleted"
}
```

**错误响应:**
- 404: "Message not found"
- 403: "Not authorized to delete this message"

**示例:**
```bash
curl -X DELETE http://localhost:8000/messages/1 \
  -H "Authorization: Bearer <your-token>"
```

### 7. WebSocket 连接

**WS** `/ws/{token}`

实时 WebSocket 连接，用于消息推送和在线状态同步。

**连接成功后会收到：**

1. **用户列表更新** - `USER_LIST:user1,user2,user3`
2. **新消息推送** - `NEW_MESSAGE:username:content:time`

**发送消息格式：**

```
MESSAGE:Hello World!
```

**示例：**

```javascript
// 连接 WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/{token}');

// 监听消息
ws.onmessage = (event) => {
    const data = event.data;
    
    if (data.startsWith('USER_LIST:')) {
        // 更新在线用户列表
        const users = data.replace('USER_LIST:', '').split(',');
    } else if (data.startsWith('NEW_MESSAGE:')) {
        // 收到新消息
        const parts = data.split(':');
        const username = parts[1];
        const content = parts[2];
        const time = parts[3];
    }
};

// 发送消息
ws.send('MESSAGE:Hello!');
```

---

### 8. 获取在线用户列表

**GET** `/users/online`

**成功响应 (200):**

```json
{
  "online_users": ["user1", "user2"]
}
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn main:app --reload
```

服务器将在 `http://localhost:8000` 启动。

### 3. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 项目结构

```
fastapi_sqlite/
├── venv/                  # Python 虚拟环境
├── models.py              # SQLAlchemy 数据库模型
├── schemas.py             # Pydantic 模式定义
├── main.py                # FastAPI 应用主文件
├── static/
│   └── index.html         # 聊天室前端界面
├── start.py               # 启动脚本
├── requirements.txt       # 项目依赖
├── README.md              # 项目文档
└── database_explorer.ipynb # 数据库探索工具
```

## 🎨 前端界面

### 功能特性

| 功能 | 描述 |
|------|------|
| 🔐 用户登录/注册 | 安全的用户认证系统 |
| 💬 实时消息 | WebSocket 实时消息推送 |
| 👥 在线成员 | 实时显示在线用户列表 |
| 🟢 在线状态 | 绿色圆点显示在线状态 |
| 📱 响应式设计 | 支持移动端适配 |
| 🎀 消息气泡 | 精美聊天气泡样式 |
| 🔔 通知提醒 | 登录/消息通知 |

### 启动方式

```bash
# 启动服务（前端自动挂载）
uvicorn main:app --reload

# 访问聊天室
http://localhost:8000
```

### 界面预览

```
┌─────────────────────────────────────────────────┐
│  💬 聊天室                           👤 用户名 │
├──────────────┬──────────────────────────────────┤
│ 👥 成员列表 3 │  💬 消息区域                      │
│              │                                  │
│ 👤 user1 🟢  │  👤 user1    10:30               │
│ 👤 user2 🟢  │  │ Hello!                        │
│ 👤 user3 🔴  │                                  │
│              │  👤 我      10:31               │
│              │  │ Hi there!                    │
│              │                                  │
│              │  ─────────────────────────────  │
│              │  [ 输入消息...              ➤ ] │
└──────────────┴──────────────────────────────────┘
```

## 🔒 安全说明

- 生产环境请修改 `SECRET_KEY` 为更复杂的值
- 密码使用 bcrypt 算法加密存储
- 使用 JWT 进行身份验证，设置过期时间 30 分钟

## 📄 许可证

MIT License
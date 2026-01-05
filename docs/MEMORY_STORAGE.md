# Memory Storage System

## Overview

LightAgent的内存存储系统提供了完整的agent事件记录、查询和分析功能。采用模块化设计，支持多种存储后端。

## 核心特性

- ✅ **模块化设计** - 可插拔的存储后端
- ✅ **自动记录** - 自动记录所有agent事件
- ✅ **多种后端** - 内存、文件、SQLite、MySQL、PostgreSQL
- ✅ **灵活查询** - 按类型、会话、时间范围过滤
- ✅ **全文搜索** - 在事件数据中搜索
- ✅ **统计分析** - 获取详细的统计信息
- ✅ **会话隔离** - 支持多会话管理
- ✅ **文件格式** - 支持JSONL和JSON格式

## 事件类型

### 自动记录的事件

| 事件类型 | 说明 | 记录时机 |
|---------|------|----------|
| `USER_MESSAGE` | 用户输入 | 用户发送消息时 |
| `MODEL_RESPONSE` | 模型响应 | 模型返回结果时 |
| `TOOL_CALL_START` | 工具调用开始 | 调用工具前 |
| `TOOL_CALL_SUCCESS` | 工具调用成功 | 工具执行成功 |
| `TOOL_CALL_ERROR` | 工具调用失败 | 工具执行失败 |
| `AGENT_INIT` | Agent初始化 | Agent初始化完成 |
| `AGENT_ERROR` | Agent错误 | 发生错误时 |
| `MIDDLEWARE_PRE` | 中间件预处理 | 中间件处理前 |
| `MIDDLEWARE_POST` | 中间件后处理 | 中间件处理后 |

### 自定义事件

```python
await agent._record_event(
    EventType.CUSTOM,
    {"action": "user_login", "user_id": "123"},
    metadata={"source": "web"}
)
```

## 存储后端

### 1. InMemoryMemoryStore

内存存储，适合测试和短期应用。

**优点：**
- 无需依赖
- 快速访问
- 易于测试

**缺点：**
- 数据不持久化
- 重启后丢失
- 内存占用大

```python
from lightagent import InMemoryMemoryStore

agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    memory_store=InMemoryMemoryStore()
)
```

### 2. FileMemoryStore

文件存储，适合日志记录和审计。

**优点：**
- 无需额外依赖
- 人类可读（JSON格式）
- 易于备份和迁移
- 支持外部工具（grep、jq等）
- 文件轮转支持

**配置选项：**
```python
from lightagent import FileMemoryStore

agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    memory_store=FileMemoryStore(config={
        "base_path": "./agent_memory",    # 日志目录
        "format": "jsonl",                 # "jsonl" 或 "json"
        "file_per_session": True,         # 每会话一个文件
        "rotate_size": 10 * 1024 * 1024    # 文件轮转大小（字节）
    })
)
```

**格式说明：**

**JSONL格式**（推荐）
```json
{"event_id":"evt_123","agent_name":"assistant","event_type":"user_message",...}
{"event_id":"evt_124","agent_name":"assistant","event_type":"model_response",...}
```
- 一行一个JSON
- 追加写入，性能高
- 适合大文件

**JSON格式**
```json
[
  {"event_id":"evt_123",...},
  {"event_id":"evt_124",...}
]
```
- JSON数组
- 人类可读性好
- 适合小文件

**文件组织：**

Per-Session模式（`file_per_session=True`）：
```
agent_memory/
├── session_abc123.jsonl
├── session_def456.jsonl
└── session_ghi789.jsonl
```

Single File模式（`file_per_session=False`）：
```
agent_memory/
└── events.jsonl
```

**文件轮转：**
- 自动检测文件大小
- 超过限制时归档旧文件
- 归档文件添加时间戳

### 3. SQLiteMemoryStore

SQLite数据库，嵌入式持久化存储。

**优点：**
- 无需服务器
- 数据持久化
- 适合单机应用
- SQL查询能力

**依赖：**
```bash
pip install aiosqlite
```

```python
from lightagent import SQLiteMemoryStore

agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    memory_store=SQLiteMemoryStore(config={
        "db_path": "agent_memory.db"  # 或 ":memory:" 用于内存数据库
    })
)
```

### 4. MySQLMemoryStore

MySQL服务器存储，适合生产环境高并发场景。

**优点：**
- 高性能
- 支持分布式
- 成熟的生态系统
- 适合大规模应用

**依赖：**
```bash
pip install aiomysql
```

```python
from lightagent import MySQLMemoryStore

agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    memory_store=MySQLMemoryStore(config={
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "password",
        "database": "agent_memory"
    })
)
```

### 5. PostgreSQLMemoryStore

PostgreSQL存储，支持高级查询和JSONB。

**优点：**
- JSONB支持
- 全文搜索
- 高级索引
- 强大的查询能力

**依赖：**
```bash
pip install asyncpg
```

```python
from lightagent import PostgreSQLMemoryStore

agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    memory_store=PostgreSQLMemoryStore(config={
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "password",
        "database": "agent_memory"
    })
)
```

## 存储后端对比

| 特性 | InMemory | File | SQLite | MySQL | PostgreSQL |
|------|----------|------|--------|-------|------------|
| 持久化 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 依赖 | 无 | 无 | aiosqlite | aiomysql | asyncpg |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可读性 | ❌ | ✅ | ⚠️ | ❌ | ❌ |
| 服务器 | 无 | 无 | 无 | 需要 | 需要 |
| 适用场景 | 测试 | 日志/审计 | 单机生产 | 分布式生产 | 高级查询 |

## 使用方法

## 使用方法

### 基本使用

```python
from lightagent import Agent, MockAdapter, ModelConfig, SQLiteMemoryStore

# 创建带记忆的agent
agent = Agent.create(
    name="assistant",
    model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
    memory_store=SQLiteMemoryStore()
)

# 初始化（会记录AGENT_INIT事件）
await agent.initialize()

# 运行（自动记录所有事件）
await agent.run("Hello!")
```

### 查询记忆

```python
# 获取所有事件
events = await agent.get_memory(limit=100)

# 过滤特定类型
tool_events = await agent.get_memory(event_type=EventType.TOOL_CALL_SUCCESS)

# 过滤特定会话
session_events = await agent.get_memory(session_id="session-123")

# 时间范围查询
from datetime import datetime, timedelta

recent_events = await agent.memory_store.retrieve(
    start_time=datetime.now() - timedelta(hours=1),
    limit=50
)
```

### 搜索记忆

```python
# 搜索包含特定内容的事件
results = await agent.search_memory("calculator", limit=10)

for event in results:
    print(f"{event.event_type}: {event.data}")
```

### 统计分析

```python
# 获取统计信息
stats = await agent.get_memory_stats()

print(f"总事件数: {stats['total_events']}")
print(f"按类型分布: {stats['by_type']}")
print(f"首个事件: {stats.get('first_event')}")
print(f"最后事件: {stats.get('last_event')}")
```

### 清空记忆

```python
# 清空当前会话
await agent.clear_memory(session_id=agent.context.session_id)

# 清空所有会话
await agent.clear_memory()
```

## 记录的数据

### 事件结构

每个事件包含：

```python
AgentEvent(
    event_id="evt_1234567890.123",
    agent_name="assistant",
    session_id="uuid-string",
    event_type=EventType.USER_MESSAGE,
    timestamp=datetime(2024, 1, 1, 12, 0, 0),
    data={
        "message": "Hello",
        "message_length": 5
    },
    metadata={}
)
```

### 各事件的data字段

**USER_MESSAGE**
```python
{
    "message": "用户消息",
    "message_length": 100
}
```

**MODEL_RESPONSE**
```python
{
    "response": "模型响应",
    "tool_calls_count": 2,
    "iterations": 1,
    "success": True
}
```

**TOOL_CALL_START**
```python
{
    "tool_name": "calculator",
    "arguments": {"expression": "2+2"}
}
```

**TOOL_CALL_SUCCESS**
```python
{
    "tool_name": "calculator",
    "result": "4"
}
```

**TOOL_CALL_ERROR**
```python
{
    "tool_name": "calculator",
    "error": "错误信息",
    "error_type": "ValueError"
}
```

## 禁用记忆存储

```python
agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    enable_memory=False  # 禁用记忆
)
```

## 最佳实践

### 1. 选择合适的存储后端

**开发/测试：**
```python
memory_store=InMemoryMemoryStore()
```

**单机生产：**
```python
memory_store=SQLiteMemoryStore(config={"db_path": "memory.db"})
```

**分布式/高并发：**
```python
memory_store=MySQLMemoryStore(config={...})
# 或
memory_store=PostgreSQLMemoryStore(config={...})
```

### 2. 定期清理

```python
# 定期清理旧记忆
import asyncio

async def cleanup_old_memory():
    while True:
        await asyncio.sleep(3600)  # 每小时
        # 清理7天前的数据
        cutoff = datetime.now() - timedelta(days=7)
        await agent.memory_store.clear(end_time=cutoff)
```

### 3. 使用会话隔离

```python
# 每个用户一个会话
user_sessions = {}

async def handle_user(user_id: str, message: str):
    if user_id not in user_sessions:
        # 创建新会话
        agent.reset_context()
        user_sessions[user_id] = agent.context.session_id

    await agent.run(message)
```

### 4. 监控和分析

```python
# 定期获取统计
async def monitor_agent():
    stats = await agent.get_memory_stats()

    # 检查错误率
    total = stats['total_events']
    errors = stats['by_type'].get('AGENT_ERROR', 0)

    if errors / total > 0.1:  # 10%错误率
        print(f"警告: 高错误率 {errors/total*100:.1f}%")
```

### 5. 性能优化

```python
# 使用批量操作
async def batch_record_events(events: List[AgentEvent]):
    # 对于某些后端，可以批量插入
    for event in events:
        await agent.memory_store.store(event)

# 异步记录（不阻塞主流程）
async def record_event_async(event: AgentEvent):
    asyncio.create_task(agent.memory_store.store(event))
```

## 实现自定义存储后端

```python
from lightagent import BaseMemoryStore, AgentEvent

class CustomMemoryStore(BaseMemoryStore):
    async def initialize(self):
        # 初始化你的存储
        pass

    async def store(self, event: AgentEvent) -> bool:
        # 存储事件
        pass

    async def retrieve(self, **kwargs) -> List[AgentEvent]:
        # 检索事件
        pass

    async def clear(self, **kwargs):
        # 清空事件
        pass

    async def get_stats(self, **kwargs) -> Dict:
        # 获取统计
        pass

    async def search(self, query: str, **kwargs) -> List[AgentEvent]:
        # 搜索事件
        pass

    async def close(self):
        # 清理资源
        pass
```

## 数据迁移

### 从内存迁移到SQLite

```python
# 1. 创建两个store
memory_store = InMemoryMemoryStore()
sqlite_store = SQLiteMemoryStore(config={"db_path": "memory.db"})

# 2. 初始化
await memory_store.initialize()
await sqlite_store.initialize()

# 3. 迁移数据
events = await memory_store.retrieve()
for event in events:
    await sqlite_store.store(event)
```

## 故障排除

### 问题1: SQLite文件被锁定

```python
# 使用WAL模式
memory_store = SQLiteMemoryStore(config={
    "db_path": "memory.db",
    "wal_mode": True
})
```

### 问题2: 内存占用过大

```python
# 限制事件数量
events = await agent.get_memory(limit=1000)

# 定期清理
await agent.clear_memory(session_id=old_session)
```

### 问题3: 性能问题

```python
# 使用索引（SQLite会自动创建）
# 对于大数据量，考虑使用MySQL或PostgreSQL

# 异步记录不阻塞主流程
async def record_non_blocking(event):
    await asyncio.create_task(agent.memory_store.store(event))
```

## 示例代码

完整示例：
- `examples/memory_storage.py` - 记忆存储完整示例

## 总结

LightAgent的记忆存储系统提供了：

- ✅ 模块化的存储后端
- ✅ 自动事件记录
- ✅ 灵活的查询和搜索
- ✅ 会话隔离
- ✅ 统计分析
- ✅ 易于扩展

使用记忆存储可以：
- 调试agent行为
- 分析性能
- 审计操作
- 追踪对话
- 收集使用数据

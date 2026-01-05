# Agent Creation Guide

## 两种创建方式

LightAgent提供了两种创建Agent的方式，各有优势：

### 方式1: 传统方式（使用AgentConfig）

```python
from lightagent import Agent, AgentConfig, MockAdapter, ModelConfig

# 创建配置
config = AgentConfig(
    name="assistant",
    system_prompt="You are a helpful assistant",
    max_iterations=10
)

# 创建Agent
agent = Agent(
    config=config,
    model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
)

agent.add_tool(tool)
await agent.initialize()
```

### 方式2: 简化方式（使用Agent.create()）

```python
from lightagent import Agent, MockAdapter, ModelConfig

# 一步到位
agent = Agent.create(
    name="assistant",
    model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
    system_prompt="You are a helpful assistant",
    tools=[tool],
    max_iterations=10
)

await agent.initialize()
```

## 对比

| 特性 | AgentConfig | Agent.create() |
|------|-------------|----------------|
| 代码行数 | ~10行 | ~5行 |
| 配置复用 | ✅ 支持 | ❌ 不支持 |
| 文件加载 | ✅ 方便 | ⚠️ 需手动解析 |
| 配置验证 | ✅ 创建时验证 | ✅ 内部验证 |
| 序列化 | ✅ 直接序列化 | ✅ 可访问config |
| 简洁性 | ⚠️ 较繁琐 | ✅ 更简洁 |
| 快速原型 | ⚠️ 较慢 | ✅ 快速 |

## 使用场景

### 使用AgentConfig的场景

#### 1. 从文件加载配置

```python
import json

# config.json
config_json = '''
{
    "name": "assistant",
    "system_prompt": "You are helpful",
    "max_iterations": 10
}
'''

# 加载并创建
config = AgentConfig.model_validate_json(config_json)
agent = Agent(config=config, model_adapter=adapter)
```

#### 2. 配置共享

```python
# 多个Agent共享配置
base_config = AgentConfig(
    name="base_agent",
    system_prompt="You are helpful",
    max_iterations=5
)

agent1 = Agent(config=base_config, model_adapter=adapter1)
agent2 = Agent(config=base_config, model_adapter=adapter2)
```

#### 3. 配置验证

```python
from pydantic import ValidationError

try:
    config = AgentConfig(
        name="agent",
        max_iterations="invalid"  # 类型错误
    )
except ValidationError as e:
    print(f"配置错误: {e}")
```

#### 4. 配置持久化

```python
# 保存配置
config_dict = agent.config.model_dump()
with open("agent_config.json", "w") as f:
    json.dump(config_dict, f)

# 加载配置
with open("agent_config.json", "r") as f:
    config = AgentConfig.model_validate_json(f.read())
```

### 使用Agent.create()的场景

#### 1. 快速原型

```python
# 快速测试想法
agent = Agent.create(
    name="test",
    model_adapter=MockAdapter(...),
    system_prompt="Test prompt"
)
await agent.run("Hello")
```

#### 2. 简单脚本

```python
import asyncio
from lightagent import Agent, MockAdapter, ModelConfig

async def main():
    agent = Agent.create(
        name="bot",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        system_prompt="You are helpful"
    )
    await agent.initialize()
    result = await agent.run("Hello")
    print(result['response'])

asyncio.run(main())
```

#### 3. 所有配置已知

```python
# 一次性配置所有参数
agent = Agent.create(
    name="assistant",
    model_adapter=adapter,
    system_prompt="You are helpful",
    tools=[tool1, tool2, tool3],
    middlewares=middleware_manager,
    max_iterations=10,
    auto_tool_prompt=True
)
```

#### 4. 不需要配置复用

```python
# 一次性使用的Agent
agent = Agent.create(
    name="temp",
    model_adapter=adapter,
    system_prompt="..."
)
```

## AgentConfig的优势

### 1. 关注点分离

```python
# 配置层
config = AgentConfig(
    name="agent",
    system_prompt="...",
    max_iterations=10
)

# 运行层
agent = Agent(config=config, model_adapter=adapter)
```

### 2. 配置管理

```python
# 集中管理配置
configs = {
    "basic": AgentConfig(name="basic", ...),
    "advanced": AgentConfig(name="advanced", ...),
    "expert": AgentConfig(name="expert", ...)
}

# 根据需要选择
agent = Agent(
    config=configs["basic"],
    model_adapter=adapter
)
```

### 3. 类型安全

```python
from pydantic import BaseModel, Field

class StrictAgentConfig(AgentConfig):
    min_iterations: int = Field(ge=1, le=100)

# 自动验证
config = StrictAgentConfig(min_iterations=150)  # 报错！超出范围
```

## Agent.create()的优势

### 1. 更少的样板代码

```python
# 传统方式：5-6行
config = AgentConfig(name="agent", system_prompt="...")
agent = Agent(config=config, model_adapter=adapter)
agent.add_tool(tool)
await agent.initialize()

# 简化方式：2-3行
agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    system_prompt="...",
    tools=[tool]
)
await agent.initialize()
```

### 2. 更直观

```python
# 所有参数一目了然
agent = Agent.create(
    name="agent",              # 名称
    model_adapter=adapter,     # 模型
    system_prompt="...",       # 提示词
    tools=[tool1, tool2],      # 工具
    max_iterations=10          # 其他配置
)
```

### 3. 链式调用友好

```python
agent = (Agent.create(
    name="agent",
    model_adapter=adapter
).add_tool(tool1).add_tool(tool2))
```

## 实际建议

### 开发阶段

```python
# 使用Agent.create()快速迭代
agent = Agent.create(
    name="test",
    model_adapter=adapter,
    system_prompt="Testing..."
)
```

### 生产环境

```python
# 使用AgentConfig管理配置
config = load_config_from_file("production.json")
agent = Agent(config=config, model_adapter=adapter)
```

### 团队协作

```python
# 配置文件版本控制
# config/agent.json - 团队共享
# 本地加载
config = AgentConfig.model_validate_json(file_content)
```

### 学习和教学

```python
# Agent.create()更易理解
agent = Agent.create(
    name="助手",
    model_adapter=adapter,
    system_prompt="你是一个助手"
)
```

## 内部实现

```python
class Agent:
    @classmethod
    def create(cls, name, model_adapter, **kwargs):
        # 内部还是创建AgentConfig
        config = AgentConfig(name=name, **kwargs)
        return cls(config=config, model_adapter=model_adapter)
```

两种方式**完全等价**，只是语法糖不同！

## 迁移指南

### 从AgentConfig迁移到Agent.create()

**之前：**
```python
config = AgentConfig(
    name="agent",
    system_prompt="...",
    max_iterations=10
)
agent = Agent(config=config, model_adapter=adapter)
agent.add_tool(tool)
```

**之后：**
```python
agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    system_prompt="...",
    max_iterations=10,
    tools=[tool]
)
```

### 从Agent.create()迁移到AgentConfig

**之前：**
```python
agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    system_prompt="..."
)
```

**之后：**
```python
config = AgentConfig(name="agent", system_prompt="...")
agent = Agent(config=config, model_adapter=adapter)
```

## 总结

### 何时使用AgentConfig
- ✅ 需要配置文件管理
- ✅ 配置复用和共享
- ✅ 生产环境
- ✅ 团队协作
- ✅ 需要配置验证

### 何时使用Agent.create()
- ✅ 快速原型开发
- ✅ 简单脚本
- ✅ 学习测试
- ✅ 一次性使用
- ✅ 代码简洁优先

### 记住
- 两者功能完全相同
- Agent.create()内部创建AgentConfig
- 选择取决于使用场景
- 可以随时相互转换

## 示例代码

完整示例：
- `examples/simplified_usage.py` - 两种方式对比
- `examples/basic_agent.py` - AgentConfig示例
- `examples/simple_demo.py` - Agent.create()示例

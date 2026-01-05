# AgentConfig 移除 - 迁移指南

## 重要变更

AgentConfig已被移除，所有配置字段现在直接在Agent类中。

### 之前（使用AgentConfig）

```python
from lightagent import Agent, AgentConfig, MockAdapter, ModelConfig

# 创建配置
config = AgentConfig(
    name="assistant",
    system_prompt="You are helpful",
    max_iterations=10
)

# 创建Agent
agent = Agent(config=config, model_adapter=MockAdapter(...))
```

### 现在（使用Agent.create）

```python
from lightagent import Agent, MockAdapter, ModelConfig

# 直接创建Agent
agent = Agent.create(
    name="assistant",
    model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
    system_prompt="You are helpful",
    max_iterations=10
)
```

## 变更详情

### Agent字段变更

所有之前的`AgentConfig`字段现在是`Agent`的直接字段：

| 之前 | 现在 |
|------|------|
| `agent.config.name` | `agent.name` |
| `agent.config.system_prompt` | `agent.system_prompt` |
| `agent.config.max_iterations` | `agent.max_iterations` |
| `agent.config.auto_tool_prompt` | `agent.auto_tool_prompt` |
| `agent.config.model_provider` | `agent.model_provider` |
| `agent.config.enable_middleware` | `agent.enable_middleware` |

### 创建Agent的方式

#### 方式1: 使用Agent.create()（推荐）

```python
agent = Agent.create(
    name="assistant",
    model_adapter=adapter,
    system_prompt="You are helpful",
    tools=[tool1, tool2],
    max_iterations=10
)
```

#### 方式2: 直接实例化

```python
agent = Agent(
    name="assistant",
    model_adapter=adapter,
    system_prompt="You are helpful",
    max_iterations=10
)
agent.add_tool(tool1)
agent.add_tool(tool2)
```

## 示例迁移

### 示例1: 基本Agent

**之前：**
```python
config = AgentConfig(
    name="bot",
    system_prompt="You are a bot"
)
agent = Agent(config=config, model_adapter=adapter)
```

**现在：**
```python
agent = Agent.create(
    name="bot",
    model_adapter=adapter,
    system_prompt="You are a bot"
)
```

### 示例2: 带工具的Agent

**之前：**
```python
config = AgentConfig(name="bot", system_prompt="...")
agent = Agent(config=config, model_adapter=adapter)
agent.add_tool(tool)
```

**现在：**
```python
agent = Agent.create(
    name="bot",
    model_adapter=adapter,
    system_prompt="...",
    tools=[tool]
)
```

### 示例3: 访问配置

**之前：**
```python
print(agent.config.name)
print(agent.config.max_iterations)
```

**现在：**
```python
print(agent.name)
print(agent.max_iterations)
```

### 示例4: 修改配置

**之前：**
```python
agent.config.system_prompt = "New prompt"
agent.config.max_iterations = 20
```

**现在：**
```python
agent.system_prompt = "New prompt"
agent.max_iterations = 20
```

## 配置文件加载

如果您之前使用JSON/YAML配置文件，现在需要直接映射到Agent字段：

### 之前

```python
import json

with open("config.json") as f:
    config_dict = json.load(f)

config = AgentConfig(**config_dict)
agent = Agent(config=config, model_adapter=adapter)
```

### 现在

```python
import json

with open("config.json") as f:
    config_dict = json.load(f)

agent = Agent(
        model_adapter=adapter,
        **config_dict
    )
```

或者使用Agent.create():

```python
agent = Agent.create(
    model_adapter=adapter,
    **config_dict
)
```

## 配置文件格式

### config.json 示例

```json
{
    "name": "assistant",
    "description": "Helpful assistant",
    "system_prompt": "You are a helpful assistant",
    "max_iterations": 10,
    "auto_tool_prompt": true,
    "enable_middleware": true
}
```

### 加载并创建

```python
import json
from lightagent import Agent, MockAdapter, ModelConfig

# 加载配置
with open("config.json") as f:
    config = json.load(f)

# 创建Agent
agent = Agent.create(
    model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
    **config
)
```

## 代码更新检查清单

迁移代码时，检查以下内容：

- [ ] 移除所有`AgentConfig`导入
- [ ] 移除所有`AgentConfig()`实例化
- [ ] 将`agent.config.field`改为`agent.field`
- [ ] 使用`Agent.create()`替代`Agent(config=...)`
- [ ] 更新配置加载代码

## 为什么移除AgentConfig？

1. **简化API**: 减少一个抽象层
2. **更直观**: 所有配置在Agent上可见
3. **减少代码**: 更少的样板代码
4. **语法糖**: `Agent.create()`提供便捷方法
5. **灵活性**: 更容易动态修改配置

## 向后兼容性

⚠️ **这是一个破坏性变更**

旧代码需要更新：
- 所有使用`AgentConfig`的代码
- 所有访问`agent.config.*`的代码
- 配置文件加载代码

## 常见问题

### Q: 如果我需要序列化配置怎么办？

```python
# 序列化Agent配置
config_dict = {
    "name": agent.name,
    "system_prompt": agent.system_prompt,
    "max_iterations": agent.max_iterations,
    # ... 其他字段
}

import json
json.dump(config_dict, file)
```

### Q: 如何在多个Agent间共享配置？

```python
# 方式1: 使用字典
shared_config = {
    "name": "base_agent",
    "system_prompt": "You are helpful",
    "max_iterations": 10
}

agent1 = Agent.create(model_adapter=adapter1, **shared_config)
agent2 = Agent.create(model_adapter=adapter2, **shared_config)

# 方式2: 使用函数
def create_agent(model_adapter, name):
    return Agent.create(
        name=name,
        model_adapter=model_adapter,
        system_prompt="You are helpful",
        max_iterations=10
    )

agent1 = create_agent(adapter1, "agent1")
agent2 = create_agent(adapter2, "agent2")
```

### Q: Agent.create()和直接实例化有什么区别？

```python
# Agent.create() - 更简洁，推荐
agent = Agent.create(
    name="bot",
    model_adapter=adapter,
    tools=[tool]  # 可以直接添加tools
)

# 直接实例化 - 更明确
agent = Agent(
    name="bot",
    model_adapter=adapter
)
agent.add_tool(tool)  # 需要手动添加
```

两者功能完全相同，`Agent.create()`是语法糖。

## 测试迁移

更新代码后，测试：

```python
from lightagent import Agent, MockAdapter, ModelConfig

# 测试基本创建
agent = Agent.create(
    name="test",
    model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
)

# 测试字段访问
assert agent.name == "test"
assert agent.max_iterations == 10  # 默认值

# 测试字段修改
agent.system_prompt = "Test"
assert agent.system_prompt == "Test"

print("迁移测试通过!")
```

## 总结

- ✅ AgentConfig已被移除
- ✅ 使用`Agent.create()`创建Agent
- ✅ 直接访问`agent.field`而不是`agent.config.field`
- ✅ 更新配置加载逻辑
- ✅ 代码更简洁、更直观

需要帮助？查看：
- `examples/simple_demo.py` - 基本用法
- `examples/` - 更多示例
- `docs/` - 完整文档

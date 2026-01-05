# Prompt Engineering Guide

## 概述

LightAgent提供了灵活的提示词工程能力，包括：
1. System prompt配置
2. 直接模型调用
3. 自动工具提示词生成
4. 自定义提示词模板

## 核心功能

### 1. System Prompt配置

在AgentConfig中配置基础system prompt：

```python
from lightagent import Agent, AgentConfig

agent_config = AgentConfig(
    name="assistant",
    system_prompt="""You are a helpful assistant specialized in weather information.
Always provide accurate and helpful responses."""
)

agent = Agent(config=agent_config, model_adapter=model_adapter)
```

### 2. 自动工具提示词生成

当`auto_tool_prompt=True`时，Agent会自动将工具的描述、参数等信息拼接到system prompt中。

#### 默认行为

```python
agent_config = AgentConfig(
    name="assistant",
    system_prompt="You are a helpful assistant.",
    auto_tool_prompt=True  # 启用自动工具提示词
)
```

生成的system prompt会包含：

```
You are a helpful assistant.

You have access to the following tools:

## get_weather
**Description**: Get current weather for a location
**Parameters**:
- `location` (required): City name or location
- `unit` (optional): Temperature unit (celsius or fahrenheit)

## calculator
**Description**: Calculate a mathematical expression
**Parameters**:
- `expression` (required): Mathematical expression

When you need to use a tool, respond with a tool call in the appropriate format.
Only use tools when necessary. If you can answer directly, do so.
```

### 3. call()方法 - 直接模型调用

`call()`方法提供更灵活的模型调用方式：

```python
# 基本调用
result = await agent.call(
    user_prompt="What's the weather in Tokyo?"
)

# 使用自定义system prompt
result = await agent.call(
    user_prompt="Calculate 25 * 4",
    system_prompt="You are a math expert. Use the calculator tool."
)

# 限制使用的工具
result = await agent.call(
    user_prompt="What's the weather in Paris?",
    tools=["get_weather"]  # 只使用get_weather工具
)
```

#### 参数说明

- `user_prompt`: 用户消息/提示词
- `system_prompt`: 可选，临时覆盖配置的system prompt
- `tools`: 可选，限制本次调用使用的工具列表

### 4. 自定义工具提示词模板

完全自定义工具信息的展示方式：

```python
custom_template = """## Available Tools

You can use these tools to help the user:

{tool_descriptions}

**Instructions**:
- Think step by step before using tools
- Explain which tool you're using and why
- Show the tool results to the user
- Always be helpful and accurate"""

agent_config = AgentConfig(
    name="assistant",
    system_prompt="You are a helpful AI assistant.",
    auto_tool_prompt=True,
    tool_prompt_template=custom_template
)
```

模板中使用`{tool_descriptions}`作为占位符，会被自动替换为生成的工具描述。

## 提示词构建流程

### 内部流程

当调用`agent.run()`或`agent.call()`时，内部会：

1. **构建System Prompt**
   ```python
   system_prompt = agent._build_system_prompt()
   ```
   - 获取配置的system_prompt
   - 如果`auto_tool_prompt=True`，追加工具描述
   - 如果有自定义模板，使用模板格式化

2. **准备消息列表**
   ```python
   messages = agent._prepare_messages(user_message)
   ```
   - System prompt（包含工具描述）
   - 对话历史
   - 当前用户消息

3. **调用模型**
   ```python
   response = await model_adapter.call(
       messages=messages,
       tools=provider_tools_schema
   )
   ```

### 消息格式

最终发送给模型的消息格式：

```python
[
    {
        "role": "system",
        "content": "You are a helpful assistant.\n\nYou have access to...\n\n## tool_name\n..."
    },
    {
        "role": "user",
        "content": "Previous conversation messages..."
    },
    {
        "role": "assistant",
        "content": "Previous assistant responses..."
    },
    {
        "role": "user",
        "content": "Current user message"
    }
]
```

## 配置选项

### AgentConfig相关配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `system_prompt` | str | None | 基础system prompt |
| `auto_tool_prompt` | bool | True | 是否自动添加工具描述 |
| `tool_prompt_template` | str | None | 自定义工具提示词模板 |

### 工具Schema生成

每个工具通过`get_schema()`方法提供schema：

```python
class MyTool(BaseTool):
    name = "my_tool"
    description = "Tool description"

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        )
```

## 使用场景

### 场景1: 专业领域助手

```python
agent_config = AgentConfig(
    name="math_tutor",
    system_prompt="""You are a mathematics tutor.
Help students understand math concepts step by step.
Use the calculator tool when needed.""",
    auto_tool_prompt=True
)

agent.add_tool(calculator_tool)
```

### 场景2: 任务型Agent

```python
# 使用call()方法快速执行特定任务
result = await agent.call(
    user_prompt="Calculate compound interest for 5 years",
    system_prompt="You are a financial calculator. Use the calculator tool.",
    tools=["calculator"]
)
```

### 场景3: 多角色切换

```python
# 创建一个agent，动态切换角色
agent = Agent(config=AgentConfig(
    system_prompt="You are a helpful assistant."
))

# 作为天气助手
weather_response = await agent.call(
    user_prompt="What's the weather?",
    system_prompt="You are a weather expert.",
    tools=["get_weather"]
)

# 作为计算器
calc_response = await agent.call(
    user_prompt="Calculate 100 * 5",
    system_prompt="You are a calculator.",
    tools=["calculator"]
)
```

### 场景4: 完全手动控制

```python
# 禁用自动工具提示词，完全自定义
agent_config = AgentConfig(
    name="assistant",
    system_prompt="""You are a helpful assistant with access to:

1. Weather tool: Get weather information for any city
2. Calculator: Perform mathematical calculations

Use these tools when appropriate to help users.""",
    auto_tool_prompt=False  # 手动控制工具描述
)
```

## 最佳实践

### 1. System Prompt设计

**好的实践：**
```python
system_prompt = """You are a helpful assistant specialized in weather information.

Your role:
- Provide accurate weather data
- Explain weather conditions clearly
- Suggest appropriate clothing

Tools available:
- get_weather: Use this for all weather queries"""
```

**避免：**
```python
# 太简单
system_prompt = "You are helpful"

# 太复杂
system_prompt = """...（1000字指令）..."""
```

### 2. 工具描述

确保工具有清晰的描述和参数说明：

```python
async def get_weather(
    location: str,
    unit: str = "celsius"
) -> dict:
    """
    Get current weather for a location

    Args:
        location: City name (e.g., "Tokyo", "New York")
        unit: "celsius" or "fahrenheit"

    Returns:
        Weather data including temperature, condition, humidity
    """
    ...
```

### 3. 模板设计

设计清晰的模板结构：

```python
template = """# Role
{system_prompt}

# Available Tools
{tool_descriptions}

# Guidelines
1. Think before using tools
2. Explain your actions
3. Show results clearly"""
```

### 4. 性能优化

- 对于简单任务，禁用`auto_tool_prompt`减少token使用
- 使用`tools`参数限制可用工具
- 缓存常用的system prompt

## 高级技巧

### 1. Few-shot Prompting

```python
system_prompt = """You are a calculator assistant.

Examples:
User: What is 5 + 3?
Assistant: [calculator: 5 + 3] The result is 8.

User: Calculate 10 * 2
Assistant: [calculator: 10 * 2] The result is 20."""

agent = Agent(
    config=AgentConfig(
        system_prompt=system_prompt,
        auto_tool_prompt=False
    )
)
```

### 2. Chain of Thought

```python
system_prompt = """You are a helpful assistant.

When solving problems:
1. Think step by step
2. Explain your reasoning
3. Use tools when needed
4. Verify your answers"""
```

### 3. 动态System Prompt

```python
async def adaptive_agent(user_query: str):
    # 根据查询类型调整prompt
    if "weather" in user_query.lower():
        system_prompt = "You are a weather expert."
        tools = ["get_weather"]
    elif "calculate" in user_query.lower():
        system_prompt = "You are a math expert."
        tools = ["calculator"]
    else:
        system_prompt = "You are a helpful assistant."
        tools = None

    return await agent.call(
        user_prompt=user_query,
        system_prompt=system_prompt,
        tools=tools
    )
```

## 故障排除

### 问题1: 工具没有被调用

**原因：**
- 工具描述不清晰
- `auto_tool_prompt`被禁用但没有手动添加工具信息

**解决：**
```python
# 检查生成的prompt
print(agent._build_system_prompt())

# 确保启用自动工具提示
agent.config.auto_tool_prompt = True
```

### 问题2: Token使用过多

**原因：**
- 每次调用都包含完整的工具描述
- System prompt太长

**解决：**
```python
# 禁用自动工具提示词，手动简化
agent.config.auto_tool_prompt = False
agent.config.system_prompt = "You have access to weather and calculator tools."

# 或者使用call()限制工具
result = await agent.call(
    user_prompt="Calculate something",
    tools=["calculator"]  # 只包含calculator的描述
)
```

### 问题3: 提示词格式混乱

**原因：**
- 工具schema参数格式不正确
- 自定义模板语法错误

**解决：**
```python
# 检查工具schema
for tool in agent.tools.values():
    print(tool.get_schema())

# 测试自定义模板
template = "Tools: {tool_descriptions}"
print(template.format(tool_descriptions="test"))
```

## 示例代码

完整示例请参考：
- `examples/prompt_engineering.py` - 提示词工程完整示例

## 总结

LightAgent的提示词工程功能提供了：

1. ✅ **灵活的System Prompt配置**
2. ✅ **自动工具描述生成**
3. ✅ **直接的call()方法**
4. ✅ **自定义模板支持**
5. ✅ **完整的控制能力**

通过合理使用这些功能，你可以构建精确、高效的AI Agent。

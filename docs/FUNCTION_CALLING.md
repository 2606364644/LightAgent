# Function Calling 多模型支持说明

## 问题

不同模型供应商的function calling格式不同：

- **OpenAI**: 使用标准的function calling格式
- **Anthropic (Claude)**: 使用tool use格式，结构略有不同
- **Ollama**: 使用OpenAI兼容格式

如果不进行转换，同一个工具无法在不同模型上使用。

## 解决方案

LightAgent实现了自动格式转换系统：

### 1. Schema转换 (`lightagent/models/schemas.py`)

将统一的工具schema转换为各供应商特定格式：

```python
class BaseSchemaConverter:
    def convert_to_openai(self, tool_schema):
        """OpenAI格式"""
        return {
            "type": "function",
            "function": {
                "name": tool_schema["name"],
                "description": tool_schema["description"],
                "parameters": tool_schema["parameters"]
            }
        }

    def convert_to_anthropic(self, tool_schema):
        """Anthropic格式"""
        return {
            "name": tool_schema["name"],
            "description": tool_schema["description"],
            "input_schema": tool_schema["parameters"]  # 注意：这里叫input_schema
        }
```

### 2. Tool Call解析

将模型返回的tool call转换为统一格式：

```python
class ToolCallFormatter:
    @staticmethod
    def format_openai_tool_call(tool_call):
        return {
            "id": tool_call["id"],
            "name": tool_call["function"]["name"],
            "arguments": json.loads(tool_call["function"]["arguments"])
        }

    @staticmethod
    def format_anthropic_tool_call(tool_call):
        return {
            "id": tool_call["id"],
            "name": tool_call["name"],  # 直接在顶层
            "arguments": tool_call["input"]  # 注意：这里叫input
        }
```

### 3. 使用方式

在Agent配置中指定provider：

```python
agent = Agent(
    config=AgentConfig(
        name="assistant",
        model_provider="openai",  # 或 "anthropic", "ollama"
        tools=["my_tool"]
    ),
    model_adapter=your_model_adapter
)
```

框架会自动：
1. 根据provider选择转换器
2. 将工具schema转换为正确格式
3. 解析模型返回的tool call
4. 统一执行工具

### 4. 扩展新供应商

添加新的模型供应商只需3步：

#### 步骤1: 添加转换方法

```python
class BaseSchemaConverter:
    def convert_to_new_provider(self, tool_schema):
        """新供应商格式"""
        return {
            # 转换为新供应商的格式
        }
```

#### 步骤2: 添加解析方法

```python
class ToolCallFormatter:
    @staticmethod
    def format_new_provider_tool_call(tool_call):
        """解析新供应商格式"""
        return {
            "id": tool_call["id"],
            "name": tool_call["name"],
            "arguments": tool_call["arguments"]
        }
```

#### 步骤3: 注册adapter

```python
# 在convert_schemas方法中添加
elif self.provider == "new_provider":
    converted.append(self.convert_to_new_provider(schema))

# 在parse_tool_calls方法中添加
elif self.provider == "new_provider":
    parsed.append(self.format_new_provider_tool_call(call))
```

## 示例

查看 `examples/multi_model_agent.py` 了解完整示例。

关键点：
- 工具定义与供应商无关
- 只需在配置时指定provider
- 自动处理格式差异

## 技术细节

### 执行流程

1. **定义工具**（供应商无关）
   ```python
   tool = FunctionBuilder.create_tool(my_func)
   ```

2. **添加到Agent**
   ```python
   agent.add_tool(tool)
   ```

3. **推理循环中转换**
   ```python
   # 获取adapter
   fc_adapter = get_function_call_adapter(config.model_provider)

   # 转换schema
   provider_schema = fc_adapter.convert_schemas(tools_schema)

   # 调用模型
   response = await model.call(tools=provider_schema)

   # 解析tool calls
   tool_calls = fc_adapter.parse_tool_calls(response["tool_calls"])
   ```

4. **执行工具**（统一格式）
   ```python
   for tool_call in tool_calls:
       await tool.execute(**tool_call["arguments"])
   ```

### 优势

1. **一次定义，多处使用**: 工具只需定义一次
2. **透明转换**: 开发者无需关心格式差异
3. **易于扩展**: 添加新供应商很简单
4. **类型安全**: 使用Pydantic验证

## 测试

使用MockAdapter测试多供应商支持：

```python
# 测试OpenAI格式
agent = Agent(
    config=AgentConfig(model_provider="openai", ...),
    model_adapter=MockAdapter(...)
)

# 测试Anthropic格式
agent = Agent(
    config=AgentConfig(model_provider="anthropic", ...),
    model_adapter=MockAdapter(...)
)
```

MockAdapter返回标准格式，通过adapter转换验证正确性。

## 总结

LightAgent的function calling多模型支持通过以下方式实现：

1. 统一的工具定义接口
2. 自动schema格式转换
3. 统一的tool call解析
4. 透明的执行流程

开发者可以专注于业务逻辑，无需关心底层模型的格式差异。

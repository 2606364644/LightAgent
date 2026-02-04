# 文件系统 Prompt 存储指南

## 概述

为了避免在代码中存储大量 prompt 模板，我们支持**从文件系统加载 prompt**。

### 优势

1. **代码分离** - prompt 和代码分离，便于管理
2. **版本控制** - prompt 变化可以被版本控制系统追踪
3. **易于编辑** - 非程序员也能编辑 prompt 文件
4. **按需加载** - 只加载需要的 prompt，节省内存
5. **热重载** - 文件变化时自动更新（可选）

---

## 目录结构

```
prompts/
├── planning/                    # Planning 工作流的 prompt
│   ├── default.yaml            # 默认 prompt
│   ├── research.yaml           # 研究型 prompt
│   ├── development.yaml        # 开发型 prompt
│   └── simple.txt              # 简单文本格式
├── sequential/                  # Sequential 工作流
│   ├── default.yaml
│   └── deployment.yaml
├── interactive/                 # Interactive 工作流
│   ├── default.yaml
│   └── customer_service.yaml
├── code_execute_refine/         # Code-Execute 工作流
│   ├── default.yaml
│   └── python.yaml
└── human_loop/                  # Human-in-the-Loop 工作流
    ├── default.yaml
    └── content_review.yaml
```

---

## 文件格式

### 1. YAML 格式（推荐）

**文件：** `prompts/planning/research.yaml`

```yaml
name: research_planning
workflow_type: planning

system_prompt: |
  你是一个专业的研究规划助手。

  研究计划应该包括：
  1. 文献综述阶段
  2. 数据收集阶段
  3. 分析方法阶段
  4. 验证实验阶段

task_prompt: |
  研究目标：{goal}

  背景信息：{context_info}

  请制定详细的研究计划。

variables:
  default_duration: "4周"
  team_size: "3-5人"
```

**特点：**
- 结构清晰，易于编辑
- 支持多行文本
- 支持变量定义

### 2. JSON 格式

**文件：** `prompts/planning/research.json`

```json
{
  "name": "research_planning",
  "workflow_type": "planning",
  "system_prompt": "你是一个专业的研究规划助手。\n研究计划应该包括：\n1. 文献综述\n2. 数据收集\n3. 分析方法",
  "task_prompt": "研究目标：{goal}\n请制定研究计划。",
  "variables": {
    "default_duration": "4周",
    "team_size": "3-5人"
  }
}
```

### 3. 纯文本格式

**文件：** `prompts/planning/simple.txt`

```
---SYSTEM---
You are a simple task planner. Break down goals into steps.

---TASK---
Goal: {goal}

Create a simple step-by-step plan.

---VARS---
default_complexity=medium
default_priority=medium
```

**格式说明：**
- `---SYSTEM---` - 系统提示词部分
- `---TASK---` - 任务提示词部分
- `---VARS---` - 变量部分（key=value 格式）

---

## 使用方法

### 基础使用

```python
from lightagent_workflow.prompt_loader import create_prompt_loader
from lightagent_workflow import WorkflowManager

# 1. 创建 prompt loader
prompt_loader = create_prompt_loader(
    base_path="prompts",      # prompt 文件目录
    format="yaml"             # 文件格式（yaml/json/txt）
)

# 2. 创建 manager（使用 loader 的 registry）
manager = WorkflowManager(
    agent=agent,
    prompt_registry=prompt_loader.registry,  # 使用 loader 的 registry
    tool_registry=tool_registry
)

# 3. 使用文件中的 prompt
wf = await manager.create_workflow(
    "planning",
    "研究AI",
    config={
        'prompts': {
            'template_name': 'research_planning'  # 使用 prompts/planning/research.yaml
        }
    }
)
```

### 高级配置

#### 1. 热重载

```python
from lightagent_workflow.prompt_loader import PromptFileLoader, PromptFileConfig

loader = PromptFileLoader(
    config=PromptFileConfig(
        base_path=Path("prompts"),
        format="yaml",
        watch_changes=True  # 启用热重载
    )
)

# 检查文件变化并重载
reloaded = loader.reload_if_changed()
print(f"{reloaded} 个文件已更新")
```

#### 2. 只加载特定工作流类型

```python
# 只加载 planning 工作流的 prompt
loader = PromptFileLoader()
count = loader.load_from_directory(
    directory=Path("prompts"),
    workflow_type="planning"
)
print(f"加载了 {count} 个 planning prompt")
```

#### 3. 自定义目录

```python
# 使用自定义目录
custom_loader = create_prompt_loader(
    base_path="my_custom_prompts",
    format="yaml"
)

# 项目可以有多个 prompt 目录
project_prompts = create_prompt_loader(base_path="prompts")
team_prompts = create_prompt_loader(base_path="team_prompts")
```

---

## 创建新的 Prompt

### 方式 1: 手动创建文件

**步骤：**
1. 在 `prompts/<workflow_type>/` 创建新文件
2. 按 YAML/JSON/TXT 格式编写 prompt
3. 重新运行程序

**示例：** 创建 `prompts/planning/ai_research.yaml`

```yaml
name: ai_research
workflow_type: planning

system_prompt: |
  你是 AI 研究专家。专注于深度学习和 NLP 领域。

task_prompt: |
  AI 研究目标：{goal}

  请制定详细的研究计划。

variables:
  default_duration: "8周"
  required_expertise: "深度学习"
```

### 方式 2: 通过代码保存

```python
from lightagent_workflow.prompts import WorkflowPromptTemplate
from lightagent_workflow.prompt_loader import PromptFileLoader, PromptFileConfig

# 创建 prompt
new_prompt = WorkflowPromptTemplate(
    name="ai_research",
    workflow_type="planning",
    system_prompt="你是 AI 研究专家",
    task_prompt="研究目标：{goal}",
    variables={"duration": "8周"}
)

# 保存到文件
loader = PromptFileLoader(
    config=PromptFileConfig(
        base_path=Path("prompts"),
        format="yaml"
    )
)

file_path = loader.save_prompt(new_prompt)
print(f"已保存到: {file_path}")
```

---

## Prompt 变量

### 定义变量

**YAML:**
```yaml
variables:
  default_duration: "4周"
  team_size: "5人"
  budget: "$10,000"
```

**使用变量:**
```python
wf = await manager.create_workflow(
    "planning",
    "研究AI",
    config={
        'prompts': {
            'template_name': 'research_planning',
            'variables': {  # 覆盖或添加变量
                'budget': '$20,000',  # 覆盖默认值
                'deadline': '2024-12-31'  # 添加新变量
            }
        }
    }
)
```

**在 prompt 中使用:**
```yaml
task_prompt: |
  研究目标：{goal}
  预算：{budget}
  截止日期：{deadline}
  默认周期：{default_duration}
```

---

## 最佳实践

### 1. 目录组织

```
prompts/
├── common/                  # 公共 prompt（可选）
│   └── base.yaml
├── planning/                # 按工作流类型组织
│   ├── default.yaml
│   ├── research.yaml
│   └── development.yaml
└── sequential/
    ├── default.yaml
    └── deployment.yaml
```

### 2. 命名规范

- 使用小写字母和下划线
- 名称要描述性强
- 例如：`customer_service.yaml`, `code_review.yaml`

### 3. 版本控制

```yaml
name: research_planning
version: "1.0"  # 添加版本号
workflow_type: planning

# prompt 内容...
```

### 4. 注释

**YAML 支持注释：**
```yaml
system_prompt: |
  你是研究规划助手。

  # 重要提示：
  # - 考虑时间限制
  # - 考虑资源限制
  # - 考虑团队规模

  请制定研究计划。
```

### 5. 多语言支持

```
prompts/
├── planning/
│   ├── default_en.yaml    # 英文
│   ├── default_zh.yaml    # 中文
│   └── default_ja.yaml    # 日文
```

---

## 迁移指南

### 从代码迁移到文件

**之前（代码中定义）：**
```python
prompt = WorkflowPromptTemplate(
    name="research_planning",
    workflow_type="planning",
    system_prompt="你是研究专家",
    task_prompt="研究: {goal}"
)
registry.register_template(prompt)
```

**之后（文件中定义）：**

**1. 创建文件** `prompts/planning/research.yaml`
```yaml
name: research_planning
workflow_type: planning
system_prompt: "你是研究专家"
task_prompt: "研究: {goal}"
```

**2. 使用 loader**
```python
loader = create_prompt_loader(base_path="prompts")
manager = WorkflowManager(
    prompt_registry=loader.registry
)
```

---

## 故障排查

### 1. 文件未加载

**检查：**
```python
loader = create_prompt_loader(base_path="prompts")
available = loader.list_available_prompts()
print(available)  # 查看加载了哪些 prompt
```

### 2. 编码错误

**确保文件使用 UTF-8 编码：**
```python
# 保存时指定编码
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

### 3. YAML 语法错误

**验证 YAML：**
```bash
# 使用 yamllint
yamllint prompts/planning/research.yaml
```

---

## 对比总结

### 文件系统 vs 代码定义

| 特性 | 文件系统 | 代码定义 |
|------|---------|---------|
| 内存占用 | 低（按需加载） | 高（全部在内存） |
| 易于编辑 | ✅ 文本编辑器 | ❌ 需要改代码 |
| 版本控制 | ✅ 清晰的 diff | ⚠️ 混在代码里 |
| 热重载 | ✅ 支持 | ❌ 需要重启 |
| 分发 | ⚠️ 需要额外文件 | ✅ 单一文件 |
| 适合场景 | 大量 prompt | 少量 prompt |

### 推荐方案

**使用文件系统，如果：**
- 有超过 5 个工作流类型
- 每个类型有多个 prompt
- 需要频繁修改 prompt
- 非程序员需要编辑 prompt

**使用代码定义，如果：**
- Prompt 数量少（< 5个）
- Prompt 很少变化
- 希望单一文件分发
- 快速原型开发

---

## 示例代码

完整示例：`examples/prompt_loader_example.py`

包含 6 个示例：
1. 从文件系统加载
2. 使用不同格式
3. 保存新 prompt
4. 热重载
5. 自定义目录
6. 混合使用

# 文件系统 Prompt 系统 - 实现总结

## 概述

成功实现了**基于文件系统的 Prompt 模板加载系统**，解决了工作流类型过多时 prompt 存储的问题。

---

## 问题

### 之前的问题

```python
# 所有 prompt 都在代码中定义
prompt_registry = WorkflowPromptRegistry()

prompt_registry.register_template(WorkflowPromptTemplate(
    name="planning_default",
    workflow_type="planning",
    system_prompt="...",
    task_prompt="..."
))

prompt_registry.register_template(WorkflowPromptTemplate(
    name="planning_research",
    workflow_type="planning",
    system_prompt="...",
    task_prompt="..."
))

# ... 数十个 prompt 定义

prompt_registry.register_template(WorkflowPromptTemplate(
    name="interactive_cs",
    workflow_type="interactive",
    system_prompt="...",
    task_prompt="..."
))

# ... 数十个 prompt 定义
```

**问题：**
- ❌ 代码臃肿
- ❌ 内存占用高（全部加载）
- ❌ 难以编辑
- ❌ 版本控制不清晰
- ❌ 不支持热重载

---

## 解决方案

### 新的架构

```
prompts/                          # 文件系统
├── planning/
│   ├── default.yaml
│   ├── research.yaml
│   └── development.yaml
├── sequential/
│   ├── default.yaml
│   └── deployment.yaml
├── interactive/
│   ├── default.yaml
│   └── customer_service.yaml
└── ...
```

**优势：**
- ✅ 代码分离
- ✅ 按需加载
- ✅ 易于编辑
- ✅ 版本控制清晰
- ✅ 支持热重载

---

## 核心组件

### 1. PromptFileLoader

**职责：** 从文件系统加载 prompt 模板

```python
from lightagent_workflow.prompt_loader import create_prompt_loader

# 创建 loader
loader = create_prompt_loader(
    base_path="prompts",   # prompt 目录
    format="yaml"          # 文件格式
)

# 自动加载所有 prompt
count = loader.load_from_directory()
print(f"加载了 {count} 个 prompt 模板")
```

**特性：**
- 支持 YAML、JSON、TXT 三种格式
- 按工作流类型组织文件
- 自动扫描目录
- 缓存机制

### 2. PromptFileConfig

**配置选项：**

```python
from lightagent_workflow.prompt_loader import PromptFileLoader, PromptFileConfig

config = PromptFileConfig(
    base_path=Path("prompts"),  # 基础路径
    format="yaml",                # 文件格式
    watch_changes=False,          # 热重载
    cache_enabled=True            # 缓存
)

loader = PromptFileLoader(config=config)
```

---

## 文件格式

### YAML 格式（推荐）

**文件：** `prompts/planning/research.yaml`

```yaml
name: research_planning
workflow_type: planning

system_prompt: |
  你是一个专业的研究规划助手。

  研究计划应该包括：
  1. 文献综述
  2. 数据收集
  3. 分析方法
  4. 验证实验

task_prompt: |
  研究目标：{goal}

  背景信息：{context_info}

  请制定详细的研究计划。

variables:
  default_duration: "4周"
  team_size: "3-5人"
```

### JSON 格式

```json
{
  "name": "research_planning",
  "workflow_type": "planning",
  "system_prompt": "你是研究规划助手。",
  "task_prompt": "研究：{goal}",
  "variables": {
    "duration": "4周"
  }
}
```

### 纯文本格式

```
---SYSTEM---
你是研究规划助手。

---TASK---
研究：{goal}

---VARS---
duration=4周
team_size=5人
```

---

## 使用方式

### 方式 1: 基础使用

```python
# 1. 创建 loader
loader = create_prompt_loader(base_path="prompts", format="yaml")

# 2. 创建 manager（使用 loader 的 registry）
manager = WorkflowManager(
    agent=agent,
    prompt_registry=loader.registry,  # 使用 loader 的 registry
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

### 方式 2: 热重载

```python
# 创建启用热重载的 loader
loader = PromptFileLoader(
    config=PromptFileConfig(
        base_path=Path("prompts"),
        format="yaml",
        watch_changes=True  # 启用热重载
    )
)

# 检查文件变化并重载
reloaded = loader.reload_if_changed()
```

### 方式 3: 保存新 Prompt

```python
# 创建新 prompt
new_prompt = WorkflowPromptTemplate(
    name="my_custom",
    workflow_type="planning",
    system_prompt="你是专家",
    task_prompt="任务: {goal}"
)

# 保存到文件
loader = PromptFileLoader(...)
file_path = loader.save_prompt(new_prompt)
print(f"已保存到: {file_path}")
```

### 方式 4: 查看可用 Prompt

```python
# 列出所有可用的 prompt
available = loader.list_available_prompts()

for wf_type, prompts in available.items():
    print(f"{wf_type}: {', '.join(prompts)}")

# 输出:
# planning: default, research, development
# sequential: default, deployment
# interactive: default, customer_service
```

---

## 最佳实践

### 1. 目录组织

```
prompts/
├── common/              # 公共 prompt（可选）
├── planning/            # 按工作流类型组织
├── sequential/
├── interactive/
└── ...
```

### 2. 命名规范

- 使用小写和下划线：`research_planning.yaml`
- 描述性名称：`customer_service.yaml`
- 避免特殊字符

### 3. 版本控制

**Git 会清晰显示变化：**

```yaml
# prompts/planning/research.yaml
name: research_planning
version: "1.0"

system_prompt: |
  你是研究专家。
  # v1.0: 初始版本
  # v1.1: 添加时间估算要求
  请制定研究计划。
```

### 4. 多语言支持

```
prompts/
├── planning/
│   ├── default_en.yaml
│   ├── default_zh.yaml
│   └── default_ja.yaml
```

---

## 对比总结

### 文件系统 vs 代码定义

| 特性 | 文件系统 | 代码定义 |
|------|---------|---------|
| 内存占用 | ✅ 低（按需） | ❌ 高（全部） |
| 易于编辑 | ✅ 文本编辑器 | ❌ 需改代码 |
| 版本控制 | ✅ 清晰 diff | ⚠️ 混在代码里 |
| 热重载 | ✅ 支持 | ❌ 需重启 |
| 非程序员 | ✅ 可编辑 | ❌ 需编程 |
| 分发 | ⚠️ 多文件 | ✅ 单文件 |

### 推荐场景

**使用文件系统，如果：**
- ✅ 有超过 5 个工作流类型
- ✅ 每个类型有多个 prompt
- ✅ 需要频繁修改
- ✅ 非程序员需要编辑

**使用代码定义，如果：**
- Prompt 数量少（< 5）
- Prompt 很少变化
- 希望单一文件
- 快速原型开发

---

## 文件清单

### 新增文件

1. **`lightagent-workflow/prompt_loader.py`** - Prompt 文件加载器
   - PromptFileLoader 类
   - 支持 YAML/JSON/TXT 格式
   - 热重载支持
   - 保存 prompt 到文件

2. **`docs/WORKFLOW_FILE_PROMPTS.md`** - 完整使用指南
   - 格式说明
   - 使用示例
   - 最佳实践
   - 迁移指南

3. **`examples/prompt_loader_example.py`** - 6 个使用示例
   - 从文件加载
   - 不同格式
   - 保存 prompt
   - 热重载
   - 自定义目录
   - 混合使用

### 示例 Prompt 文件

4. **`examples/prompts/planning/default.yaml`** - 默认 planning prompt
5. **`examples/prompts/planning/research.yaml`** - 研究 prompt（中文）
6. **`examples/prompts/planning/simple.txt`** - 纯文本格式
7. **`examples/prompts/sequential/default.yaml`** - 默认 sequential prompt
8. **`examples/prompts/interactive/customer_service.yaml`** - 客服 prompt（中文）
9. **`examples/prompts/code_execute_refine/python.yaml`** - Python 代码生成
10. **`examples/prompts/human_loop/content_review.yaml`** - 内容审核（中文）

---

## 总结

### ✅ 完全解决问题

**问题：** 工作流太多，prompt 不好存储

**解决：**
1. ✅ 文件系统存储 - 不占用代码空间
2. ✅ 按需加载 - 节省内存
3. ✅ 易于管理 - 目录结构清晰
4. ✅ 支持多种格式 - YAML/JSON/TXT
5. ✅ 热重载 - 文件变化自动更新
6. ✅ 向后兼容 - 仍支持代码定义

### 使用建议

**项目小（< 5个 prompt）:**
- 可以使用代码定义

**项目大（> 5个 prompt）:**
- 推荐使用文件系统

**混合使用:**
- 核心 prompt 用代码
- 可变 prompt 用文件

所有功能已实现并提供完整文档！

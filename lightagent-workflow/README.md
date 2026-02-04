# LightAgent Workflow

这是 LightAgent 的 workflow 模块，已从主包中独立出来。

## 目录结构

```
lightagent-workflow/
├── __init__.py              # 模块初始化和导出
├── base.py                  # 基础类和接口
├── engine.py                # 工作流引擎
├── integration.py           # Agent 集成
├── planning/                # 任务规划
│   ├── __init__.py
│   ├── task.py
│   ├── planner.py
│   └── executor.py
└── prompts/                 # 提示词模板
    ├── __init__.py
    ├── template.py
    ├── manager.py
    └── presets.py
```

## 使用方式

### 方式 1: 添加到 Python 路径

在你的代码中添加：

```python
import sys
from pathlib import Path

# 添加 lightagent-workflow 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lightagent-workflow"))

from lightagent_workflow import WorkflowEngine, create_workflow_engine
```

### 方式 2: 使用 PYTHONPATH 环境变量

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/LightAgent/lightagent-workflow"
```

### 方式 3: 在开发时安装为可编辑包

```bash
cd lightagent-workflow
pip install -e .
```

然后在代码中正常导入：

```python
from lightagent_workflow import create_workflow_engine, WorkflowEngine
```

## 代码示例

```python
from lightagent import Agent, OpenAIAdapter
from lightagent_workflow import create_workflow_engine

# 创建 agent
agent = Agent(
    name="workflow-agent",
    model_adapter=OpenAIAdapter(api_key="your-key", model="gpt-3.5-turbo")
)

# 创建工作流引擎
engine = await create_workflow_engine(agent=agent, verbose=True)

# 执行工作流
result = await engine.execute("你的任务描述")
```

## 说明

- 这个模块不是独立的发布包，只是代码组织上的独立
- 依赖主包 `lightagent`
- 未来可能会发布为独立的包 `lightagent-workflow`

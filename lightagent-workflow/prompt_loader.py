"""
File-based Prompt Template System

Loads prompt templates from file system instead of storing them all in memory.
Supports YAML, JSON, and plain text formats.
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import yaml
import json
from .prompts import WorkflowPromptTemplate, WorkflowPromptRegistry


class PromptFileConfig(BaseModel):
    """Configuration for prompt file loading"""
    base_path: Path = Field(default_factory=lambda: Path("prompts"))
    format: str = "yaml"  # yaml, json, txt
    watch_changes: bool = False  # Hot reload on file changes
    cache_enabled: bool = True


class PromptFileLoader(BaseModel):
    """
    Loads prompt templates from file system

    Directory structure:
    prompts/
    ├── planning/
    │   ├── default.yaml
    │   ├── research.yaml
    │   └── development.yaml
    ├── sequential/
    │   ├── default.yaml
    │   └── deployment.yaml
    └── ...
    """

    config: PromptFileConfig = Field(default_factory=PromptFileConfig)
    registry: WorkflowPromptRegistry = Field(default_factory=WorkflowPromptRegistry)
    _file_cache: Dict[str, float] = Field(default_factory=dict)  # path -> mtime

    class Config:
        arbitrary_types_allowed = True

    def load_from_directory(
        self,
        directory: Optional[Path] = None,
        workflow_type: Optional[str] = None
    ) -> int:
        """
        Load prompt templates from directory

        Args:
            directory: Directory to load from (default: config.base_path)
            workflow_type: Only load specific workflow type (default: all)

        Returns:
            Number of templates loaded
        """
        base_path = directory or self.config.base_path

        if not base_path.exists():
            if self.config.cache_enabled:
                # Create directory if it doesn't exist
                base_path.mkdir(parents=True, exist_ok=True)
                return 0
            return 0

        count = 0

        if workflow_type:
            # Load specific workflow type
            workflow_path = base_path / workflow_type
            if workflow_path.exists():
                count += self._load_workflow_directory(workflow_path, workflow_type)
        else:
            # Load all workflow types
            for workflow_dir in base_path.iterdir():
                if workflow_dir.is_dir():
                    wf_type = workflow_dir.name
                    count += self._load_workflow_directory(workflow_dir, wf_type)

        return count

    def _load_workflow_directory(self, workflow_path: Path, workflow_type: str) -> int:
        """Load all prompt files for a workflow type"""
        count = 0

        for prompt_file in workflow_path.glob(f"*.{self.config.format}"):
            try:
                template = self._load_prompt_file(prompt_file, workflow_type)
                if template:
                    self.registry.register_template(template)
                    self._file_cache[str(prompt_file)] = prompt_file.stat().st_mtime
                    count += 1
            except Exception as e:
                print(f"Error loading {prompt_file}: {e}")

        return count

    def _load_prompt_file(
        self,
        file_path: Path,
        workflow_type: str
    ) -> Optional[WorkflowPromptTemplate]:
        """Load a single prompt file"""
        file_format = self.config.format.lower()

        if file_format == "yaml":
            return self._load_yaml_prompt(file_path, workflow_type)
        elif file_format == "json":
            return self._load_json_prompt(file_path, workflow_type)
        elif file_format == "txt":
            return self._load_txt_prompt(file_path, workflow_type)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    def _load_yaml_prompt(
        self,
        file_path: Path,
        workflow_type: str
    ) -> Optional[WorkflowPromptTemplate]:
        """Load YAML format prompt"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return WorkflowPromptTemplate(
            name=data.get('name', file_path.stem),
            workflow_type=workflow_type,
            system_prompt=data.get('system_prompt'),
            task_prompt=data.get('task_prompt'),
            variables=data.get('variables', {})
        )

    def _load_json_prompt(
        self,
        file_path: Path,
        workflow_type: str
    ) -> Optional[WorkflowPromptTemplate]:
        """Load JSON format prompt"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return WorkflowPromptTemplate(
            name=data.get('name', file_path.stem),
            workflow_type=workflow_type,
            system_prompt=data.get('system_prompt'),
            task_prompt=data.get('task_prompt'),
            variables=data.get('variables', {})
        )

    def _load_txt_prompt(
        self,
        file_path: Path,
        workflow_type: str
    ) -> Optional[WorkflowPromptTemplate]:
        """
        Load plain text format prompt

        Format:
        ---SYSTEM---
        System prompt here
        ---TASK---
        Task prompt here
        ---VARS---
        key1=value1
        key2=value2
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        sections = content.split('---')
        system_prompt = None
        task_prompt = None
        variables = {}

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.split('\n', 1)
            if len(lines) < 2:
                continue

            section_type = lines[0].strip().upper()
            section_content = lines[1].strip()

            if section_type == 'SYSTEM':
                system_prompt = section_content
            elif section_type == 'TASK':
                task_prompt = section_content
            elif section_type == 'VARS':
                for line in section_content.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        variables[key.strip()] = value.strip()

        return WorkflowPromptTemplate(
            name=file_path.stem,
            workflow_type=workflow_type,
            system_prompt=system_prompt,
            task_prompt=task_prompt,
            variables=variables
        )

    def reload_if_changed(self) -> int:
        """
        Reload templates if files have changed

        Returns:
            Number of reloaded templates
        """
        if not self.config.watch_changes:
            return 0

        count = 0
        base_path = self.config.base_path

        if not base_path.exists():
            return 0

        for file_path in base_path.rglob(f"*.{self.config.format}"):
            current_mtime = file_path.stat().st_mtime
            cached_mtime = self._file_cache.get(str(file_path), 0)

            if current_mtime > cached_mtime:
                # File changed, reload
                workflow_type = file_path.parent.name
                try:
                    template = self._load_prompt_file(file_path, workflow_type)
                    if template:
                        self.registry.register_template(template)
                        self._file_cache[str(file_path)] = current_mtime
                        count += 1
                except Exception as e:
                    print(f"Error reloading {file_path}: {e}")

        return count

    def save_prompt(
        self,
        template: WorkflowPromptTemplate,
        filename: Optional[str] = None,
        workflow_dir: Optional[Path] = None
    ) -> Path:
        """
        Save a prompt template to file

        Args:
            template: Template to save
            filename: Filename (default: template.name)
            workflow_dir: Workflow directory (default: base_path/workflow_type)

        Returns:
            Path to saved file
        """
        base_path = workflow_dir or (self.config.base_path / template.workflow_type)
        base_path.mkdir(parents=True, exist_ok=True)

        filename = filename or f"{template.name}.{self.config.format}"
        file_path = base_path / filename

        if self.config.format == "yaml":
            self._save_yaml_prompt(file_path, template)
        elif self.config.format == "json":
            self._save_json_prompt(file_path, template)
        elif self.config.format == "txt":
            self._save_txt_prompt(file_path, template)

        return file_path

    def _save_yaml_prompt(self, file_path: Path, template: WorkflowPromptTemplate):
        """Save template as YAML"""
        data = {
            'name': template.name,
            'workflow_type': template.workflow_type,
            'system_prompt': template.system_prompt,
            'task_prompt': template.task_prompt,
            'variables': template.variables
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def _save_json_prompt(self, file_path: Path, template: WorkflowPromptTemplate):
        """Save template as JSON"""
        data = {
            'name': template.name,
            'workflow_type': template.workflow_type,
            'system_prompt': template.system_prompt,
            'task_prompt': template.task_prompt,
            'variables': template.variables
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_txt_prompt(self, file_path: Path, template: WorkflowPromptTemplate):
        """Save template as plain text"""
        content = ""

        if template.system_prompt:
            content += "---SYSTEM---\n"
            content += template.system_prompt + "\n\n"

        if template.task_prompt:
            content += "---TASK---\n"
            content += template.task_prompt + "\n\n"

        if template.variables:
            content += "---VARS---\n"
            for key, value in template.variables.items():
                content += f"{key}={value}\n"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def list_available_prompts(
        self,
        workflow_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        List available prompt files

        Args:
            workflow_type: Filter by workflow type

        Returns:
            Dictionary mapping workflow types to prompt names
        """
        result = {}
        base_path = self.config.base_path

        if not base_path.exists():
            return result

        if workflow_type:
            workflow_dirs = [base_path / workflow_type]
        else:
            workflow_dirs = [d for d in base_path.iterdir() if d.is_dir()]

        for workflow_dir in workflow_dirs:
            if not workflow_dir.is_dir():
                continue

            wf_type = workflow_dir.name
            prompts = []

            for prompt_file in workflow_dir.glob(f"*.{self.config.format}"):
                prompts.append(prompt_file.stem)

            if prompts:
                result[wf_type] = prompts

        return result


def create_prompt_loader(
    base_path: str = "prompts",
    format: str = "yaml",
    watch_changes: bool = False
) -> PromptFileLoader:
    """
    Create a prompt file loader

    Args:
        base_path: Base directory for prompt files
        format: File format (yaml, json, txt)
        watch_changes: Enable hot reload

    Returns:
        PromptFileLoader instance
    """
    config = PromptFileConfig(
        base_path=Path(base_path),
        format=format,
        watch_changes=watch_changes
    )

    loader = PromptFileLoader(config=config)

    # Load all prompts on creation
    loader.load_from_directory()

    return loader


def migrate_registry_to_files(
    registry: WorkflowPromptRegistry,
    output_dir: Path,
    format: str = "yaml"
) -> PromptFileLoader:
    """
    Migrate prompts from registry to file system

    Args:
        registry: Source registry
        output_dir: Output directory
        format: Output format

    Returns:
        PromptFileLoader with migrated prompts
    """
    loader = create_prompt_loader(
        base_path=str(output_dir),
        format=format
    )

    for template in registry.templates.values():
        loader.save_prompt(template)

    return loader

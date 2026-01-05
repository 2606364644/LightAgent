"""
Prompt manager for organizing and retrieving templates
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .template import PromptTemplate, MultiPartPrompt


class PromptManager(BaseModel):
    """
    Manager for organizing and retrieving prompt templates

    Features:
    - Register and retrieve templates by name
    - Template versioning
    - Dynamic template composition
    - Template search and filtering
    """

    templates: Dict[str, PromptTemplate] = Field(default_factory=dict)
    multipart_templates: Dict[str, MultiPartPrompt] = Field(default_factory=dict)
    categories: Dict[str, List[str]] = Field(default_factory=dict)
    metadata: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def register_template(
        self,
        name: str,
        template: PromptTemplate,
        category: Optional[str] = None,
        **metadata
    ):
        """
        Register a prompt template

        Args:
            name: Template name/identifier
            template: PromptTemplate instance
            category: Optional category for organization
            **metadata: Additional metadata
        """
        self.templates[name] = template

        # Add to category
        if category:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(name)

        # Store metadata
        self.metadata[name] = {
            'category': category,
            'description': template.description,
            **metadata
        }

    def register_multipart(
        self,
        name: str,
        template: MultiPartPrompt,
        category: Optional[str] = None,
        **metadata
    ):
        """
        Register a multipart prompt template

        Args:
            name: Template name/identifier
            template: MultiPartPrompt instance
            category: Optional category
            **metadata: Additional metadata
        """
        self.multipart_templates[name] = template

        if category:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(name)

        self.metadata[name] = {
            'category': category,
            'type': 'multipart',
            **metadata
        }

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name

        Args:
            name: Template name

        Returns:
            PromptTemplate or None if not found
        """
        return self.templates.get(name)

    def get_multipart(self, name: str) -> Optional[MultiPartPrompt]:
        """
        Get a multipart template by name

        Args:
            name: Template name

        Returns:
            MultiPartPrompt or None if not found
        """
        return self.multipart_templates.get(name)

    def list_templates(
        self,
        category: Optional[str] = None,
        include_metadata: bool = False
    ) -> List[str]:
        """
        List available templates

        Args:
            category: Filter by category
            include_metadata: Include metadata in results

        Returns:
            List of template names
        """
        if category:
            templates = self.categories.get(category, [])
        else:
            templates = list(self.templates.keys())

        if include_metadata:
            return [
                {
                    'name': name,
                    **self.metadata.get(name, {})
                }
                for name in templates
            ]

        return templates

    def search_templates(self, query: str) -> List[str]:
        """
        Search templates by description or name

        Args:
            query: Search query

        Returns:
            List of matching template names
        """
        query = query.lower()
        results = []

        for name, template in self.templates.items():
            # Check name
            if query in name.lower():
                results.append(name)
                continue

            # Check description
            if template.description and query in template.description.lower():
                results.append(name)

            # Check metadata
            meta = self.metadata.get(name, {})
            for key, value in meta.items():
                if isinstance(value, str) and query in value.lower():
                    results.append(name)
                    break

        return results

    def compose_templates(
        self,
        name: str,
        template_names: List[str],
        separator: str = "\n\n"
    ) -> PromptTemplate:
        """
        Compose multiple templates into one

        Args:
            name: Name for the composed template
            template_names: List of template names to compose
            separator: Separator between templates

        Returns:
            Composed PromptTemplate

        Raises:
            ValueError: If any template not found
        """
        templates = []
        for template_name in template_names:
            template = self.get_template(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            templates.append(template)

        # Compose templates
        composed = templates[0]
        for template in templates[1:]:
            composed = composed.compose(template, separator)

        # Register composed template
        composed.description = f"Composed from: {', '.join(template_names)}"
        self.register_template(name, composed, category='composed')

        return composed

    def create_template_from_string(
        self,
        name: str,
        template_string: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        **metadata
    ) -> PromptTemplate:
        """
        Create and register a template from a string

        Args:
            name: Template name
            template_string: Template string
            category: Optional category
            description: Optional description
            **metadata: Additional metadata

        Returns:
            Created PromptTemplate
        """
        template = PromptTemplate(
            template=template_string,
            description=description
        )

        self.register_template(name, template, category, **metadata)

        return template

    def export_templates(self, category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Export templates for serialization

        Args:
            category: Filter by category

        Returns:
            Dictionary of template data
        """
        result = {}

        template_names = self.list_templates(category=category)

        for name in template_names:
            template = self.get_template(name)
            if template:
                result[name] = {
                    'template': template.template,
                    'required_variables': template.required_variables,
                    'optional_variables': template.optional_variables,
                    'description': template.description,
                    'metadata': self.metadata.get(name, {})
                }

        return result

    def import_templates(
        self,
        templates_data: Dict[str, Dict[str, Any]],
        overwrite: bool = False
    ):
        """
        Import templates from serialized data

        Args:
            templates_data: Dictionary of template data
            overwrite: Whether to overwrite existing templates
        """
        for name, data in templates_data.items():
            if not overwrite and name in self.templates:
                continue

            template = PromptTemplate(
                template=data['template'],
                required_variables=data.get('required_variables', []),
                optional_variables=data.get('optional_variables', {}),
                description=data.get('description')
            )

            category = data.get('metadata', {}).get('category')
            self.register_template(name, template, category)


# Global prompt manager instance
_global_manager = None


def get_global_manager() -> PromptManager:
    """
    Get or create the global prompt manager

    Returns:
        Global PromptManager instance
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = PromptManager()
    return _global_manager

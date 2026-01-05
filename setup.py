"""
LightAgent Setup Configuration
"""
from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="lightagent",
    version="0.1.0",
    author="LightAgent Team",
    author_email="contact@lightagent.dev",
    description="A lightweight, modular Python framework for building AI agents",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lightagent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "openai": [
            "openai>=1.0.0",
        ],
        "anthropic": [
            "anthropic>=0.18.0",
        ],
        "rag": [
            "sentence-transformers>=2.2.0",
            "chromadb>=0.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lightagent=lightagent.cli:main",
        ],
    },
    include_package_data=True,
    keywords="agent ai llm autonomous multi-agent framework",
    project_urls={
        "Documentation": "https://github.com/yourusername/lightagent/wiki",
        "Source": "https://github.com/yourusername/lightagent",
        "Tracker": "https://github.com/yourusername/lightagent/issues",
    },
)

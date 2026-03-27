"""
Root conftest.py — ensure the project root is on sys.path so all domain
packages are importable regardless of how pytest is invoked.
pytest-django handles Django setup via DJANGO_SETTINGS_MODULE in pyproject.toml.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

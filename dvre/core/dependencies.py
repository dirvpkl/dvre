from fastapi import Request

from dvre.utils.engine_instance import get_resolve
from dvre.utils.types import ProjectManager as ResolveProjectManager


def get_project_manager(_: Request) -> ResolveProjectManager:
    return get_resolve().GetProjectManager()

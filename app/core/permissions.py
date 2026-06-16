# IMPORTANT: Do not check user roles inline.
# Always use these permission helpers so RBAC stays consistent and testable.

from app.core.authz import user_can, user_can_access_project
from app.models.project import Project
from app.models.user import User


def can_access_project(user: User, project: Project, action: str = "read") -> bool:
    return user_can_access_project(user, project, action)


def can(user: User, resource: str, action: str) -> bool:
    return user_can(user, resource, action)

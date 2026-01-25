import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectUserAssociation, ProjectUserRole
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

if TYPE_CHECKING:
    from app.models.user import User
    from app.schemas.user import UserRead


class ProjectNotFoundError(Exception):
    pass


async def list_projects_service(
    db: AsyncSession,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    user: User | None = None,
) -> tuple[list[ProjectRead], int]:
    """
    List projects with optional user-based filtering (page-based pagination for Web API).

    Args:
        db: Database session
        search: Optional search term for name/description
        page: Page number for pagination
        page_size: Number of items per page
        user: Optional user to filter projects by their access

    Returns:
        Tuple of (projects list, total count)
    """
    offset = (page - 1) * page_size
    return await _list_projects_core(
        db=db, search=search, offset=offset, limit=page_size, user=user
    )


async def list_projects_service_offset(
    db: AsyncSession,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
    user: User | None = None,
) -> tuple[list[ProjectRead], int]:
    """
    List projects with optional user-based filtering (offset-based pagination for Control API).

    Args:
        db: Database session
        search: Optional search term for name/description
        skip: Number of records to skip
        limit: Number of records to return
        user: Optional user to filter projects by their access

    Returns:
        Tuple of (projects list, total count)
    """
    return await _list_projects_core(
        db=db, search=search, offset=skip, limit=limit, user=user
    )


async def _list_projects_core(
    db: AsyncSession,
    search: str | None = None,
    offset: int = 0,
    limit: int = 20,
    user: User | None = None,
) -> tuple[list[ProjectRead], int]:
    """
    Core implementation for listing projects with offset-based pagination.

    Args:
        db: Database session
        search: Optional search term for name/description
        offset: Number of records to skip
        limit: Number of records to return
        user: Optional user to filter projects by their access

    Returns:
        Tuple of (projects list, total count)
    """
    stmt = (
        select(Project)
        .options(selectinload(Project.user_associations))
        .where(Project.archived_at.is_(None))
    )

    # Filter by user access if provided
    if user is not None:
        # Check if user is superuser or admin role
        # If so, don't filter by project associations (show all projects)
        from app.models.user import UserRole

        if not (user.is_superuser or user.role == UserRole.ADMIN):
            # Query user's project associations fresh from the database to avoid stale data
            user_associations_result = await db.execute(
                select(ProjectUserAssociation.project_id).where(
                    ProjectUserAssociation.user_id == user.id
                )
            )
            accessible_project_ids = [
                row[0] for row in user_associations_result.fetchall()
            ]

            if accessible_project_ids:
                stmt = stmt.where(Project.id.in_(accessible_project_ids))
            else:
                # User has no accessible projects, return empty result
                return [], 0

    if search:
        stmt = stmt.where(
            or_(
                Project.name.ilike(f"%{search}%"),
                Project.description.ilike(f"%{search}%"),
            )
        )
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = stmt.order_by(Project.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    projects = result.scalars().all()

    # Convert projects to schema format
    project_reads = []
    for project in projects:
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "private": project.private,
            "archived_at": project.archived_at,
            "notes": project.notes,
            "users": project.user_associations,  # Pass the associations to the validator
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        project_reads.append(ProjectRead.model_validate(project_data))

    return project_reads, total


async def get_project_service(project_id: int, db: AsyncSession) -> ProjectRead:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.user_associations))
        .where(Project.id == project_id, Project.archived_at.is_(None))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise ProjectNotFoundError(f"Project {project_id} not found")

    # Build the data dict with user associations for the validator
    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "private": project.private,
        "archived_at": project.archived_at,
        "notes": project.notes,
        "users": project.user_associations,  # Pass the associations to the validator
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    return ProjectRead.model_validate(project_data)


async def create_project_service(data: ProjectCreate, db: AsyncSession) -> ProjectRead:
    project = Project(
        name=data.name,
        description=data.description,
        private=data.private,
        archived_at=data.archived_at,
        notes=data.notes,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    # Eagerly load user_associations and users for serialization
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.user_associations).selectinload(
                ProjectUserAssociation.user
            )
        )
        .where(Project.id == project.id)
    )
    project_with_users = result.scalar_one()
    return ProjectRead.model_validate(project_with_users)


async def update_project_service(
    project_id: int, data: ProjectUpdate, db: AsyncSession
) -> ProjectRead:
    """
    Update a project with the given data.

    Args:
        project_id: The ID of the project to update
        data: The data to update the project with
        db: The database session

    Returns:
        The updated project

    Raises:
        ProjectNotFoundError: If the project is not found
    """
    project = await db.get(Project, project_id)
    if not project:
        raise ProjectNotFoundError(f"Project {project_id} not found")
    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "users":
            if value is not None:
                # Remove all current associations (async-safe)
                await db.execute(
                    delete(ProjectUserAssociation).where(
                        ProjectUserAssociation.project_id == project_id
                    )
                )
                # Add new associations
                for user_id in value:
                    uid = (
                        user_id
                        if isinstance(user_id, uuid.UUID)
                        else uuid.UUID(str(user_id))
                    )
                    assoc = ProjectUserAssociation(
                        project_id=project_id,
                        user_id=uid,
                        role=ProjectUserRole.member,
                    )
                    db.add(assoc)
        else:
            setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    # Eagerly load user_associations and users for serialization
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.user_associations).selectinload(
                ProjectUserAssociation.user
            )
        )
        .where(Project.id == project.id)
    )
    project_with_users = result.scalar_one()
    # Build users list as UUIDs for ProjectRead
    user_uuids = [assoc.user_id for assoc in project_with_users.user_associations]
    # Build ProjectRead dict
    project_dict = {
        "id": project_with_users.id,
        "name": project_with_users.name,
        "description": project_with_users.description,
        "private": project_with_users.private,
        "archived_at": project_with_users.archived_at,
        "notes": project_with_users.notes,
        "users": user_uuids,
        "created_at": project_with_users.created_at,
        "updated_at": project_with_users.updated_at,
    }
    return ProjectRead.model_validate(project_dict)


async def delete_project_service(project_id: int, db: AsyncSession) -> None:
    """
    Delete a project by ID.

    Args:
        project_id: The ID of the project to delete
        db: The database session

    Returns:
        None

    Raises:
        ProjectNotFoundError: If the project is not found
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ProjectNotFoundError(f"Project {project_id} not found")
    project.archived_at = datetime.now(UTC)
    await db.commit()


async def list_project_users_service(
    project_id: int, db: AsyncSession, offset: int = 0, limit: int = 20
) -> tuple[list[UserRead], int]:
    """
    List users associated with a specific project.

    Args:
        project_id: The ID of the project
        db: The database session
        offset: Number of records to skip
        limit: Number of records to return

    Returns:
        Tuple of (users list, total count)

    Raises:
        ProjectNotFoundError: If the project is not found
    """
    # First check if project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.archived_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise ProjectNotFoundError(f"Project {project_id} not found")

    # Import User model here to avoid circular imports
    from app.models.user import User
    from app.schemas.user import UserRead

    # Query users associated with the project
    stmt = (
        select(User)
        .join(ProjectUserAssociation)
        .where(ProjectUserAssociation.project_id == project_id)
        .order_by(User.name)
    )

    # Get total count
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    # Apply pagination
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    # Convert to UserRead schema
    user_reads = [UserRead.model_validate(user, from_attributes=True) for user in users]

    return user_reads, total

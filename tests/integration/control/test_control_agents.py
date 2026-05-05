"""Integration tests for Control API agents endpoints."""

from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectUserAssociation, ProjectUserRole
from app.models.user import User
from tests.factories.agent_factory import AgentFactory
from tests.factories.project_factory import ProjectFactory


@pytest.mark.asyncio
async def test_list_agents_project_scoping(
    api_key_client: tuple[AsyncClient, User, str],
    agent_factory: AgentFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Agents outside the caller's projects are not returned."""
    async_client, user, api_key = api_key_client

    project1 = await project_factory.create_async()
    project2 = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project1.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    accessible_agent = await agent_factory.create_async(host_name="accessible-agent")
    inaccessible_agent = await agent_factory.create_async(
        host_name="inaccessible-agent"
    )

    project1.agents.append(accessible_agent)
    project2.agents.append(inaccessible_agent)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/agents", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    host_names = {item["host_name"] for item in data["items"]}
    assert "accessible-agent" in host_names
    assert "inaccessible-agent" not in host_names
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_agents_search_and_total_are_project_scoped(
    api_key_client: tuple[AsyncClient, User, str],
    agent_factory: AgentFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Search and totals are applied after project scoping."""
    async_client, user, api_key = api_key_client

    project1 = await project_factory.create_async()
    project2 = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project1.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    accessible_match = await agent_factory.create_async(host_name="shared-match-a")
    accessible_other = await agent_factory.create_async(host_name="other-agent")
    inaccessible_match = await agent_factory.create_async(host_name="shared-match-b")

    project1.agents.extend([accessible_match, accessible_other])
    project2.agents.append(inaccessible_match)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/agents?search=shared-match", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 1
    assert [item["host_name"] for item in data["items"]] == ["shared-match-a"]


@pytest.mark.asyncio
async def test_list_agents_denies_user_without_project_access(
    api_key_client: tuple[AsyncClient, User, str],
) -> None:
    """Users with no project associations keep the existing denial behavior."""
    async_client, _user, api_key = api_key_client

    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/agents", headers=headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN

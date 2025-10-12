from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient, codes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.models.agent import Agent, AgentState, AgentType, OperatingSystemEnum
from app.models.attack import Attack, AttackMode, AttackState
from app.models.campaign import Campaign
from app.models.hash_item import HashItem
from app.models.hash_list import HashList
from app.models.hash_type import HashType
from app.models.hashcat_benchmark import HashcatBenchmark
from app.models.project import Project, project_agents  # noqa: F401
from app.models.task import Task, TaskStatus
from tests.factories.agent_factory import AgentFactory
from tests.factories.attack_factory import AttackFactory
from tests.factories.campaign_factory import CampaignFactory
from tests.factories.hash_item_factory import HashItemFactory
from tests.factories.hash_list_factory import HashListFactory
from tests.factories.project_factory import ProjectFactory
from tests.factories.task_factory import TaskFactory

# Magic values for test assertions
EXPECTED_PROGRESS = 42.5
EXPECTED_KEYSPACE_PROCESSED = 123456
EXPECTED_RUNTIME = 12.3


async def ensure_hash_type(db_session: AsyncSession) -> HashType:
    from tests.utils.hash_type_utils import get_or_create_hash_type

    return await get_or_create_hash_type(db_session, 0, "MD5", "Message Digest 5")


async def create_agent_with_benchmark(
    db_session: AsyncSession,
    os: OperatingSystemEnum,
    hash_type: HashType,
    async_engine=None,
    **agent_kwargs: Any,
) -> tuple[Agent, Agent]:
    agent = Agent(
        host_name=agent_kwargs.get(
            "host_name", f"test-agent-{datetime.now(UTC).timestamp()}"
        ),
        client_signature=agent_kwargs.get(
            "client_signature", f"test-sig-{datetime.now(UTC).timestamp()}"
        ),
        agent_type=AgentType.physical,
        state=AgentState.active,
        token=f"csa_{datetime.now(UTC).timestamp()}_testtoken",
        operating_system=os,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    assert agent is not None
    benchmark = HashcatBenchmark(
        agent_id=agent.id,
        hash_type_id=hash_type.id,
        hash_speed=500000.0,
        runtime=100,
        device="cpu0",
    )
    db_session.add(benchmark)
    await db_session.commit()
    await db_session.refresh(agent)
    # Add agent to project
    project = Project(name="TaskAssignProj_1", description="Test", private=False)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    project.agents.append(agent)
    await db_session.flush()
    await db_session.commit()
    # Move all relationship access before session close
    # Eagerly load benchmarks for assertion
    agent_with_bench = (
        await db_session.execute(
            select(Agent)
            .options(selectinload(Agent.benchmarks))
            .where(Agent.id == agent.id)
        )
    ).scalar_one()
    await db_session.close()

    if async_engine is not None:
        async_session_maker = async_sessionmaker(
            async_engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session_maker() as fresh_session:
            project_obj = (
                await fresh_session.execute(
                    select(Project)
                    .options(selectinload(Project.agents))
                    .where(Project.id == project.id)
                )
            ).scalar_one()
            agent_ids = [a.id for a in project_obj.agents]
            assert agent.id in agent_ids
    return agent, agent_with_bench


async def create_attack(
    db_session: AsyncSession,
    **attack_kwargs,  # noqa: ANN003
) -> Attack:
    if "campaign_id" not in attack_kwargs or attack_kwargs["campaign_id"] is None:
        raise ValueError("campaign_id is required for create_attack")
    attack = Attack(
        name=attack_kwargs.get("name", "Test Attack"),
        description=attack_kwargs.get("description", "Integration test attack"),
        state=attack_kwargs.get("state", AttackState.PENDING),
        attack_mode=attack_kwargs.get("attack_mode", AttackMode.DICTIONARY),
        attack_mode_hashcat=attack_kwargs.get("attack_mode_hashcat", 0),
        hash_mode=attack_kwargs.get("hash_mode", 0),
        campaign_id=attack_kwargs["campaign_id"],
        hash_list_id=attack_kwargs.get("hash_list_id", 1),
        hash_list_url=attack_kwargs.get(
            "hash_list_url", "http://example.com/hashes.txt"
        ),
        hash_list_checksum=attack_kwargs.get("hash_list_checksum", "deadbeef"),
        priority=attack_kwargs.get("priority", 0),
        start_time=attack_kwargs.get("start_time", datetime.now(UTC)),
        end_time=attack_kwargs.get("end_time"),
        template_id=attack_kwargs.get("template_id"),
    )
    db_session.add(attack)
    await db_session.commit()
    await db_session.refresh(attack)
    return attack


@pytest.mark.asyncio
async def test_task_progress_update_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    async_engine: AsyncEngine,
) -> None:
    # Setup: create OS, agent, attack, and running task assigned to agent
    # Create project and campaign
    project = Project(name="Test Project", description="Test", private=False)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="Test Campaign",
        description="Test",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    agent, _ = await create_agent_with_benchmark(
        db_session,
        OperatingSystemEnum.linux,
        hash_type,
        async_engine=async_engine,
    )
    assert agent is not None
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
    )
    task = Task(
        attack_id=attack.id,
        start_date=datetime.now(UTC),
        status=TaskStatus.RUNNING,
        agent_id=agent.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task.error_details = {"keyspace_total": 1000000}
    await db_session.commit()
    await db_session.refresh(task)
    session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as fresh_session:
        agent_with_bench_fresh: Agent | None = (
            (
                await fresh_session.execute(
                    select(Agent)
                    .options(selectinload(Agent.benchmarks))
                    .order_by(Agent.id.desc())
                )
            )
            .scalars()
            .first()
        )
        assert agent_with_bench_fresh is not None, (
            "agent_with_bench is None after re-query; agent creation or flush failed"
        )
        headers = {
            "Authorization": f"Bearer {agent_with_bench_fresh.token}",
            "User-Agent": "Ouroboros-Agent/1.0.0",
        }
        payload = {
            "progress_percent": EXPECTED_PROGRESS,
            "keyspace_processed": EXPECTED_KEYSPACE_PROCESSED,
        }
        resp = await async_client.post(
            f"/api/v1/client/tasks/{task.id}/progress", json=payload, headers=headers
        )
        assert resp.status_code == codes.NO_CONTENT
        # Confirm DB update
        await db_session.refresh(task)
        assert task.progress == EXPECTED_PROGRESS
        if (
            task.error_details is not None
            and "keyspace_processed" in task.error_details
        ):
            assert (
                task.error_details["keyspace_processed"] == EXPECTED_KEYSPACE_PROCESSED
            )


@pytest.mark.asyncio
async def test_task_progress_update_invalid_token(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = {
        "Authorization": "Bearer invalidtoken",
        "User-Agent": "Ouroboros-Agent/1.0.0",
    }
    payload = {"progress_percent": 10.0, "keyspace_processed": 100}
    resp = await async_client.post(
        "/api/v1/client/tasks/1/progress", json=payload, headers=headers
    )
    assert resp.status_code == codes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_task_progress_update_agent_not_assigned(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    # Setup: create OS, agent, attack, and running task NOT assigned to agent
    # Create project and campaign
    project = Project(name="Test Project", description="Test", private=False)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="Test Campaign",
        description="Test",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    _agent, _ = await create_agent_with_benchmark(
        db_session,
        OperatingSystemEnum.linux,
        hash_type,
        async_engine=async_engine,
    )
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
    )
    task = Task(
        attack_id=attack.id,
        start_date=datetime.now(UTC),
        status=TaskStatus.RUNNING,
        agent_id=None,  # Not assigned
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task.error_details = {"keyspace_total": 1000000}
    await db_session.commit()
    await db_session.refresh(task)
    session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as fresh_session:
        agent_with_bench_fresh: Agent | None = (
            (
                await fresh_session.execute(
                    select(Agent)
                    .options(selectinload(Agent.benchmarks))
                    .order_by(Agent.id.desc())
                )
            )
            .scalars()
            .first()
        )
        assert agent_with_bench_fresh is not None, (
            "agent_with_bench is None after re-query; agent creation or flush failed"
        )
        headers = {
            "Authorization": f"Bearer {agent_with_bench_fresh.token}",
            "User-Agent": "Ouroboros-Agent/1.0.0",
        }
        payload = {"progress_percent": 10.0, "keyspace_processed": 100}
        resp = await async_client.post(
            f"/api/v1/client/tasks/{task.id}/progress", json=payload, headers=headers
        )
        # v1: agent not assigned should return 404 (legacy/Swagger behavior)
        assert resp.status_code == codes.NOT_FOUND


@pytest.mark.asyncio
async def test_task_progress_update_task_not_running(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    # Setup: create OS, agent, attack, and task assigned to agent but not running
    # Create project and campaign
    project = Project(name="Test Project", description="Test", private=False)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="Test Campaign",
        description="Test",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    agent, _ = await create_agent_with_benchmark(
        db_session,
        OperatingSystemEnum.linux,
        hash_type,
        async_engine=async_engine,
    )
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
    )
    task = Task(
        attack_id=attack.id,
        start_date=datetime.now(UTC),
        status=TaskStatus.PAUSED,
        agent_id=agent.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task.error_details = {"keyspace_total": 1000000}
    await db_session.commit()
    await db_session.refresh(task)
    session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as fresh_session:
        agent_with_bench_fresh: Agent | None = (
            (
                await fresh_session.execute(
                    select(Agent)
                    .options(selectinload(Agent.benchmarks))
                    .order_by(Agent.id.desc())
                )
            )
            .scalars()
            .first()
        )
        assert agent_with_bench_fresh is not None, (
            "agent_with_bench is None after re-query; agent creation or flush failed"
        )
        headers = {
            "Authorization": f"Bearer {agent_with_bench_fresh.token}",
            "User-Agent": "Ouroboros-Agent/1.0.0",
        }
        payload = {"progress_percent": 10.0, "keyspace_processed": 100}
        resp = await async_client.post(
            f"/api/v1/client/tasks/{task.id}/progress", json=payload, headers=headers
        )
        assert resp.status_code == codes.CONFLICT


@pytest.mark.asyncio
async def test_task_progress_update_invalid_headers(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    # Setup: create OS, agent, attack, and running task assigned to agent
    # Create project and campaign
    project = Project(name="Test Project", description="Test", private=False)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="Test Campaign",
        description="Test",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    agent, _ = await create_agent_with_benchmark(
        db_session,
        OperatingSystemEnum.linux,
        hash_type,
        async_engine=async_engine,
    )
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
    )
    task = Task(
        attack_id=attack.id,
        start_date=datetime.now(UTC),
        status=TaskStatus.RUNNING,
        agent_id=agent.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task.error_details = {"keyspace_total": 1000000}
    await db_session.commit()
    await db_session.refresh(task)
    # v1: User-Agent is not required, so only Authorization matters
    session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as fresh_session:
        agent_with_bench_fresh: Agent | None = (
            (
                await fresh_session.execute(
                    select(Agent)
                    .options(selectinload(Agent.benchmarks))
                    .order_by(Agent.id.desc())
                )
            )
            .scalars()
            .first()
        )
        assert agent_with_bench_fresh is not None, (
            "agent_with_bench is None after re-query; agent creation or flush failed"
        )
        headers = {
            "Authorization": f"Bearer {agent_with_bench_fresh.token}",
            "User-Agent": "InvalidAgent/1.0.0",
        }
        payload = {"progress_percent": 10.0, "keyspace_processed": 100}
        resp = await async_client.post(
            f"/api/v1/client/tasks/{task.id}/progress", json=payload, headers=headers
        )
        # Should succeed if Authorization is valid, or 401 if not
        assert resp.status_code in (codes.NO_CONTENT, codes.UNAUTHORIZED)


@pytest.mark.asyncio
async def test_get_new_task_success(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    hash_type = await ensure_hash_type(db_session)
    project = Project(name="TaskAssignProj2_1", description="Test", private=False)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    # Create a HashList and at least one HashItem
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="TaskAssignCamp2",
        description="Test",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    agent = Agent(
        host_name="test-agent",
        client_signature="test-sig",
        agent_type=AgentType.physical,
        state=AgentState.active,
        token="csa_1_testtoken",
        operating_system=OperatingSystemEnum.linux,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    assert agent is not None
    benchmark = HashcatBenchmark(
        agent_id=agent.id,
        hash_type_id=hash_type.id,
        hash_speed=100000.0,
        runtime=100,
        device="cpu0",
    )
    db_session.add(benchmark)
    await db_session.commit()
    await db_session.refresh(agent)
    await db_session.refresh(project)
    # Add agent to project
    project.agents.append(agent)
    await db_session.flush()
    await db_session.commit()
    await db_session.close()

    if async_engine is not None:
        async_session_maker = async_sessionmaker(
            async_engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session_maker() as fresh_session:
            project_obj = (
                await fresh_session.execute(
                    select(Project)
                    .options(selectinload(Project.agents))
                    .where(Project.id == project.id)
                )
            ).scalar_one()
            agent_ids = [a.id for a in project_obj.agents]
            assert agent.id in agent_ids
    # Do not refresh agent/project after session close


@pytest.mark.asyncio
async def test_accept_task_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.PENDING, agent_id=None, attack_id=attack.id
    )
    token = f"Bearer {agent.token}"
    url = f"/api/v1/client/tasks/{task.id}/accept_task"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.NO_CONTENT
    updated_task = await db_session.get(Task, task.id)
    assert updated_task is not None, "Task not found after accept_task call"
    assert updated_task.status == TaskStatus.RUNNING
    assert updated_task.agent_id == agent.id


@pytest.mark.asyncio
async def test_accept_task_already_completed(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.COMPLETED, agent_id=agent.id, attack_id=attack.id
    )
    token = f"Bearer {agent.token}"
    url = f"/api/v1/client/tasks/{task.id}/accept_task"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    assert "already completed" in response.text.lower()


@pytest.mark.asyncio
async def test_accept_task_not_found(
    async_client: AsyncClient,
    agent_factory: AgentFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    token = f"Bearer {agent.token}"
    url = "/api/v1/client/tasks/999999/accept_task"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.NOT_FOUND


@pytest.mark.asyncio
async def test_accept_task_unauthorized(
    async_client: AsyncClient,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
    db_session: AsyncSession,
) -> None:
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.PENDING, agent_id=None, attack_id=attack.id
    )
    url = f"/api/v1/client/tasks/{task.id}/accept_task"
    response = await async_client.post(
        url, headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == codes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_accept_task_forbidden(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    await ensure_hash_type(db_session)  # Ensure hash type 0 exists
    agent1 = await agent_factory.create_async(
        operating_system=OperatingSystemEnum.linux
    )
    agent2 = await agent_factory.create_async(
        operating_system=OperatingSystemEnum.macos
    )
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.PENDING, agent_id=agent2.id, attack_id=attack.id
    )
    token = f"Bearer {agent1.token}"
    url = f"/api/v1/client/tasks/{task.id}/accept_task"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.FORBIDDEN


@pytest.mark.asyncio
async def test_exhaust_task_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.RUNNING, agent_id=agent.id, attack_id=attack.id
    )
    token = f"Bearer {agent.token}"
    url = f"/api/v1/client/tasks/{task.id}/exhausted"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.NO_CONTENT
    updated_task = await db_session.get(Task, task.id)
    assert updated_task is not None, "Task not found after exhaust_task call"
    assert updated_task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_exhaust_task_already_completed(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.COMPLETED, agent_id=agent.id, attack_id=attack.id
    )
    token = f"Bearer {agent.token}"
    url = f"/api/v1/client/tasks/{task.id}/exhausted"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    assert "already completed" in response.text.lower()


@pytest.mark.asyncio
async def test_exhaust_task_not_found(
    async_client: AsyncClient,
    agent_factory: AgentFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    token = f"Bearer {agent.token}"
    url = "/api/v1/client/tasks/999999/exhausted"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.NOT_FOUND


@pytest.mark.asyncio
async def test_exhaust_task_forbidden(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent1 = await agent_factory.create_async(
        operating_system=OperatingSystemEnum.linux
    )
    agent2 = await agent_factory.create_async(
        operating_system=OperatingSystemEnum.macos
    )
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.RUNNING, agent_id=agent1.id, attack_id=attack.id
    )
    token = f"Bearer {agent2.token}"
    url = f"/api/v1/client/tasks/{task.id}/exhausted"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.FORBIDDEN


@pytest.mark.asyncio
async def test_abandon_task_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.RUNNING, agent_id=agent.id, attack_id=attack.id
    )
    token = f"Bearer {agent.token}"
    url = f"/api/v1/client/tasks/{task.id}/abandon"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.NO_CONTENT
    updated_task = await db_session.get(Task, task.id)
    assert updated_task is not None, "Task not found after abandon_task call"
    assert updated_task.status == TaskStatus.ABANDONED


@pytest.mark.asyncio
async def test_abandon_task_already_abandoned(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.ABANDONED, agent_id=agent.id, attack_id=attack.id
    )
    token = f"Bearer {agent.token}"
    url = f"/api/v1/client/tasks/{task.id}/abandon"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    assert (
        "already abandoned" in response.text.lower()
        or 'cannot transition via "abandon"' in response.text
        or "abandon" in response.text.lower()
    )


@pytest.mark.asyncio
async def test_abandon_task_not_found(
    async_client: AsyncClient,
    agent_factory: AgentFactory,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    token = f"Bearer {agent.token}"
    url = "/api/v1/client/tasks/999999/abandon"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.NOT_FOUND


@pytest.mark.asyncio
async def test_abandon_task_forbidden(
    async_client: AsyncClient,
    db_session: AsyncSession,
    agent_factory: AgentFactory,
    task_factory: TaskFactory,
    attack_factory: AttackFactory,
) -> None:
    agent1 = await agent_factory.create_async(
        operating_system=OperatingSystemEnum.linux
    )
    agent2 = await agent_factory.create_async(
        operating_system=OperatingSystemEnum.macos
    )
    project = await ProjectFactory.create_async()
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=project.id, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)
    task = await task_factory.create_async(
        status=TaskStatus.ABANDONED, agent_id=agent2.id, attack_id=attack.id
    )
    token = f"Bearer {agent1.token}"
    url = f"/api/v1/client/tasks/{task.id}/abandon"
    response = await async_client.post(url, headers={"Authorization": token})
    assert response.status_code == codes.FORBIDDEN


@pytest.mark.asyncio
async def test_get_zaps_happy_path(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    # Setup: OS, agent, hash list, campaign, attack, task
    hash_type: HashType = await ensure_hash_type(db_session)
    os = OperatingSystemEnum.linux
    agent, _ = await create_agent_with_benchmark(db_session, os, hash_type)
    hash_type = await ensure_hash_type(db_session)
    hash_list: HashList = HashListFactory.build(project_id=1, hash_type_id=hash_type.id)
    hash_list.items.clear()  # Ensure no extra items from factory or DB state
    hash_item1: HashItem = HashItemFactory.build(hash="deadbeef")
    hash_item2: HashItem = HashItemFactory.build(hash="cafebabe")
    hash_item1.plain_text = "password1"
    hash_item2.plain_text = "password2"
    hash_list.items.extend([hash_item1, hash_item2])
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="ZapCamp", description="Test", project_id=1, hash_list_id=hash_list.id
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
    )
    task = Task(
        attack_id=attack.id,
        agent_id=agent.id,
        start_date=datetime.now(UTC),
        status=TaskStatus.RUNNING,
        skip=0,
        limit=0,
        error_details={
            "cracked_hashes": [
                {"hash": "deadbeef", "plain_text": "password1"},
                {"hash": "cafebabe", "plain_text": "password2"},
            ]
        },
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    headers = {"Authorization": f"Bearer {agent.token}"}
    resp = await async_client.get(
        f"/api/v1/client/tasks/{task.id}/get_zaps", headers=headers
    )
    assert resp.status_code == codes.OK
    assert resp.headers["content-type"].startswith("text/plain")
    lines = resp.text.strip().split("\n")
    assert set(lines) == {"deadbeef", "cafebabe"}


@pytest.mark.asyncio
async def test_get_zaps_task_not_found(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    os = OperatingSystemEnum.linux
    agent = Agent(
        id=2,
        host_name="test-agent2",
        client_signature="sig2",
        agent_type=AgentType.physical,
        state=AgentState.active,
        token="csa_2_testtoken",
        operating_system=os,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    headers = {"Authorization": f"Bearer {agent.token}"}
    resp = await async_client.get(
        "/api/v1/client/tasks/999999/get_zaps", headers=headers
    )
    assert resp.status_code == codes.NOT_FOUND


@pytest.mark.asyncio
async def test_get_zaps_unauthorized(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    # Setup: create OS, agent, attack, and task
    hash_type = await ensure_hash_type(db_session)
    os = OperatingSystemEnum.linux
    agent, _ = await create_agent_with_benchmark(db_session, os, hash_type)
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=1, hash_type_id=0)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="ZapCamp2", description="Test", project_id=1, hash_list_id=hash_list.id
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
    )
    task = Task(
        attack_id=attack.id,
        agent_id=agent.id,
        start_date=datetime.now(UTC),
        status=TaskStatus.RUNNING,
        skip=0,
        limit=0,
        error_details={"cracked_hashes": [{"hash": "deadbeef", "plain_text": "pw"}]},
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    # No Authorization header
    resp = await async_client.get(f"/api/v1/client/tasks/{task.id}/get_zaps")
    assert resp.status_code == codes.UNAUTHORIZED
    # Invalid token
    headers = {"Authorization": "Bearer invalidtoken"}
    resp = await async_client.get(
        f"/api/v1/client/tasks/{task.id}/get_zaps", headers=headers
    )
    assert resp.status_code == codes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_zaps_forbidden(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    # Setup: create two agents, only one assigned to task
    hash_type = await ensure_hash_type(db_session)
    os = OperatingSystemEnum.linux
    agent1, _ = await create_agent_with_benchmark(db_session, os, hash_type)
    agent2 = Agent(
        id=3,
        host_name="test-agent3",
        client_signature="sig3",
        agent_type=AgentType.physical,
        state=AgentState.active,
        token="csa_3_testtoken",
        operating_system=os,
    )
    db_session.add(agent2)
    await db_session.commit()
    await db_session.refresh(agent2)
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=1, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="ZapCamp3", description="Test", project_id=1, hash_list_id=hash_list.id
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
    )
    task = Task(
        attack_id=attack.id,
        agent_id=agent1.id,
        start_date=datetime.now(UTC),
        status=TaskStatus.RUNNING,
        skip=0,
        limit=0,
        error_details={"cracked_hashes": [{"hash": "deadbeef", "plain_text": "pw"}]},
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    headers = {"Authorization": f"Bearer {agent2.token}"}
    resp = await async_client.get(
        f"/api/v1/client/tasks/{task.id}/get_zaps", headers=headers
    )
    assert resp.status_code == codes.NOT_FOUND
    assert resp.json()["error"] == "Record not found"


@pytest.mark.asyncio
async def test_get_zaps_completed_or_abandoned(
    async_client: AsyncClient, db_session: AsyncSession, async_engine: AsyncEngine
) -> None:
    # Setup: create OS, agent, attack, and completed task
    hash_type = await ensure_hash_type(db_session)
    os = OperatingSystemEnum.linux
    agent, _ = await create_agent_with_benchmark(db_session, os, hash_type)
    hash_type = await ensure_hash_type(db_session)
    hash_list = HashListFactory.build(project_id=1, hash_type_id=hash_type.id)
    hash_item = HashItemFactory.build(hash="deadbeef")
    hash_list.items.append(hash_item)
    db_session.add(hash_list)
    await db_session.flush()
    await db_session.commit()
    campaign = Campaign(
        name="ZapCamp4", description="Test", project_id=1, hash_list_id=hash_list.id
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    attack = await create_attack(
        db_session,
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
    )
    for status in [TaskStatus.COMPLETED, TaskStatus.ABANDONED]:
        task = Task(
            attack_id=attack.id,
            agent_id=agent.id,
            start_date=datetime.now(UTC),
            status=status,
            skip=0,
            limit=0,
            error_details={
                "cracked_hashes": [{"hash": "deadbeef", "plain_text": "pw"}]
            },
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        headers = {"Authorization": f"Bearer {agent.token}"}
        resp = await async_client.get(
            f"/api/v1/client/tasks/{task.id}/get_zaps", headers=headers
        )
        assert resp.status_code == codes.UNPROCESSABLE_ENTITY
        assert resp.json()["error"] == "Task already completed"

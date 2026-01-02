import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentState, OperatingSystemEnum
from tests.factories.agent_factory import AgentFactory


@pytest.fixture(autouse=True)
def set_async_sessions(db_session: AsyncSession) -> None:
    AgentFactory.__async_session__ = db_session


@pytest.mark.asyncio
async def test_create_agent_minimal(
    agent_factory: AgentFactory,
    db_session: AsyncSession,
) -> None:
    agent = await agent_factory.create_async(operating_system=OperatingSystemEnum.linux)
    assert agent.id is not None
    assert agent.host_name.startswith("host")
    assert agent.state == AgentState.active


@pytest.mark.asyncio
async def test_agent_enum_enforcement(
    agent_factory: AgentFactory,
    db_session: AsyncSession,
) -> None:
    with pytest.raises(Exception) as exc_info:
        await agent_factory.create_async(
            operating_system=OperatingSystemEnum.linux, state="notastate"
        )
    assert "invalid input value for enum agentstate" in str(exc_info.value)


@pytest.mark.asyncio
async def test_agent_update_and_delete(
    agent_factory: AgentFactory,
    db_session: AsyncSession,
) -> None:
    agent = await agent_factory.create_async(
        operating_system=OperatingSystemEnum.macos, state=AgentState.stopped
    )
    agent_id = agent.id
    await db_session.delete(agent)
    await db_session.commit()
    result = await db_session.get(Agent, agent_id)
    assert result is None

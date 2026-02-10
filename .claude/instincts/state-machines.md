# Instinct: State Machine Pattern

**Confidence**: 95% **Source**: Control API implementation, app/core/state_machines.py **Category**: domain-logic

## Pattern

Campaign and Attack entities use state machines for lifecycle management.

### State Machine Structure

```python
class CampaignStateMachine:
    TRANSITIONS: ClassVar[dict[CampaignState, set[CampaignState]]] = {
        CampaignState.DRAFT: {CampaignState.ACTIVE, CampaignState.ARCHIVED},
        CampaignState.ACTIVE: {CampaignState.PAUSED, CampaignState.COMPLETED, ...},
        # ...
    }

    ACTIONS: ClassVar[dict[str, dict[CampaignState, CampaignState]]] = {
        "start": {CampaignState.DRAFT: CampaignState.ACTIVE},
        "pause": {CampaignState.ACTIVE: CampaignState.PAUSED},
        # ...
    }

    @classmethod
    def can_transition(cls, from_state: CampaignState, to_state: CampaignState) -> bool:
        """Check if transition is valid."""

    @classmethod
    def get_valid_actions(cls, from_state: CampaignState) -> list[str]:
        """Get all valid actions from a given state."""
```

### Usage in Services

```python
async def start_campaign(db: AsyncSession, campaign_id: int) -> Campaign:
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise CampaignNotFoundError()

    if not CampaignStateMachine.can_transition(campaign.state, CampaignState.ACTIVE):
        valid_actions = CampaignStateMachine.get_valid_actions(campaign.state)
        raise InvalidResourceStateError(
            f"Cannot start campaign from {campaign.state}",
            current_state=campaign.state.value,
            valid_actions=valid_actions,
        )

    campaign.state = CampaignState.ACTIVE
    await db.flush()
    return campaign
```

### Error Messages Include Valid Actions

When a state transition fails, always include what actions ARE valid:

```python
raise HTTPException(
    status_code=409, detail=f"Cannot perform action. Valid actions: {valid_actions}"
)
```

## Trigger

Activate when:

- Working with Campaign or Attack state changes
- Implementing lifecycle actions (start, pause, resume, etc.)
- Handling `InvalidResourceStateError`

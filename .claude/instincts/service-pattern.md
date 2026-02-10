# Instinct: Service Layer Pattern

**Confidence**: 95% **Source**: Codebase analysis, AGENTS.md **Category**: architecture

## Pattern

Business logic lives in service functions, not endpoints. Endpoints are thin wrappers.

### Service Function Naming

```python
# Standard CRUD operations
create_campaign(db, data) -> Campaign
get_campaign(db, id) -> Campaign | None
list_campaigns(db, filters) -> list[Campaign]
update_campaign(db, id, data) -> Campaign
delete_campaign(db, id) -> None

# Action operations
start_campaign(db, id) -> Campaign
pause_campaign(db, id) -> Campaign
```

### Exception Pattern

Services raise domain exceptions; endpoints translate to HTTP:

```python
# app/core/exceptions.py
class CampaignNotFoundError(Exception):
    """Raised when a campaign is not found."""

    pass


class InvalidResourceStateError(Exception):
    """Raised when a state transition is invalid."""

    def __init__(self, message: str, current_state: str, valid_actions: list[str]):
        self.current_state = current_state
        self.valid_actions = valid_actions
        super().__init__(message)


# app/api/v1/endpoints/web/campaigns.py
try:
    campaign = await start_campaign(db, campaign_id)
except CampaignNotFoundError:
    raise HTTPException(status_code=404, detail="Campaign not found")
except InvalidResourceStateError as e:
    raise HTTPException(
        status_code=409, detail=f"Cannot start: valid actions are {e.valid_actions}"
    )
```

### Database Session Pattern

```python
async def create_campaign(db: AsyncSession, data: CampaignCreate) -> Campaign:
    campaign = Campaign(**data.model_dump())
    db.add(campaign)
    await db.flush()  # Get ID without committing
    await db.refresh(campaign)
    return campaign
    # Commit happens in session context manager
```

## Trigger

Activate when:

- Creating new endpoints
- Adding business logic
- Handling errors in API layer
- Writing service functions

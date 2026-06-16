"""Event type constants for the event bus.

Centralizes event type strings to prevent typos and enable IDE autocomplete.
Use these constants when subscribing to or publishing events.

Example:
    from app.core.events import EventTypes, get_event_bus

    bus = get_event_bus()
    bus.subscribe(EventTypes.CAMPAIGN_CREATED, handler)
    await bus.publish(EventTypes.CAMPAIGN_CREATED, {"campaign_id": 123})
"""


class EventTypes:
    """Constants for event bus event types.

    Naming convention: ENTITY_ACTION (e.g., CAMPAIGN_CREATED)
    """

    # Campaign events
    CAMPAIGN_CREATED = "campaign.created"
    CAMPAIGN_UPDATED = "campaign.updated"
    CAMPAIGN_DELETED = "campaign.deleted"
    CAMPAIGN_STARTED = "campaign.started"
    CAMPAIGN_PAUSED = "campaign.paused"
    CAMPAIGN_COMPLETED = "campaign.completed"

    # Attack events
    ATTACK_CREATED = "attack.created"
    ATTACK_UPDATED = "attack.updated"
    ATTACK_DELETED = "attack.deleted"
    ATTACK_STARTED = "attack.started"
    ATTACK_COMPLETED = "attack.completed"

    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Agent events
    AGENT_REGISTERED = "agent.registered"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_OFFLINE = "agent.offline"
    AGENT_ERROR = "agent.error"

    # Hash events
    HASH_CRACKED = "hash.cracked"
    HASH_LIST_CREATED = "hash_list.created"
    HASH_LIST_UPDATED = "hash_list.updated"

    # Resource events
    RESOURCE_UPLOADED = "resource.uploaded"
    RESOURCE_DELETED = "resource.deleted"

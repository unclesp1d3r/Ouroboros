"""State machine classes for Campaign and Attack state transitions.

This module provides declarative state machines that encapsulate valid state transitions
and provide clear validation. The state machines distinguish between user-initiated actions
(start, stop, pause, resume, archive, unarchive) and system-driven transitions (automatic
completion, failure detection).

State Transition Diagram for Campaign:

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> ACTIVE: start
    ACTIVE --> PAUSED: pause
    PAUSED --> ACTIVE: resume
    ACTIVE --> COMPLETED: system_completes
    ACTIVE --> DRAFT: stop
    DRAFT --> ARCHIVED: archive
    ACTIVE --> ARCHIVED: archive
    PAUSED --> ARCHIVED: archive
    COMPLETED --> ARCHIVED: archive
    ARCHIVED --> DRAFT: unarchive
    ERROR --> DRAFT: reset
```

State Transition Diagram for Attack:

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> RUNNING: start
    RUNNING --> PAUSED: pause
    PAUSED --> RUNNING: resume
    RUNNING --> COMPLETED: system_completes
    RUNNING --> FAILED: system_fails
    RUNNING --> ABANDONED: abort
    PAUSED --> ABANDONED: abort
    FAILED --> PENDING: retry
    PENDING --> ABANDONED: abandon
    ABANDONED --> PENDING: reactivate
    COMPLETED --> [*]
```

Usage Example (Service Layer Integration):

```python
from app.core.state_machines import (
    CampaignStateMachine,
    InvalidStateTransitionError,
)
from app.core.control_exceptions import (
    InvalidStateTransitionProblem,
)


async def start_campaign_service(
    campaign_id: int,
    db: AsyncSession,
) -> CampaignRead:
    campaign = await get_campaign(
        campaign_id,
        db,
    )

    try:
        CampaignStateMachine.validate_transition(
            campaign.state,
            CampaignState.ACTIVE,
            action="start",
        )
    except InvalidStateTransitionError as e:
        # For Control API, convert to RFC9457
        raise InvalidStateTransitionProblem(
            from_state=e.from_state,
            to_state=e.to_state,
            action=e.action,
            entity_type="campaign",
        )

    campaign.state = CampaignState.ACTIVE
    await (
        db.commit()
    )
    return campaign
```

See also: Tech Plan spec for architectural context on state management.
"""

from typing import ClassVar

from app.models.attack import AttackState
from app.models.campaign import CampaignState


class InvalidStateTransitionError(Exception):
    """Exception raised when an invalid state transition is attempted.

    Attributes:
        from_state: The current state before the attempted transition.
        to_state: The target state of the attempted transition.
        action: Optional user action that triggered the transition attempt.
        message: Descriptive error message.
    """

    def __init__(
        self,
        from_state: CampaignState | AttackState,
        to_state: CampaignState | AttackState,
        action: str | None = None,
    ) -> None:
        self.from_state = from_state
        self.to_state = to_state
        self.action = action

        if action:
            self.message = (
                f"Cannot perform action '{action}': transition from "
                f"'{from_state.value}' to '{to_state.value}' is not allowed"
            )
        else:
            self.message = f"Invalid state transition from '{from_state.value}' to '{to_state.value}'"

        super().__init__(self.message)


class CampaignStateMachine:
    """State machine for Campaign state transitions.

    This class provides validation for campaign state transitions, supporting both
    user-initiated actions (start, stop, pause, resume, archive, unarchive) and
    system-driven transitions (automatic completion).

    Valid Transitions:
        - DRAFT → ACTIVE (start), ARCHIVED (archive)
        - ACTIVE → PAUSED (pause), DRAFT (stop), ARCHIVED (archive), COMPLETED (system)
        - PAUSED → ACTIVE (resume), ARCHIVED (archive)
        - COMPLETED → ARCHIVED (archive)
        - ARCHIVED → DRAFT (unarchive)
        - ERROR → DRAFT (reset)
    """

    # Mapping of each state to its valid target states
    TRANSITIONS: ClassVar[dict[CampaignState, list[CampaignState]]] = {
        CampaignState.DRAFT: [CampaignState.ACTIVE, CampaignState.ARCHIVED],
        CampaignState.ACTIVE: [
            CampaignState.PAUSED,
            CampaignState.DRAFT,
            CampaignState.ARCHIVED,
            CampaignState.COMPLETED,
        ],
        CampaignState.PAUSED: [CampaignState.ACTIVE, CampaignState.ARCHIVED],
        CampaignState.COMPLETED: [CampaignState.ARCHIVED],
        CampaignState.ARCHIVED: [CampaignState.DRAFT],
        CampaignState.ERROR: [CampaignState.DRAFT],
    }

    # Mapping of user actions to (from_state, to_state) pairs
    ACTIONS: ClassVar[dict[str, dict[CampaignState, CampaignState]]] = {
        "start": {CampaignState.DRAFT: CampaignState.ACTIVE},
        "stop": {CampaignState.ACTIVE: CampaignState.DRAFT},
        "pause": {CampaignState.ACTIVE: CampaignState.PAUSED},
        "resume": {CampaignState.PAUSED: CampaignState.ACTIVE},
        "archive": {
            CampaignState.DRAFT: CampaignState.ARCHIVED,
            CampaignState.ACTIVE: CampaignState.ARCHIVED,
            CampaignState.PAUSED: CampaignState.ARCHIVED,
            CampaignState.COMPLETED: CampaignState.ARCHIVED,
        },
        "unarchive": {CampaignState.ARCHIVED: CampaignState.DRAFT},
        "reset": {CampaignState.ERROR: CampaignState.DRAFT},
    }

    @classmethod
    def can_transition(cls, from_state: CampaignState, to_state: CampaignState) -> bool:
        """Check if a state transition is valid.

        Args:
            from_state: The current state.
            to_state: The target state.

        Returns:
            True if the transition is valid, False otherwise.
        """
        valid_targets = cls.TRANSITIONS.get(from_state, [])
        return to_state in valid_targets

    @classmethod
    def validate_transition(
        cls,
        from_state: CampaignState,
        to_state: CampaignState,
        action: str | None = None,
    ) -> None:
        """Validate a state transition and raise an error if invalid.

        Args:
            from_state: The current state.
            to_state: The target state.
            action: Optional user action that triggered the transition.

        Raises:
            InvalidStateTransitionError: If the transition is not valid.
        """
        if not cls.can_transition(from_state, to_state):
            raise InvalidStateTransitionError(from_state, to_state, action)

    @classmethod
    def validate_action(
        cls, current_state: CampaignState, action: str
    ) -> CampaignState:
        """Validate a user action against the current state.

        Args:
            current_state: The current campaign state.
            action: The user action to validate (start, stop, pause, resume, archive, unarchive, reset).

        Returns:
            The target state for the action.

        Raises:
            InvalidStateTransitionError: If the action is not valid for the current state.
        """
        action_map = cls.ACTIONS.get(action)
        if action_map is None:
            raise InvalidStateTransitionError(
                current_state,
                current_state,
                action=action,
            )

        target_state = action_map.get(current_state)
        if target_state is None:
            # Find any valid target for this action to provide in error
            valid_targets = list(action_map.values())
            target_for_error = valid_targets[0] if valid_targets else current_state
            raise InvalidStateTransitionError(current_state, target_for_error, action)

        return target_state

    @classmethod
    def get_valid_transitions(cls, from_state: CampaignState) -> list[CampaignState]:
        """Get all valid target states from a given state.

        Args:
            from_state: The current state.

        Returns:
            List of valid target states.
        """
        return cls.TRANSITIONS.get(from_state, [])


class AttackStateMachine:
    """State machine for Attack state transitions.

    This class provides validation for attack state transitions, supporting both
    user-initiated actions (start, pause, resume, retry, abandon, abort, reactivate)
    and system-driven transitions (completion, failure).

    Valid Transitions:
        - PENDING → RUNNING (start), ABANDONED (abandon)
        - RUNNING → PAUSED (pause), COMPLETED (system), FAILED (system), ABANDONED (abort)
        - PAUSED → RUNNING (resume), ABANDONED (abort)
        - COMPLETED → (terminal state, no outgoing transitions)
        - FAILED → PENDING (retry)
        - ABANDONED → PENDING (reactivate)
    """

    # Mapping of each state to its valid target states
    TRANSITIONS: ClassVar[dict[AttackState, list[AttackState]]] = {
        AttackState.PENDING: [AttackState.RUNNING, AttackState.ABANDONED],
        AttackState.RUNNING: [
            AttackState.PAUSED,
            AttackState.COMPLETED,
            AttackState.FAILED,
            AttackState.ABANDONED,
        ],
        AttackState.PAUSED: [AttackState.RUNNING, AttackState.ABANDONED],
        AttackState.COMPLETED: [],  # Terminal state
        AttackState.FAILED: [AttackState.PENDING],
        AttackState.ABANDONED: [AttackState.PENDING],
    }

    # Mapping of user actions to (from_state, to_state) pairs
    ACTIONS: ClassVar[dict[str, dict[AttackState, AttackState]]] = {
        "start": {AttackState.PENDING: AttackState.RUNNING},
        "pause": {AttackState.RUNNING: AttackState.PAUSED},
        "resume": {AttackState.PAUSED: AttackState.RUNNING},
        "retry": {AttackState.FAILED: AttackState.PENDING},
        "abandon": {AttackState.PENDING: AttackState.ABANDONED},
        "abort": {
            AttackState.RUNNING: AttackState.ABANDONED,
            AttackState.PAUSED: AttackState.ABANDONED,
        },
        "reactivate": {AttackState.ABANDONED: AttackState.PENDING},
    }

    @classmethod
    def can_transition(cls, from_state: AttackState, to_state: AttackState) -> bool:
        """Check if a state transition is valid.

        Args:
            from_state: The current state.
            to_state: The target state.

        Returns:
            True if the transition is valid, False otherwise.
        """
        valid_targets = cls.TRANSITIONS.get(from_state, [])
        return to_state in valid_targets

    @classmethod
    def validate_transition(
        cls,
        from_state: AttackState,
        to_state: AttackState,
        action: str | None = None,
    ) -> None:
        """Validate a state transition and raise an error if invalid.

        Args:
            from_state: The current state.
            to_state: The target state.
            action: Optional user action that triggered the transition.

        Raises:
            InvalidStateTransitionError: If the transition is not valid.
        """
        if not cls.can_transition(from_state, to_state):
            raise InvalidStateTransitionError(from_state, to_state, action)

    @classmethod
    def validate_action(cls, current_state: AttackState, action: str) -> AttackState:
        """Validate a user action against the current state.

        Args:
            current_state: The current attack state.
            action: The user action to validate (start, retry, abandon, reactivate).

        Returns:
            The target state for the action.

        Raises:
            InvalidStateTransitionError: If the action is not valid for the current state.
        """
        action_map = cls.ACTIONS.get(action)
        if action_map is None:
            raise InvalidStateTransitionError(
                current_state,
                current_state,
                action=action,
            )

        target_state = action_map.get(current_state)
        if target_state is None:
            # Find any valid target for this action to provide in error
            valid_targets = list(action_map.values())
            target_for_error = valid_targets[0] if valid_targets else current_state
            raise InvalidStateTransitionError(current_state, target_for_error, action)

        return target_state

    @classmethod
    def get_valid_transitions(cls, from_state: AttackState) -> list[AttackState]:
        """Get all valid target states from a given state.

        Args:
            from_state: The current state.

        Returns:
            List of valid target states.
        """
        return cls.TRANSITIONS.get(from_state, [])

    @classmethod
    def is_terminal_state(cls, state: AttackState) -> bool:
        """Check if a state is terminal (no outgoing transitions).

        Args:
            state: The state to check.

        Returns:
            True if the state is terminal, False otherwise.
        """
        return len(cls.TRANSITIONS.get(state, [])) == 0

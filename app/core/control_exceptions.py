"""Custom Control API exceptions using RFC9457 Problem Details format."""

from fastapi_problem.error import (
    BadRequestProblem,
    ConflictProblem,
    ForbiddenProblem,
    NotFoundProblem,
    ServerProblem,
)


class CampaignNotFoundError(NotFoundProblem):
    """Campaign not found error."""

    title = "Campaign Not Found"


class AttackNotFoundError(NotFoundProblem):
    """Attack not found error."""

    title = "Attack Not Found"


class AgentNotFoundError(NotFoundProblem):
    """Agent not found error."""

    title = "Agent Not Found"


class HashListNotFoundError(NotFoundProblem):
    """Hash list not found error."""

    title = "Hash List Not Found"


class HashItemNotFoundError(NotFoundProblem):
    """Hash item not found error."""

    title = "Hash Item Not Found"


class ResourceNotFoundError(NotFoundProblem):
    """Resource not found error."""

    title = "Resource Not Found"


class UserNotFoundError(NotFoundProblem):
    """User not found error."""

    title = "User Not Found"


class UserConflictError(ConflictProblem):
    """User creation conflict error."""

    title = "User Already Exists"


class ProjectNotFoundError(NotFoundProblem):
    """Project not found error."""

    title = "Project Not Found"


class TaskNotFoundError(NotFoundProblem):
    """Task not found error."""

    title = "Task Not Found"


class InvalidAttackConfigError(BadRequestProblem):
    """Invalid attack configuration error."""

    title = "Invalid Attack Configuration"


class InvalidHashFormatError(BadRequestProblem):
    """Invalid hash format error."""

    title = "Invalid Hash Format"


class InvalidResourceFormatError(BadRequestProblem):
    """Invalid resource format error."""

    title = "Invalid Resource Format"


class InsufficientPermissionsError(ForbiddenProblem):
    """Insufficient permissions error."""

    title = "Insufficient Permissions"


class ProjectAccessDeniedError(ForbiddenProblem):
    """Project access denied error."""

    title = "Project Access Denied"


class InternalServerError(ServerProblem):
    """Internal server error."""

    title = "Internal Server Error"


class InvalidResourceStateError(BadRequestProblem):
    """Invalid resource state error.

    Raised when an operation is attempted on a resource in an incompatible state,
    such as cancelling an already-uploaded resource. Returns HTTP 400 Bad Request.
    """

    title = "Invalid Resource State"


class InvalidStateTransitionError(ConflictProblem):
    """Invalid state transition error with RFC9457 Problem Details.

    Provides detailed error information for invalid state transitions.
    Can be initialized with just a detail message, or with full structured
    information for machine-readable error handling.

    Uses HTTP 409 Conflict since this represents a conflict between the current
    resource state and the requested action.
    """

    title = "Invalid State Transition"

    def __init__(
        self,
        detail: str | None = None,
        *,
        from_state: str | None = None,
        to_state: str | None = None,
        action: str | None = None,
        entity_type: str = "entity",
        valid_transitions: list[str] | None = None,
    ) -> None:
        """Initialize the InvalidStateTransitionError.

        Args:
            detail: Error detail message. If not provided, will be generated from other args.
            from_state: The current state value (optional if detail provided).
            to_state: The attempted target state value (optional if detail provided).
            action: Optional user action that triggered the transition attempt.
            entity_type: Type of entity (e.g., "campaign", "attack").
            valid_transitions: Optional list of valid target states from current state.
        """
        if detail is None:
            if action and from_state and to_state:
                detail = (
                    f"Cannot perform action '{action}' on {entity_type}: "
                    f"transition from '{from_state}' to '{to_state}' is not allowed."
                )
            elif from_state and to_state:
                detail = f"Invalid {entity_type} state transition from '{from_state}' to '{to_state}'."
            else:
                detail = "Invalid state transition."

            if valid_transitions:
                detail += (
                    f" Valid transitions from '{from_state}': {valid_transitions}."
                )

        super().__init__(detail=detail)

        # Set instance attributes for extension fields
        self.current_state = from_state
        self.attempted_state = to_state
        self.entity_type = entity_type
        self.action = action
        self.valid_transitions = valid_transitions


# Alias for backward compatibility
InvalidStateTransitionProblem = InvalidStateTransitionError

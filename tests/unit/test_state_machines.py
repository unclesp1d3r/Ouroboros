"""Comprehensive tests for state machine classes."""

import pytest

from app.core.control_exceptions import InvalidStateTransitionProblem
from app.core.state_machines import (
    AttackStateMachine,
    CampaignStateMachine,
    InvalidStateTransitionError,
)
from app.models.attack import AttackState
from app.models.campaign import CampaignState


class TestInvalidStateTransitionError:
    """Tests for InvalidStateTransitionError exception."""

    def test_error_with_action(self) -> None:
        """Test error message when action is provided."""
        error = InvalidStateTransitionError(
            CampaignState.DRAFT, CampaignState.PAUSED, action="pause"
        )
        assert error.from_state == CampaignState.DRAFT
        assert error.to_state == CampaignState.PAUSED
        assert error.action == "pause"
        assert "pause" in str(error)
        assert "draft" in str(error)
        assert "paused" in str(error)

    def test_error_without_action(self) -> None:
        """Test error message when no action is provided."""
        error = InvalidStateTransitionError(CampaignState.DRAFT, CampaignState.PAUSED)
        assert error.from_state == CampaignState.DRAFT
        assert error.to_state == CampaignState.PAUSED
        assert error.action is None
        assert "draft" in str(error)
        assert "paused" in str(error)


class TestCampaignStateMachine:
    """Tests for CampaignStateMachine."""

    # Valid transitions tests
    def test_valid_transition_draft_to_active(self) -> None:
        """Test valid transition from DRAFT to ACTIVE."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.DRAFT, CampaignState.ACTIVE
            )
            is True
        )
        # Should not raise
        CampaignStateMachine.validate_transition(
            CampaignState.DRAFT, CampaignState.ACTIVE, action="start"
        )

    def test_valid_transition_draft_to_archived(self) -> None:
        """Test valid transition from DRAFT to ARCHIVED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.DRAFT, CampaignState.ARCHIVED
            )
            is True
        )
        CampaignStateMachine.validate_transition(
            CampaignState.DRAFT, CampaignState.ARCHIVED, action="archive"
        )

    def test_valid_transition_active_to_paused(self) -> None:
        """Test valid transition from ACTIVE to PAUSED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.ACTIVE, CampaignState.PAUSED
            )
            is True
        )
        CampaignStateMachine.validate_transition(
            CampaignState.ACTIVE, CampaignState.PAUSED, action="pause"
        )

    def test_valid_transition_active_to_draft(self) -> None:
        """Test valid transition from ACTIVE to DRAFT (stop)."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.ACTIVE, CampaignState.DRAFT
            )
            is True
        )
        CampaignStateMachine.validate_transition(
            CampaignState.ACTIVE, CampaignState.DRAFT, action="stop"
        )

    def test_valid_transition_active_to_archived(self) -> None:
        """Test valid transition from ACTIVE to ARCHIVED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.ACTIVE, CampaignState.ARCHIVED
            )
            is True
        )

    def test_valid_transition_active_to_completed(self) -> None:
        """Test valid transition from ACTIVE to COMPLETED (system)."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.ACTIVE, CampaignState.COMPLETED
            )
            is True
        )

    def test_valid_transition_paused_to_active(self) -> None:
        """Test valid transition from PAUSED to ACTIVE (resume)."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.PAUSED, CampaignState.ACTIVE
            )
            is True
        )
        CampaignStateMachine.validate_transition(
            CampaignState.PAUSED, CampaignState.ACTIVE, action="resume"
        )

    def test_valid_transition_paused_to_archived(self) -> None:
        """Test valid transition from PAUSED to ARCHIVED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.PAUSED, CampaignState.ARCHIVED
            )
            is True
        )

    def test_valid_transition_completed_to_archived(self) -> None:
        """Test valid transition from COMPLETED to ARCHIVED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.COMPLETED, CampaignState.ARCHIVED
            )
            is True
        )

    def test_valid_transition_archived_to_draft(self) -> None:
        """Test valid transition from ARCHIVED to DRAFT (unarchive)."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.ARCHIVED, CampaignState.DRAFT
            )
            is True
        )
        CampaignStateMachine.validate_transition(
            CampaignState.ARCHIVED, CampaignState.DRAFT, action="unarchive"
        )

    def test_valid_transition_error_to_draft(self) -> None:
        """Test valid transition from ERROR to DRAFT (reset)."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.ERROR, CampaignState.DRAFT
            )
            is True
        )
        CampaignStateMachine.validate_transition(
            CampaignState.ERROR, CampaignState.DRAFT, action="reset"
        )

    # Invalid transitions tests
    def test_invalid_transition_draft_to_paused(self) -> None:
        """Test invalid transition from DRAFT to PAUSED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.DRAFT, CampaignState.PAUSED
            )
            is False
        )
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            CampaignStateMachine.validate_transition(
                CampaignState.DRAFT, CampaignState.PAUSED, action="pause"
            )
        assert "draft" in str(exc_info.value).lower()
        assert "paused" in str(exc_info.value).lower()

    def test_invalid_transition_draft_to_completed(self) -> None:
        """Test invalid transition from DRAFT to COMPLETED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.DRAFT, CampaignState.COMPLETED
            )
            is False
        )

    def test_invalid_transition_completed_to_active(self) -> None:
        """Test invalid transition from COMPLETED to ACTIVE."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.COMPLETED, CampaignState.ACTIVE
            )
            is False
        )
        with pytest.raises(InvalidStateTransitionError):
            CampaignStateMachine.validate_transition(
                CampaignState.COMPLETED, CampaignState.ACTIVE
            )

    def test_invalid_transition_archived_to_active(self) -> None:
        """Test invalid transition from ARCHIVED to ACTIVE."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.ARCHIVED, CampaignState.ACTIVE
            )
            is False
        )

    def test_invalid_transition_paused_to_completed(self) -> None:
        """Test invalid transition from PAUSED to COMPLETED."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.PAUSED, CampaignState.COMPLETED
            )
            is False
        )

    def test_invalid_transition_same_state(self) -> None:
        """Test invalid transition from same state to same state."""
        assert (
            CampaignStateMachine.can_transition(
                CampaignState.DRAFT, CampaignState.DRAFT
            )
            is False
        )
        with pytest.raises(InvalidStateTransitionError):
            CampaignStateMachine.validate_transition(
                CampaignState.DRAFT, CampaignState.DRAFT
            )

    # Action validation tests
    def test_validate_action_start(self) -> None:
        """Test start action from DRAFT."""
        target = CampaignStateMachine.validate_action(CampaignState.DRAFT, "start")
        assert target == CampaignState.ACTIVE

    def test_validate_action_stop(self) -> None:
        """Test stop action from ACTIVE."""
        target = CampaignStateMachine.validate_action(CampaignState.ACTIVE, "stop")
        assert target == CampaignState.DRAFT

    def test_validate_action_pause(self) -> None:
        """Test pause action from ACTIVE."""
        target = CampaignStateMachine.validate_action(CampaignState.ACTIVE, "pause")
        assert target == CampaignState.PAUSED

    def test_validate_action_resume(self) -> None:
        """Test resume action from PAUSED."""
        target = CampaignStateMachine.validate_action(CampaignState.PAUSED, "resume")
        assert target == CampaignState.ACTIVE

    def test_validate_action_archive_from_draft(self) -> None:
        """Test archive action from DRAFT."""
        target = CampaignStateMachine.validate_action(CampaignState.DRAFT, "archive")
        assert target == CampaignState.ARCHIVED

    def test_validate_action_archive_from_active(self) -> None:
        """Test archive action from ACTIVE."""
        target = CampaignStateMachine.validate_action(CampaignState.ACTIVE, "archive")
        assert target == CampaignState.ARCHIVED

    def test_validate_action_archive_from_paused(self) -> None:
        """Test archive action from PAUSED."""
        target = CampaignStateMachine.validate_action(CampaignState.PAUSED, "archive")
        assert target == CampaignState.ARCHIVED

    def test_validate_action_archive_from_completed(self) -> None:
        """Test archive action from COMPLETED."""
        target = CampaignStateMachine.validate_action(
            CampaignState.COMPLETED, "archive"
        )
        assert target == CampaignState.ARCHIVED

    def test_validate_action_unarchive(self) -> None:
        """Test unarchive action from ARCHIVED."""
        target = CampaignStateMachine.validate_action(
            CampaignState.ARCHIVED, "unarchive"
        )
        assert target == CampaignState.DRAFT

    def test_validate_action_reset(self) -> None:
        """Test reset action from ERROR."""
        target = CampaignStateMachine.validate_action(CampaignState.ERROR, "reset")
        assert target == CampaignState.DRAFT

    def test_validate_action_invalid_from_state(self) -> None:
        """Test action from invalid state raises error."""
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            CampaignStateMachine.validate_action(CampaignState.COMPLETED, "start")
        assert exc_info.value.action == "start"

    def test_validate_action_unknown_action(self) -> None:
        """Test unknown action raises error."""
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            CampaignStateMachine.validate_action(CampaignState.DRAFT, "unknown_action")
        assert exc_info.value.action == "unknown_action"

    # Get valid transitions tests
    def test_get_valid_transitions_draft(self) -> None:
        """Test getting valid transitions from DRAFT."""
        valid = CampaignStateMachine.get_valid_transitions(CampaignState.DRAFT)
        assert CampaignState.ACTIVE in valid
        assert CampaignState.ARCHIVED in valid
        assert len(valid) == 2

    def test_get_valid_transitions_active(self) -> None:
        """Test getting valid transitions from ACTIVE."""
        valid = CampaignStateMachine.get_valid_transitions(CampaignState.ACTIVE)
        assert CampaignState.PAUSED in valid
        assert CampaignState.DRAFT in valid
        assert CampaignState.ARCHIVED in valid
        assert CampaignState.COMPLETED in valid
        assert len(valid) == 4

    def test_get_valid_transitions_completed(self) -> None:
        """Test getting valid transitions from COMPLETED."""
        valid = CampaignStateMachine.get_valid_transitions(CampaignState.COMPLETED)
        assert CampaignState.ARCHIVED in valid
        assert len(valid) == 1


class TestAttackStateMachine:
    """Tests for AttackStateMachine."""

    # Valid transitions tests
    def test_valid_transition_pending_to_running(self) -> None:
        """Test valid transition from PENDING to RUNNING."""
        assert (
            AttackStateMachine.can_transition(AttackState.PENDING, AttackState.RUNNING)
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.PENDING, AttackState.RUNNING, action="start"
        )

    def test_valid_transition_pending_to_abandoned(self) -> None:
        """Test valid transition from PENDING to ABANDONED."""
        assert (
            AttackStateMachine.can_transition(
                AttackState.PENDING, AttackState.ABANDONED
            )
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.PENDING, AttackState.ABANDONED, action="abandon"
        )

    def test_valid_transition_running_to_paused(self) -> None:
        """Test valid transition from RUNNING to PAUSED."""
        assert (
            AttackStateMachine.can_transition(AttackState.RUNNING, AttackState.PAUSED)
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.RUNNING, AttackState.PAUSED, action="pause"
        )

    def test_valid_transition_paused_to_running(self) -> None:
        """Test valid transition from PAUSED to RUNNING (resume)."""
        assert (
            AttackStateMachine.can_transition(AttackState.PAUSED, AttackState.RUNNING)
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.PAUSED, AttackState.RUNNING, action="resume"
        )

    def test_valid_transition_running_to_completed(self) -> None:
        """Test valid transition from RUNNING to COMPLETED."""
        assert (
            AttackStateMachine.can_transition(
                AttackState.RUNNING, AttackState.COMPLETED
            )
            is True
        )

    def test_valid_transition_running_to_failed(self) -> None:
        """Test valid transition from RUNNING to FAILED."""
        assert (
            AttackStateMachine.can_transition(AttackState.RUNNING, AttackState.FAILED)
            is True
        )

    def test_valid_transition_failed_to_pending(self) -> None:
        """Test valid transition from FAILED to PENDING (retry)."""
        assert (
            AttackStateMachine.can_transition(AttackState.FAILED, AttackState.PENDING)
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.FAILED, AttackState.PENDING, action="retry"
        )

    def test_valid_transition_abandoned_to_pending(self) -> None:
        """Test valid transition from ABANDONED to PENDING (reactivate)."""
        assert (
            AttackStateMachine.can_transition(
                AttackState.ABANDONED, AttackState.PENDING
            )
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.ABANDONED, AttackState.PENDING, action="reactivate"
        )

    def test_valid_transition_running_to_abandoned(self) -> None:
        """Test valid transition from RUNNING to ABANDONED (abort)."""
        assert (
            AttackStateMachine.can_transition(
                AttackState.RUNNING, AttackState.ABANDONED
            )
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.RUNNING, AttackState.ABANDONED, action="abort"
        )

    def test_valid_transition_paused_to_abandoned(self) -> None:
        """Test valid transition from PAUSED to ABANDONED (abort)."""
        assert (
            AttackStateMachine.can_transition(AttackState.PAUSED, AttackState.ABANDONED)
            is True
        )
        AttackStateMachine.validate_transition(
            AttackState.PAUSED, AttackState.ABANDONED, action="abort"
        )

    # Invalid transitions tests
    def test_invalid_transition_pending_to_completed(self) -> None:
        """Test invalid transition from PENDING to COMPLETED."""
        assert (
            AttackStateMachine.can_transition(
                AttackState.PENDING, AttackState.COMPLETED
            )
            is False
        )
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_transition(
                AttackState.PENDING, AttackState.COMPLETED
            )

    def test_invalid_transition_completed_to_running(self) -> None:
        """Test invalid transition from COMPLETED to RUNNING."""
        assert (
            AttackStateMachine.can_transition(
                AttackState.COMPLETED, AttackState.RUNNING
            )
            is False
        )

    def test_invalid_transition_completed_to_pending(self) -> None:
        """Test invalid transition from COMPLETED to PENDING."""
        assert (
            AttackStateMachine.can_transition(
                AttackState.COMPLETED, AttackState.PENDING
            )
            is False
        )

    def test_invalid_transition_failed_to_running(self) -> None:
        """Test invalid transition from FAILED to RUNNING."""
        assert (
            AttackStateMachine.can_transition(AttackState.FAILED, AttackState.RUNNING)
            is False
        )

    def test_invalid_transition_same_state(self) -> None:
        """Test invalid transition from same state to same state."""
        assert (
            AttackStateMachine.can_transition(AttackState.PENDING, AttackState.PENDING)
            is False
        )

    def test_invalid_pause_from_pending(self) -> None:
        """Test that pause is invalid from PENDING state."""
        assert (
            AttackStateMachine.can_transition(AttackState.PENDING, AttackState.PAUSED)
            is False
        )
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.PENDING, "pause")

    def test_invalid_pause_from_completed(self) -> None:
        """Test that pause is invalid from COMPLETED (terminal) state."""
        assert (
            AttackStateMachine.can_transition(AttackState.COMPLETED, AttackState.PAUSED)
            is False
        )
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.COMPLETED, "pause")

    def test_invalid_pause_from_failed(self) -> None:
        """Test that pause is invalid from FAILED state."""
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.FAILED, "pause")

    def test_invalid_resume_from_pending(self) -> None:
        """Test that resume is invalid from PENDING state."""
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.PENDING, "resume")

    def test_invalid_resume_from_running(self) -> None:
        """Test that resume is invalid from RUNNING state (already running)."""
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.RUNNING, "resume")

    def test_invalid_resume_from_completed(self) -> None:
        """Test that resume is invalid from COMPLETED (terminal) state."""
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.COMPLETED, "resume")

    # Terminal state tests
    def test_completed_is_terminal(self) -> None:
        """Test that COMPLETED is a terminal state."""
        assert AttackStateMachine.is_terminal_state(AttackState.COMPLETED) is True

    def test_pending_is_not_terminal(self) -> None:
        """Test that PENDING is not a terminal state."""
        assert AttackStateMachine.is_terminal_state(AttackState.PENDING) is False

    def test_running_is_not_terminal(self) -> None:
        """Test that RUNNING is not a terminal state."""
        assert AttackStateMachine.is_terminal_state(AttackState.RUNNING) is False

    def test_failed_is_not_terminal(self) -> None:
        """Test that FAILED is not a terminal state."""
        assert AttackStateMachine.is_terminal_state(AttackState.FAILED) is False

    def test_abandoned_is_not_terminal(self) -> None:
        """Test that ABANDONED is not a terminal state."""
        assert AttackStateMachine.is_terminal_state(AttackState.ABANDONED) is False

    def test_paused_is_not_terminal(self) -> None:
        """Test that PAUSED is not a terminal state."""
        assert AttackStateMachine.is_terminal_state(AttackState.PAUSED) is False

    # Action validation tests
    def test_validate_action_start(self) -> None:
        """Test start action from PENDING."""
        target = AttackStateMachine.validate_action(AttackState.PENDING, "start")
        assert target == AttackState.RUNNING

    def test_validate_action_pause(self) -> None:
        """Test pause action from RUNNING."""
        target = AttackStateMachine.validate_action(AttackState.RUNNING, "pause")
        assert target == AttackState.PAUSED

    def test_validate_action_resume(self) -> None:
        """Test resume action from PAUSED."""
        target = AttackStateMachine.validate_action(AttackState.PAUSED, "resume")
        assert target == AttackState.RUNNING

    def test_validate_action_retry(self) -> None:
        """Test retry action from FAILED."""
        target = AttackStateMachine.validate_action(AttackState.FAILED, "retry")
        assert target == AttackState.PENDING

    def test_validate_action_abandon(self) -> None:
        """Test abandon action from PENDING."""
        target = AttackStateMachine.validate_action(AttackState.PENDING, "abandon")
        assert target == AttackState.ABANDONED

    def test_validate_action_reactivate(self) -> None:
        """Test reactivate action from ABANDONED."""
        target = AttackStateMachine.validate_action(AttackState.ABANDONED, "reactivate")
        assert target == AttackState.PENDING

    def test_validate_action_abort_from_running(self) -> None:
        """Test abort action from RUNNING."""
        target = AttackStateMachine.validate_action(AttackState.RUNNING, "abort")
        assert target == AttackState.ABANDONED

    def test_validate_action_abort_from_paused(self) -> None:
        """Test abort action from PAUSED."""
        target = AttackStateMachine.validate_action(AttackState.PAUSED, "abort")
        assert target == AttackState.ABANDONED

    def test_validate_action_abort_from_pending_invalid(self) -> None:
        """Test that abort is invalid from PENDING (use abandon instead)."""
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.PENDING, "abort")

    def test_validate_action_abort_from_completed_invalid(self) -> None:
        """Test that abort is invalid from COMPLETED (terminal state)."""
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.COMPLETED, "abort")

    def test_validate_action_invalid_from_state(self) -> None:
        """Test action from invalid state raises error."""
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            AttackStateMachine.validate_action(AttackState.RUNNING, "start")
        assert exc_info.value.action == "start"

    def test_validate_action_unknown_action(self) -> None:
        """Test unknown action raises error."""
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            AttackStateMachine.validate_action(AttackState.PENDING, "unknown_action")
        assert exc_info.value.action == "unknown_action"

    def test_validate_action_from_terminal_state(self) -> None:
        """Test action from terminal state raises error."""
        with pytest.raises(InvalidStateTransitionError):
            AttackStateMachine.validate_action(AttackState.COMPLETED, "start")

    # Get valid transitions tests
    def test_get_valid_transitions_pending(self) -> None:
        """Test getting valid transitions from PENDING."""
        valid = AttackStateMachine.get_valid_transitions(AttackState.PENDING)
        assert AttackState.RUNNING in valid
        assert AttackState.ABANDONED in valid
        assert len(valid) == 2

    def test_get_valid_transitions_running(self) -> None:
        """Test getting valid transitions from RUNNING."""
        valid = AttackStateMachine.get_valid_transitions(AttackState.RUNNING)
        assert AttackState.PAUSED in valid
        assert AttackState.COMPLETED in valid
        assert AttackState.FAILED in valid
        assert AttackState.ABANDONED in valid
        assert len(valid) == 4

    def test_get_valid_transitions_paused(self) -> None:
        """Test getting valid transitions from PAUSED."""
        valid = AttackStateMachine.get_valid_transitions(AttackState.PAUSED)
        assert AttackState.RUNNING in valid
        assert AttackState.ABANDONED in valid
        assert len(valid) == 2

    def test_get_valid_transitions_completed(self) -> None:
        """Test getting valid transitions from COMPLETED (terminal)."""
        valid = AttackStateMachine.get_valid_transitions(AttackState.COMPLETED)
        assert len(valid) == 0


class TestInvalidStateTransitionProblem:
    """Tests for InvalidStateTransitionProblem RFC9457 exception."""

    def test_problem_with_action(self) -> None:
        """Test problem creation with action."""
        problem = InvalidStateTransitionProblem(
            from_state="draft",
            to_state="paused",
            action="pause",
            entity_type="campaign",
        )
        assert problem.title == "Invalid State Transition"
        assert "pause" in problem.detail
        assert "draft" in problem.detail
        assert "paused" in problem.detail
        assert "campaign" in problem.detail
        assert problem.current_state == "draft"
        assert problem.attempted_state == "paused"
        assert problem.action == "pause"
        assert problem.entity_type == "campaign"

    def test_problem_without_action(self) -> None:
        """Test problem creation without action."""
        problem = InvalidStateTransitionProblem(
            from_state="pending",
            to_state="completed",
            entity_type="attack",
        )
        assert problem.title == "Invalid State Transition"
        assert "pending" in problem.detail
        assert "completed" in problem.detail
        assert "attack" in problem.detail
        assert problem.current_state == "pending"
        assert problem.attempted_state == "completed"
        assert problem.entity_type == "attack"

    def test_problem_with_valid_transitions(self) -> None:
        """Test problem creation with valid transitions list."""
        problem = InvalidStateTransitionProblem(
            from_state="draft",
            to_state="paused",
            action="pause",
            entity_type="campaign",
            valid_transitions=["active", "archived"],
        )
        assert "active" in problem.detail
        assert "archived" in problem.detail
        assert problem.valid_transitions == ["active", "archived"]

    def test_problem_default_entity_type(self) -> None:
        """Test problem with default entity type."""
        problem = InvalidStateTransitionProblem(
            from_state="draft",
            to_state="paused",
        )
        assert problem.entity_type == "entity"


class TestStateMachineIntegration:
    """Integration tests for state machine usage patterns."""

    def test_campaign_full_lifecycle(self) -> None:
        """Test a campaign going through its full lifecycle."""
        state = CampaignState.DRAFT

        # Start campaign
        assert CampaignStateMachine.can_transition(state, CampaignState.ACTIVE)
        state = CampaignState.ACTIVE

        # Pause campaign
        assert CampaignStateMachine.can_transition(state, CampaignState.PAUSED)
        state = CampaignState.PAUSED

        # Resume campaign
        assert CampaignStateMachine.can_transition(state, CampaignState.ACTIVE)
        state = CampaignState.ACTIVE

        # Complete campaign (system transition)
        assert CampaignStateMachine.can_transition(state, CampaignState.COMPLETED)
        state = CampaignState.COMPLETED

        # Archive campaign
        assert CampaignStateMachine.can_transition(state, CampaignState.ARCHIVED)
        state = CampaignState.ARCHIVED

        # Unarchive campaign
        assert CampaignStateMachine.can_transition(state, CampaignState.DRAFT)
        state = CampaignState.DRAFT

    def test_attack_full_lifecycle(self) -> None:
        """Test an attack going through its full lifecycle."""
        state = AttackState.PENDING

        # Start attack
        assert AttackStateMachine.can_transition(state, AttackState.RUNNING)
        state = AttackState.RUNNING

        # Attack completes
        assert AttackStateMachine.can_transition(state, AttackState.COMPLETED)
        state = AttackState.COMPLETED

        # Cannot transition from terminal state
        assert AttackStateMachine.is_terminal_state(state)
        assert len(AttackStateMachine.get_valid_transitions(state)) == 0

    def test_attack_pause_resume_lifecycle(self) -> None:
        """Test an attack being paused and resumed."""
        state = AttackState.PENDING

        # Start attack
        assert AttackStateMachine.can_transition(state, AttackState.RUNNING)
        state = AttackState.RUNNING

        # Pause attack
        assert AttackStateMachine.can_transition(state, AttackState.PAUSED)
        state = AttackState.PAUSED

        # Cannot pause again from paused
        assert not AttackStateMachine.can_transition(state, AttackState.PAUSED)

        # Resume attack
        assert AttackStateMachine.can_transition(state, AttackState.RUNNING)
        state = AttackState.RUNNING

        # Attack completes
        assert AttackStateMachine.can_transition(state, AttackState.COMPLETED)
        state = AttackState.COMPLETED

    def test_attack_failure_retry_cycle(self) -> None:
        """Test an attack failing and being retried."""
        state = AttackState.PENDING

        # Start attack
        state = AttackState.RUNNING

        # Attack fails
        assert AttackStateMachine.can_transition(state, AttackState.FAILED)
        state = AttackState.FAILED

        # Retry attack
        assert AttackStateMachine.can_transition(state, AttackState.PENDING)
        state = AttackState.PENDING

        # Start again
        assert AttackStateMachine.can_transition(state, AttackState.RUNNING)

    def test_error_conversion_to_rfc9457(self) -> None:
        """Test converting InvalidStateTransitionError to RFC9457 problem."""
        try:
            CampaignStateMachine.validate_transition(
                CampaignState.DRAFT, CampaignState.PAUSED, action="pause"
            )
        except InvalidStateTransitionError as e:
            problem = InvalidStateTransitionProblem(
                from_state=e.from_state.value,
                to_state=e.to_state.value,
                action=e.action,
                entity_type="campaign",
                valid_transitions=[
                    s.value
                    for s in CampaignStateMachine.get_valid_transitions(e.from_state)
                ],
            )
            assert problem.current_state == "draft"
            assert problem.attempted_state == "paused"
            assert problem.action == "pause"
            assert "active" in problem.valid_transitions
            assert "archived" in problem.valid_transitions

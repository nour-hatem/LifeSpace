"""Overdue computation (BUSINESS_RULES 4.7, ADR 0001 item 9)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from lifespace.domain.deadline import is_deadline_passed
from lifespace.domain.task import Task, TaskStatus
from lifespace.domain.time import ensure_aware


def is_overdue(task: Task, now: datetime, tz: ZoneInfo) -> bool:
    """Return whether ``task`` is overdue at ``now`` in ``tz`` (ADR 0001 item 9).

    A task is overdue only when it has a deadline, its status is not COMPLETED
    or CANCELED, and the deadline has passed (BUSINESS_RULES 4.7). Overdue is
    computed, never stored, and never a status.
    """
    ensure_aware(now, field="now")
    if task.deadline is None:
        return False
    if task.status is TaskStatus.COMPLETED or task.status is TaskStatus.CANCELED:
        return False
    return is_deadline_passed(task.deadline, now, tz)

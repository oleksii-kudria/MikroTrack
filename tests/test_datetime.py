from __future__ import annotations

from datetime import UTC, datetime

from app.persistence import (
    _idle_timeout_exceeded,
    _parse_snapshot_timestamp,
    configure_persistence,
)


def test_parse_snapshot_timestamp_handles_naive_aware_and_z() -> None:
    expected = datetime(2026, 4, 11, 12, 0, 0, tzinfo=UTC)

    naive = _parse_snapshot_timestamp("2026-04-11T12:00:00")
    aware = _parse_snapshot_timestamp("2026-04-11T12:00:00+00:00")
    zulu = _parse_snapshot_timestamp("2026-04-11T12:00:00Z")

    assert naive == expected
    assert aware == expected
    assert zulu == expected


def test_idle_timeout_exceeded_is_stable_for_mixed_snapshot_formats() -> None:
    configure_persistence("/tmp", retention_days=7, idle_timeout_seconds=900)
    now = datetime(2026, 4, 11, 12, 20, 0, tzinfo=UTC)

    assert (
        _idle_timeout_exceeded(previous={"idle_since": "2026-04-11T12:00:00"}, now=now)
        is True
    )
    assert (
        _idle_timeout_exceeded(
            previous={"idle_since": "2026-04-11T12:00:00+00:00"}, now=now
        )
        is True
    )
    assert (
        _idle_timeout_exceeded(previous={"idle_since": "2026-04-11T12:00:00Z"}, now=now)
        is True
    )


def test_idle_timeout_exceeded_falls_back_to_state_changed_at() -> None:
    configure_persistence("/tmp", retention_days=7, idle_timeout_seconds=900)
    now = datetime(2026, 4, 11, 12, 20, 0, tzinfo=UTC)

    assert (
        _idle_timeout_exceeded(
            previous={"state_changed_at": "2026-04-11T12:00:00Z"}, now=now
        )
        is True
    )

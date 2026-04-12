from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.persistence import _apply_stable_timestamps, configure_persistence


FIXED_NOW = "2026-04-11T12:00:00+00:00"


def _write_previous_snapshot(tmp: str, device: dict[str, object]) -> None:
    Path(tmp, "2026-04-11T11-59-00.json").write_text(json.dumps([device]), encoding="utf-8")


def test_state_transition_online_to_idle_updates_idle_since() -> None:
    with TemporaryDirectory() as tmp:
        configure_persistence(tmp, retention_days=7)
        _write_previous_snapshot(
            tmp,
            {
                "mac_address": "AA:BB:CC:DD:EE:10",
                "fused_state": "online",
                "state_changed_at": "2026-04-11T11:00:00+00:00",
                "online_since": "2026-04-11T11:00:00+00:00",
                "idle_since": None,
                "offline_since": None,
            },
        )

        with patch("app.persistence._iso_timestamp", return_value=FIXED_NOW):
            updated = _apply_stable_timestamps(
                [{"mac_address": "AA:BB:CC:DD:EE:10", "fused_state": "idle"}]
            )[0]

    assert updated["state_changed_at"] == FIXED_NOW
    assert updated["online_since"] == "2026-04-11T11:00:00+00:00"
    assert updated["idle_since"] == FIXED_NOW
    assert updated["offline_since"] is None


def test_state_transition_idle_to_offline_sets_offline_since() -> None:
    with TemporaryDirectory() as tmp:
        configure_persistence(tmp, retention_days=7)
        _write_previous_snapshot(
            tmp,
            {
                "mac_address": "AA:BB:CC:DD:EE:11",
                "fused_state": "idle",
                "state_changed_at": "2026-04-11T11:30:00+00:00",
                "online_since": "2026-04-11T10:00:00+00:00",
                "idle_since": "2026-04-11T11:30:00+00:00",
                "offline_since": None,
            },
        )

        with patch("app.persistence._iso_timestamp", return_value=FIXED_NOW):
            updated = _apply_stable_timestamps(
                [{"mac_address": "AA:BB:CC:DD:EE:11", "fused_state": "offline"}]
            )[0]

    assert updated["state_changed_at"] == FIXED_NOW
    assert updated["online_since"] is None
    assert updated["idle_since"] is None
    assert updated["offline_since"] == FIXED_NOW


def test_state_transition_online_to_offline_sets_offline_since() -> None:
    with TemporaryDirectory() as tmp:
        configure_persistence(tmp, retention_days=7)
        _write_previous_snapshot(
            tmp,
            {
                "mac_address": "AA:BB:CC:DD:EE:14",
                "fused_state": "online",
                "state_changed_at": "2026-04-11T11:20:00+00:00",
                "online_since": "2026-04-11T11:00:00+00:00",
                "idle_since": None,
                "offline_since": None,
            },
        )

        with patch("app.persistence._iso_timestamp", return_value=FIXED_NOW):
            updated = _apply_stable_timestamps(
                [{"mac_address": "AA:BB:CC:DD:EE:14", "fused_state": "offline"}]
            )[0]

    assert updated["state_changed_at"] == FIXED_NOW
    assert updated["online_since"] is None
    assert updated["idle_since"] is None
    assert updated["offline_since"] == FIXED_NOW


def test_state_transition_offline_to_online_starts_new_session() -> None:
    with TemporaryDirectory() as tmp:
        configure_persistence(tmp, retention_days=7)
        _write_previous_snapshot(
            tmp,
            {
                "mac_address": "AA:BB:CC:DD:EE:12",
                "fused_state": "offline",
                "state_changed_at": "2026-04-11T11:20:00+00:00",
                "online_since": None,
                "idle_since": None,
                "offline_since": "2026-04-11T11:20:00+00:00",
            },
        )

        current = {
            "mac_address": "AA:BB:CC:DD:EE:12",
            "fused_state": "online",
            "arp_status": "reachable",
            "bridge_host_present": False,
        }
        with patch("app.persistence._iso_timestamp", return_value=FIXED_NOW):
            updated = _apply_stable_timestamps([current])[0]

    assert updated["state_changed_at"] == FIXED_NOW
    assert updated["online_since"] == FIXED_NOW
    assert updated["idle_since"] is None
    assert updated["offline_since"] is None


def test_offline_device_preserves_last_known_fields_when_current_data_missing() -> None:
    with TemporaryDirectory() as tmp:
        configure_persistence(tmp, retention_days=7)
        _write_previous_snapshot(
            tmp,
            {
                "mac_address": "AA:BB:CC:DD:EE:13",
                "fused_state": "offline",
                "ip_address": "192.168.88.130",
                "host_name": "known-host",
                "last_known_ip": "192.168.88.130",
                "last_known_hostname": "known-host",
                "offline_since": "2026-04-11T11:00:00+00:00",
            },
        )

        with patch("app.persistence._iso_timestamp", return_value=FIXED_NOW):
            updated = _apply_stable_timestamps(
                [
                    {
                        "mac_address": "AA:BB:CC:DD:EE:13",
                        "fused_state": "offline",
                        "ip_address": "",
                        "host_name": "",
                    }
                ]
            )[0]

    assert updated["ip_address"] == "192.168.88.130"
    assert updated["last_known_ip"] == "192.168.88.130"
    assert updated["ip_is_stale"] is True
    assert updated["data_is_stale"] is True

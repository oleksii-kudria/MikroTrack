from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from ipaddress import ip_address
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from app.arp_logic import fused_device_state, normalize_arp_status

app = FastAPI(title="MikroTrack API", version="0.1.0")
logger = logging.getLogger("mikrotrack.api")


def _persistence_path() -> Path:
    return Path(os.getenv("PERSISTENCE_PATH", "/data/snapshots"))


def _snapshot_files() -> list[Path]:
    path = _persistence_path()
    if not path.exists():
        return []
    return sorted(path.glob("*.json"), reverse=True)


def _idle_timeout_seconds() -> int:
    raw = os.getenv("IDLE_TIMEOUT_SECONDS", "900")
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return 900
    return parsed if parsed > 0 else 900


def _load_latest_snapshot() -> list[dict[str, Any]] | None:
    files = _snapshot_files()
    if not files:
        return None

    latest = files[0]
    with latest.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise HTTPException(status_code=500, detail="Invalid snapshot format")

    return payload


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _presence_state(state: str | None) -> str:
    normalized = str(state or "").strip().lower()
    return normalized if normalized in {"online", "idle", "offline"} else "unknown"


def _sanitize_presence_transition(previous_state: str, current_state: str) -> tuple[str, str]:
    prev = _presence_state(previous_state)
    curr = _presence_state(current_state)
    if prev == "offline" and curr == "idle":
        curr = "online"
    return prev, curr


def _extract_state_transition(event: dict[str, Any]) -> tuple[str, str] | None:
    event_type = str(event.get("event_type", "")).strip().lower()

    if event_type == "state_changed":
        old_state = str(event.get("old_state", event.get("old_value", "")))
        new_state = str(event.get("new_state", event.get("new_value", "")))
        prev, curr = _sanitize_presence_transition(old_state, new_state)
        if prev == "unknown" or curr == "unknown":
            return None
        return prev, curr

    if event_type == "arp_state_changed":
        old_state = str(event.get("old_state", event.get("old_value", "")))
        new_state = str(event.get("new_state", event.get("new_value", "")))
        prev, curr = _sanitize_presence_transition(old_state, new_state)
        if prev == "unknown" or curr == "unknown":
            return None
        return prev, curr

    return None


def _read_events(limit: int = 10000) -> list[dict[str, Any]]:
    events_file = _persistence_path() / "events.jsonl"
    if not events_file.exists():
        return []

    lines = events_file.read_text(encoding="utf-8").splitlines()[-max(1, min(limit, 20000)):]
    items: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(payload, dict):
            items.append(payload)

    return items


def _comment_text(dhcp_comment: str, arp_comment: str) -> str:
    dhcp_text = (dhcp_comment or "").strip()
    arp_text = (arp_comment or "").strip()

    if dhcp_text and arp_text:
        if dhcp_text == arp_text:
            return f"dhcp arp: {dhcp_text}"
        return f"dhcp: {dhcp_text}\narp: {arp_text}"
    if dhcp_text:
        return f"dhcp: {dhcp_text}"
    if arp_text:
        return f"arp: {arp_text}"
    return "-"


def _comment_badge_label(dhcp_comment: str, arp_comment: str) -> str:
    dhcp_text = (dhcp_comment or "").strip()
    arp_text = (arp_comment or "").strip()

    if dhcp_text and arp_text:
        if dhcp_text == arp_text:
            return f"DHCP+ARP: {dhcp_text}"
        return f"DHCP: {dhcp_text} | ARP: {arp_text}"
    if dhcp_text:
        return f"DHCP: {dhcp_text}"
    if arp_text:
        return f"ARP: {arp_text}"
    return "-"


def _is_link_local(ip_raw: str) -> bool:
    ip_text = str(ip_raw or "").strip()
    if not ip_text:
        return False
    try:
        return ip_address(ip_text).is_link_local
    except ValueError:
        return False


def _device_state(device: dict[str, Any]) -> str:
    arp_status_raw = normalize_arp_status(device.get("arp_status", ""))
    arp_flags = device.get("arp_flags") if isinstance(device.get("arp_flags"), dict) else {}
    bridge_host_present = bool(device.get("bridge_host_present", False))
    evidence = device.get("evidence")
    if not bridge_host_present and isinstance(evidence, dict):
        bridge_host_present = bool(evidence.get("bridge_host_present", False))
    dhcp_status = str(device.get("dhcp_status", "")).strip().lower()

    if bool(arp_flags.get("disabled")) or bool(arp_flags.get("invalid")):
        return "offline"

    if arp_status_raw and arp_status_raw != "unknown":
        return fused_device_state(arp_status_raw, bridge_host_present)

    if bridge_host_present:
        return "online"

    # Fallback path when ARP status is absent in historical/legacy snapshots.
    if dhcp_status == "bound":
        return "unknown"

    return "offline"


def _dhcp_flag(has_dhcp_lease: bool, dhcp_flags: dict[str, Any], dhcp_is_dynamic: bool | None = None) -> str | None:
    if not has_dhcp_lease:
        return None

    if dhcp_is_dynamic is not None:
        return "D" if dhcp_is_dynamic else "S"
    return "D" if bool(dhcp_flags.get("dynamic")) else "S"


def _arp_flag(has_arp_entry: bool, arp_flags: dict[str, Any]) -> str | None:
    if not has_arp_entry:
        return None

    base_flag = "D" if bool(arp_flags.get("dynamic")) else "S"
    if bool(arp_flags.get("complete")):
        return f"{base_flag}C"
    return base_flag


def _resolve_api_state(
    *,
    mac: str,
    offline_since: datetime | None,
    online_since: datetime | None,
    idle_since: datetime | None,
    bridge_host_present: bool,
    now: datetime,
    idle_timeout_seconds: int,
    fallback_state: str,
) -> str:
    if bridge_host_present:
        return "online"

    if isinstance(offline_since, datetime):
        if fallback_state == "idle":
            logger.info("API state mapping: prevented idle override for MAC %s", mac)
        logger.info("API state mapping: resolved offline for MAC %s", mac)
        return "offline"
    if (
        isinstance(idle_since, datetime)
        and not bridge_host_present
        and int((now - idle_since).total_seconds()) >= idle_timeout_seconds
    ):
        logger.info(
            "API idle timeout exceeded for MAC %s, resolving state to offline",
            mac,
        )
        return "offline"
    if isinstance(idle_since, datetime) and (
        not isinstance(online_since, datetime) or idle_since >= online_since
    ):
        return "idle"
    if isinstance(online_since, datetime):
        return "online"
    return "unknown"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/snapshots")
def list_snapshots(limit: int = 20) -> dict[str, object]:
    files = _snapshot_files()[: max(1, min(limit, 200))]
    return {
        "items": [
            {"filename": file.name, "mtime": file.stat().st_mtime, "size": file.stat().st_size}
            for file in files
        ]
    }


@app.get("/api/v1/snapshots/latest")
def latest_snapshot() -> dict[str, object]:
    files = _snapshot_files()
    if not files:
        raise HTTPException(status_code=404, detail="No snapshots found")

    with files[0].open(encoding="utf-8") as handle:
        payload = json.load(handle)

    return {"filename": files[0].name, "devices": payload}


@app.get("/api/v1/events")
def list_events(limit: int = 200) -> dict[str, object]:
    events_file = _persistence_path() / "events.jsonl"
    if not events_file.exists():
        return {"items": []}

    capped_limit = max(1, min(limit, 2000))
    lines = events_file.read_text(encoding="utf-8").splitlines()[-capped_limit:]
    items: list[dict[str, object]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return {"items": items}


@app.get("/api/devices")
@app.get("/api/v1/devices")
def list_devices() -> dict[str, object]:
    snapshot = _load_latest_snapshot()
    if not isinstance(snapshot, list):
        return {"items": []}

    now = datetime.now(UTC)
    idle_timeout_seconds = _idle_timeout_seconds()
    events = _read_events()
    session_by_mac: dict[str, dict[str, datetime | None]] = {}

    sorted_events = sorted(events, key=lambda event: _parse_ts(str(event.get("timestamp", ""))) or datetime.min.replace(tzinfo=UTC))
    for event in sorted_events:
        mac = str(event.get("mac", "")).strip()
        timestamp = _parse_ts(str(event.get("timestamp", "")))
        transition = _extract_state_transition(event)
        if not mac or timestamp is None or transition is None:
            continue

        previous_state, current_state = transition
        session = session_by_mac.setdefault(
            mac,
            {
                "state_changed_at": None,
                "online_since": None,
                "idle_since": None,
                "offline_since": None,
            },
        )
        session["state_changed_at"] = timestamp

        if current_state in {"online", "idle"}:
            if previous_state not in {"online", "idle"} or session["online_since"] is None:
                session["online_since"] = timestamp
            session["idle_since"] = timestamp if current_state == "idle" else None
            session["offline_since"] = None
        elif current_state == "offline":
            session["offline_since"] = timestamp
            session["online_since"] = None
            session["idle_since"] = None

    items: list[dict[str, Any]] = []

    for device in snapshot:
        if not isinstance(device, dict):
            continue

        mac = str(device.get("mac_address", ""))
        dhcp_flags = device.get("dhcp_flags") if isinstance(device.get("dhcp_flags"), dict) else {}
        arp_flags = device.get("arp_flags") if isinstance(device.get("arp_flags"), dict) else {}
        source = device.get("source")
        source_text = "+".join(source) if isinstance(source, list) else str(source or "-")
        source_tokens = set(source_text.split("+"))

        raw_has_dhcp_lease = device.get("has_dhcp_lease")
        if isinstance(raw_has_dhcp_lease, bool):
            has_dhcp_lease = raw_has_dhcp_lease
        else:
            has_dhcp_lease = "dhcp" in source_tokens

        raw_dhcp_is_dynamic = device.get("dhcp_is_dynamic")
        dhcp_is_dynamic = raw_dhcp_is_dynamic if isinstance(raw_dhcp_is_dynamic, bool) else None
        raw_has_arp_entry = device.get("has_arp_entry")
        if isinstance(raw_has_arp_entry, bool):
            has_arp_entry = raw_has_arp_entry
        else:
            has_arp_entry = "arp" in source_tokens
        bridge_host_present = bool(device.get("bridge_host_present", False) or "bridge_host" in source_tokens)
        dhcp_flag = _dhcp_flag(has_dhcp_lease, dhcp_flags, dhcp_is_dynamic)
        arp_flag = _arp_flag(has_arp_entry, arp_flags)
        device_state = _device_state(device)
        arp_status = normalize_arp_status(device.get("arp_status", "unknown"))
        arp_state = str(device.get("arp_state", "")).strip().lower() or device_state
        primary_ip = str(device.get("ip_address", ""))
        last_known_ip = str(device.get("last_known_ip", "")).strip()
        last_known_hostname = str(device.get("last_known_hostname", "")).strip()
        ip_is_stale = bool(device.get("ip_is_stale", False))
        hostname_is_stale = bool(device.get("hostname_is_stale", False))
        data_is_stale = bool(device.get("data_is_stale", False))
        arp_secondary = device.get("arp_secondary") if isinstance(device.get("arp_secondary"), list) else []
        badges = [str(value).strip().upper() for value in device.get("badges", []) if str(value).strip()]
        entity_type = str(device.get("entity_type", "client")).strip().lower() or "client"
        interface_name = str(device.get("interface_name", "")).strip()
        session = session_by_mac.get(mac, {})

        state_changed_at = _parse_ts(str(device.get("state_changed_at", "")))
        online_since = _parse_ts(str(device.get("online_since", "")))
        idle_since = _parse_ts(str(device.get("idle_since", "")))
        offline_since = _parse_ts(str(device.get("offline_since", "")))

        if isinstance(session, dict):
            event_state_changed_at = session.get("state_changed_at")
            should_override_from_events = isinstance(event_state_changed_at, datetime) and (
                not isinstance(state_changed_at, datetime) or event_state_changed_at >= state_changed_at
            )

            if should_override_from_events:
                logger.info(
                    "API: overriding snapshot session timestamps with newer event data for MAC %s",
                    mac,
                )
                state_changed_at = event_state_changed_at
                online_since = session.get("online_since")
                idle_since = session.get("idle_since")
                offline_since = session.get("offline_since")
            else:
                if not isinstance(state_changed_at, datetime):
                    state_changed_at = event_state_changed_at
                if not isinstance(online_since, datetime):
                    online_since = session.get("online_since")
                if not isinstance(idle_since, datetime):
                    idle_since = session.get("idle_since")
                if not isinstance(offline_since, datetime):
                    offline_since = session.get("offline_since")

        resolved_state = _resolve_api_state(
            mac=mac,
            offline_since=offline_since,
            online_since=online_since,
            idle_since=idle_since,
            bridge_host_present=bridge_host_present,
            now=now,
            idle_timeout_seconds=idle_timeout_seconds,
            fallback_state=device_state,
        )
        active = resolved_state == "online"

        presence_duration_seconds = (
            max(0, int((now - online_since).total_seconds()))
            if resolved_state in {"online", "idle"} and isinstance(online_since, datetime)
            else None
        )
        offline_duration_seconds = (
            max(0, int((now - offline_since).total_seconds()))
            if resolved_state == "offline" and isinstance(offline_since, datetime)
            else None
        )
        idle_duration_seconds = (
            max(0, int((now - idle_since).total_seconds()))
            if resolved_state == "idle" and isinstance(idle_since, datetime)
            else None
        )
        elapsed_seconds = presence_duration_seconds or offline_duration_seconds or 0

        items.append(
            {
                "mac": mac,
                "ip": primary_ip,
                "last_known_ip": last_known_ip,
                "is_link_local_ip": _is_link_local(primary_ip),
                "hostname": device.get("host_name", ""),
                "last_known_hostname": last_known_hostname,
                "ip_is_stale": ip_is_stale,
                "hostname_is_stale": hostname_is_stale,
                "data_is_stale": data_is_stale,
                "dhcp_comment": str(device.get("dhcp_comment", "")),
                "arp_comment": str(device.get("arp_comment", "")),
                "comments_badge": _comment_badge_label(
                    str(device.get("dhcp_comment", "")),
                    str(device.get("arp_comment", "")),
                ),
                "comments": _comment_text(
                    str(device.get("dhcp_comment", "")),
                    str(device.get("arp_comment", "")),
                ),
                "flags": {
                    "source": source_text,
                    "dhcp_flag": dhcp_flag,
                    "has_dhcp_lease": has_dhcp_lease,
                    "has_arp_entry": has_arp_entry,
                    "bridge_host_present": bridge_host_present,
                    "arp_flag": arp_flag,
                    "state": resolved_state,
                },
                "status": resolved_state,
                "arp_status": arp_status,
                "arp_state": arp_state,
                "arp_secondary_count": len(arp_secondary),
                "arp_secondary": arp_secondary,
                "badges": badges,
                "entity_type": entity_type,
                "interface_name": interface_name,
                "active": active,
                "last_change": state_changed_at.isoformat() if isinstance(state_changed_at, datetime) else None,
                "state_changed_at": state_changed_at.isoformat() if isinstance(state_changed_at, datetime) else None,
                "online_since": online_since.isoformat() if isinstance(online_since, datetime) else None,
                "idle_since": idle_since.isoformat() if isinstance(idle_since, datetime) else None,
                "offline_since": offline_since.isoformat() if isinstance(offline_since, datetime) else None,
                "presence_duration_seconds": presence_duration_seconds,
                "offline_duration_seconds": offline_duration_seconds,
                "idle_duration_seconds": idle_duration_seconds,
                "elapsed_seconds": elapsed_seconds,
            }
        )

    items.sort(key=lambda item: (not bool(item.get("active")), int(item.get("elapsed_seconds", 0))))
    return {"items": items, "generated_at": now.isoformat()}

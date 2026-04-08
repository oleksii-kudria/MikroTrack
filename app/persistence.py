from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.arp_logic import fused_device_state, normalize_arp_status
from app.exceptions import MikroTrackError

logger = logging.getLogger("mikrotrack")
_persistence_path = Path("/data/snapshots")
_retention_days = 7
_LOW_DISK_SPACE_THRESHOLD_BYTES = 50 * 1024 * 1024
_EVENTS_FILENAME = "events.jsonl"


Event = dict[str, Any]


def configure_persistence(path: str, retention_days: int) -> None:
    global _persistence_path, _retention_days
    _persistence_path = Path(path)
    _retention_days = retention_days


def _read_mount_points() -> set[Path]:
    mount_points: set[Path] = set()

    try:
        with Path("/proc/self/mountinfo").open("r", encoding="utf-8") as mount_file:
            for line in mount_file:
                parts = line.split()
                if len(parts) > 4:
                    mount_points.add(Path(parts[4]))
    except OSError:
        return set()

    return mount_points


def _warn_if_path_not_mounted_to_host() -> None:
    mount_points = _read_mount_points()
    if not mount_points:
        return

    resolved_path = _persistence_path.resolve()
    if resolved_path not in mount_points:
        logger.warning("WARNING: Persistence path may not be mounted to host")
        logger.warning("Recommendation: Verify docker-compose volume mapping")


def validate_persistence() -> None:
    logger.info("Persistence enabled: true")
    logger.info("Persistence path: %s", _persistence_path)

    if _persistence_path.exists() and not _persistence_path.is_dir():
        raise MikroTrackError(
            error_code="PERSISTENCE_ERROR",
            message="Persistence path is not writable or does not exist",
            recommendation="Verify volume mapping and directory permissions on host",
        )

    if not _persistence_path.exists():
        try:
            _persistence_path.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise MikroTrackError(
                error_code="PERSISTENCE_ERROR",
                message="Failed to create persistence directory",
                recommendation="Check permissions or create directory manually on host",
                original_exception=error,
            ) from error

    test_file = _persistence_path / ".mikrotrack_write_test"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except OSError as error:
        raise MikroTrackError(
            error_code="PERSISTENCE_ERROR",
            message="Persistence path is not writable",
            recommendation="Check filesystem permissions and Docker volume mapping",
            original_exception=error,
        ) from error

    disk_usage = shutil.disk_usage(_persistence_path)
    if disk_usage.free < _LOW_DISK_SPACE_THRESHOLD_BYTES:
        logger.warning("[LOW_DISK_SPACE] Available disk space is low (<50MB)")
        logger.warning("Recommendation: Clean up old snapshots or increase storage")

    _warn_if_path_not_mounted_to_host()


def _cleanup_old_snapshots() -> int:
    if _retention_days < 0:
        return 0

    cutoff = datetime.now() - timedelta(days=_retention_days)
    removed_count = 0

    for snapshot in _persistence_path.glob("*.json"):
        try:
            modified_at = datetime.fromtimestamp(snapshot.stat().st_mtime)
        except FileNotFoundError:
            continue

        if modified_at < cutoff:
            snapshot.unlink(missing_ok=True)
            removed_count += 1

    return removed_count


def _latest_snapshot_path() -> Path | None:
    snapshots = sorted(_persistence_path.glob("*.json"))
    if not snapshots:
        return None

    return snapshots[-1]


def _index_devices_by_mac(devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for device in devices:
        mac = str(device.get("mac_address", "")).strip()
        if mac:
            indexed[mac] = device
    return indexed


def _iso_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _source_value(device: dict[str, Any]) -> str:
    source = device.get("source", [])
    if isinstance(source, list):
        cleaned = sorted(str(item).strip() for item in source if str(item).strip())
        return "+".join(cleaned)
    return str(source).strip()


def _get_nested_flag(device: dict[str, Any], container_key: str, flag_key: str) -> bool:
    container = device.get(container_key, {})
    if not isinstance(container, dict):
        return False
    return bool(container.get(flag_key, False))


def _event_context(device: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(device, dict):
        return {}
    context: dict[str, Any] = {}
    entity_type = str(device.get("entity_type", "")).strip().lower()
    if entity_type:
        context["entity_type"] = entity_type
    interface_name = str(device.get("interface_name", "")).strip()
    if interface_name:
        context["interface_name"] = interface_name
    return context


def _build_event(
    event_type: str,
    mac: str,
    *,
    device: dict[str, Any] | None = None,
    old_value: Any | None = None,
    new_value: Any | None = None,
) -> Event:
    event: Event = {
        "timestamp": _iso_timestamp(),
        "event_type": event_type,
        "mac": mac,
    }
    event.update(_event_context(device))
    if old_value is not None:
        event["old_value"] = old_value
    if new_value is not None:
        event["new_value"] = new_value
    return event


def _log_event(event: Event) -> None:
    details: list[str] = []
    if "old_value" in event:
        details.append(f"old={event['old_value']}")
    if "new_value" in event:
        details.append(f"new={event['new_value']}")

    suffix = f" ({', '.join(details)})" if details else ""
    logger.debug("[%s] Event generated for %s%s", event["event_type"], event["mac"], suffix)


def _build_arp_transition_event(
    event_type: str,
    mac: str,
    *,
    device: dict[str, Any] | None = None,
    old_key: str,
    new_key: str,
    old_value: str,
    new_value: str,
) -> Event:
    event = {
        "timestamp": _iso_timestamp(),
        "event_type": event_type,
        "type": event_type,
        "mac": mac,
        old_key: old_value,
        new_key: new_value,
        "old_value": old_value,
        "new_value": new_value,
    }
    event.update(_event_context(device))
    return event


def _online_reason(arp_status: str, bridge_host_present: bool) -> str:
    if normalize_arp_status(arp_status) == "reachable":
        return "arp_reachable"
    if bridge_host_present:
        return "bridge_host_detected"
    return "unknown"


def _state_reason(state: str, arp_status: str, bridge_host_present: bool) -> str:
    if state == "online":
        return _online_reason(arp_status, bridge_host_present)
    normalized = normalize_arp_status(arp_status)
    if state == "idle" and normalized in {"stale", "delay", "probe"}:
        return f"arp_{normalized}"
    if state == "offline" and normalized in {"failed", "incomplete"}:
        return f"arp_{normalized}"
    return "no_evidence"


def _normalized_device_state(state: str) -> str:
    normalized = str(state).strip().lower()
    return normalized if normalized in {"online", "idle", "offline", "permanent", "unknown"} else "unknown"


def _normalized_presence_state(state: str) -> str:
    normalized = str(state).strip().lower()
    return normalized if normalized in {"online", "idle", "offline"} else "unknown"


def _sanitize_presence_transition(previous_state: str, current_state: str) -> tuple[str, str]:
    prev = _normalized_presence_state(previous_state)
    curr = _normalized_presence_state(current_state)

    # Idle is a sub-state of the online presence session.
    # Transition offline -> idle is invalid and must become a new online session.
    if prev == "offline" and curr == "idle":
        curr = "online"

    return prev, curr


def _derive_device_state(device: dict[str, Any]) -> str:
    arp_status = normalize_arp_status(device.get("arp_status", "unknown"))
    bridge_host_present = bool(device.get("bridge_host_present", False))
    raw_state = str(device.get("arp_state", "")).strip().lower()
    if raw_state:
        return _normalized_device_state(raw_state)
    if arp_status == "permanent":
        return "permanent"
    return _normalized_device_state(fused_device_state(arp_status, bridge_host_present))


def _has_presence_evidence(device: dict[str, Any]) -> bool:
    bridge_host_present = bool(device.get("bridge_host_present", False))
    evidence = device.get("evidence")
    if not bridge_host_present and isinstance(evidence, dict):
        bridge_host_present = bool(evidence.get("bridge_host_present", False))
    if bridge_host_present:
        return True

    arp_status = normalize_arp_status(device.get("arp_status", "unknown"))
    if arp_status in {"reachable", "delay"}:
        return True

    if isinstance(evidence, dict):
        evidence_arp_status = normalize_arp_status(evidence.get("arp_status", "unknown"))
        if evidence_arp_status in {"reachable", "delay"}:
            return True

    return False


def _apply_stable_timestamps(current_devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    previous_snapshot_path = _latest_snapshot_path()
    previous_devices: list[dict[str, Any]] = []
    if previous_snapshot_path is not None:
        try:
            with previous_snapshot_path.open("r", encoding="utf-8") as snapshot_file:
                payload = json.load(snapshot_file)
            if isinstance(payload, list):
                previous_devices = [item for item in payload if isinstance(item, dict)]
        except Exception:
            logger.warning("Failed to load previous snapshot for stable timestamp propagation")

    previous_by_mac = _index_devices_by_mac(previous_devices)
    now_iso = _iso_timestamp()
    enriched_devices: list[dict[str, Any]] = []

    for current in current_devices:
        mac = str(current.get("mac_address", "")).strip()
        if not mac:
            enriched_devices.append(current)
            continue

        previous = previous_by_mac.get(mac)
        current_state = _derive_device_state(current)
        device = dict(current)
        device.setdefault("state_changed_at", None)
        device.setdefault("online_since", None)
        device.setdefault("offline_since", None)

        if previous is None:
            if current_state in {"online", "idle"}:
                device["state_changed_at"] = now_iso
                device["online_since"] = now_iso
                device["offline_since"] = None
            elif current_state == "offline":
                device["state_changed_at"] = now_iso
                device["offline_since"] = now_iso
                device["online_since"] = None
            else:
                device["state_changed_at"] = None
                device["online_since"] = None
                device["offline_since"] = None
            _initialize_missing_session_timestamps(
                device=device,
                presence_state=current_state,
                now_iso=now_iso,
                mac=mac,
            )
            enriched_devices.append(device)
            continue

        previous_state = _derive_device_state(previous)
        merge_current_state = current_state
        decision = "apply_transition_rules"
        if current_state == "unknown" and _has_presence_evidence(device):
            merge_current_state = previous_state
            decision = "unknown_with_evidence_preserved_previous_state"

        previous_presence_state, current_presence_state = _sanitize_presence_transition(previous_state, merge_current_state)
        previous_state_changed_at = previous.get("state_changed_at")
        previous_online_since = previous.get("online_since")
        previous_offline_since = previous.get("offline_since")

        if previous_state == merge_current_state:
            device["state_changed_at"] = previous_state_changed_at
            if merge_current_state in {"online", "idle"}:
                device["online_since"] = previous_online_since
                device["offline_since"] = None
            elif merge_current_state == "offline":
                device["online_since"] = None
                device["offline_since"] = previous_offline_since
            else:
                device["online_since"] = previous_online_since
                device["offline_since"] = previous_offline_since
            _initialize_missing_session_timestamps(
                device=device,
                presence_state=current_presence_state,
                now_iso=now_iso,
                mac=mac,
            )
            logger.debug(
                "state timestamp merge: mac=%s old_state=%s new_state=%s "
                "old_online_since=%s new_online_since=%s "
                "old_offline_since=%s new_offline_since=%s decision=%s",
                mac,
                previous_state,
                current_state,
                previous_online_since,
                device.get("online_since"),
                previous_offline_since,
                device.get("offline_since"),
                "preserved",
            )
            enriched_devices.append(device)
            continue

        device["state_changed_at"] = now_iso

        if previous_presence_state == "offline" and current_presence_state in {"online", "idle"}:
            device["online_since"] = now_iso
            device["offline_since"] = None
        elif previous_presence_state in {"online", "idle"} and current_presence_state == "offline":
            device["online_since"] = None
            device["offline_since"] = now_iso
        elif previous_presence_state == "online" and current_presence_state == "idle":
            device["online_since"] = previous_online_since
            device["offline_since"] = None
        elif previous_presence_state == "idle" and current_presence_state == "online":
            device["online_since"] = previous_online_since
            device["offline_since"] = None
        else:
            device["online_since"] = previous_online_since
            device["offline_since"] = previous_offline_since

        _initialize_missing_session_timestamps(
            device=device,
            presence_state=current_presence_state,
            now_iso=now_iso,
            mac=mac,
        )

        logger.debug(
            "state timestamp merge: mac=%s old_state=%s new_state=%s "
            "old_online_since=%s new_online_since=%s "
            "old_offline_since=%s new_offline_since=%s decision=%s",
            mac,
            previous_state,
            current_state,
            previous_online_since,
            device.get("online_since"),
            previous_offline_since,
            device.get("offline_since"),
            decision,
        )
        enriched_devices.append(device)

    return enriched_devices


def _initialize_missing_session_timestamps(
    *,
    device: dict[str, Any],
    presence_state: str,
    now_iso: str,
    mac: str,
) -> None:
    initialized_online_since = False
    initialized_offline_since = False
    initialized_state_changed_at = False

    if presence_state in {"online", "idle"} and not device.get("online_since"):
        device["online_since"] = now_iso
        initialized_online_since = True

    if presence_state == "offline" and not device.get("offline_since"):
        device["offline_since"] = now_iso
        initialized_offline_since = True

    if (initialized_online_since or initialized_offline_since) and not device.get("state_changed_at"):
        device["state_changed_at"] = now_iso
        initialized_state_changed_at = True

    if initialized_online_since or initialized_offline_since or initialized_state_changed_at:
        logger.debug(
            "session timestamp initialized: mac=%s state=%s online_since_initialized=%s "
            "offline_since_initialized=%s state_changed_at_initialized=%s",
            mac,
            presence_state,
            initialized_online_since,
            initialized_offline_since,
            initialized_state_changed_at,
        )


def _append_events(events: list[Event]) -> None:
    if not events:
        return

    events_path = _persistence_path / _EVENTS_FILENAME
    with events_path.open("a", encoding="utf-8") as events_file:
        for event in events:
            events_file.write(json.dumps(event, ensure_ascii=False) + "\n")

    logger.info("Events persisted: %d -> %s", len(events), events_path)


def _generate_diff_events(previous_devices: list[dict[str, Any]], current_devices: list[dict[str, Any]]) -> list[Event]:
    previous_by_mac = _index_devices_by_mac(previous_devices)
    current_by_mac = _index_devices_by_mac(current_devices)

    events: list[Event] = []
    new_count = 0
    removed_count = 0
    changed_count = 0

    for mac, current in current_by_mac.items():
        previous = previous_by_mac.get(mac)
        if previous is None:
            new_count += 1
            logger.debug(
                "[NEW_DEVICE] New device detected: %s (%s)",
                current.get("ip_address", ""),
                mac,
            )
            event = _build_event("NEW_DEVICE", mac, device=current)
            events.append(event)
            _log_event(event)
            current_entity_type = str(current.get("entity_type", "")).strip().lower()
            if current_entity_type:
                entity_event = _build_event(
                    "entity_type_detected",
                    mac,
                    device=current,
                    new_value=current_entity_type,
                )
                events.append(entity_event)
                _log_event(entity_event)
            if current_entity_type == "interface":
                interface_event = _build_event(
                    "interface_detected",
                    mac,
                    device=current,
                    new_value=str(current.get("interface_name", "")).strip(),
                )
                events.append(interface_event)
                _log_event(interface_event)
            continue

        previous_ip = str(previous.get("ip_address", ""))
        current_ip = str(current.get("ip_address", ""))
        if previous_ip != current_ip:
            changed_count += 1
            logger.debug("[IP_CHANGED] Device IP changed: %s %s -> %s", mac, previous_ip, current_ip)
            event = _build_event("IP_CHANGED", mac, device=current, old_value=previous_ip, new_value=current_ip)
            events.append(event)
            _log_event(event)

        previous_hostname = str(previous.get("host_name", ""))
        current_hostname = str(current.get("host_name", ""))
        if previous_hostname != current_hostname:
            changed_count += 1
            logger.debug(
                "[HOSTNAME_CHANGED] Hostname changed: %s %s -> %s",
                mac,
                previous_hostname,
                current_hostname,
            )
            event = _build_event(
                "HOSTNAME_CHANGED",
                mac,
                device=current,
                old_value=previous_hostname,
                new_value=current_hostname,
            )
            events.append(event)
            _log_event(event)

        previous_has_dhcp = "dhcp" in _source_value(previous).split("+")
        current_has_dhcp = "dhcp" in _source_value(current).split("+")
        if not previous_has_dhcp and current_has_dhcp:
            changed_count += 1
            logger.debug("[DHCP_ADDED] DHCP lease appeared")
            event = _build_event("DHCP_ADDED", mac, device=current)
            events.append(event)
            _log_event(event)
        elif previous_has_dhcp and not current_has_dhcp:
            changed_count += 1
            logger.debug("[DHCP_REMOVED] DHCP lease removed")
            event = _build_event("DHCP_REMOVED", mac, device=current)
            events.append(event)
            _log_event(event)

        previous_dhcp_dynamic = _get_nested_flag(previous, "dhcp_flags", "dynamic")
        current_dhcp_dynamic = _get_nested_flag(current, "dhcp_flags", "dynamic")
        if previous_dhcp_dynamic != current_dhcp_dynamic:
            changed_count += 1
            logger.debug(
                "[DHCP_DYNAMIC_CHANGED] DHCP dynamic flag changed: %s -> %s",
                previous_dhcp_dynamic,
                current_dhcp_dynamic,
            )
            event = _build_event(
                "DHCP_DYNAMIC_CHANGED",
                mac,
                device=current,
                old_value=previous_dhcp_dynamic,
                new_value=current_dhcp_dynamic,
            )
            events.append(event)
            _log_event(event)

            assignment_old = "dynamic" if previous_dhcp_dynamic else "static"
            assignment_new = "dynamic" if current_dhcp_dynamic else "static"
            logger.debug(
                "[DEVICE_IP_ASSIGNMENT_CHANGED] IP assignment changed: %s -> %s",
                assignment_old,
                assignment_new,
            )
            event = _build_event(
                "DEVICE_IP_ASSIGNMENT_CHANGED",
                mac,
                device=current,
                old_value=assignment_old,
                new_value=assignment_new,
            )
            events.append(event)
            _log_event(event)

        previous_dhcp_status = str(previous.get("dhcp_status", "unknown"))
        current_dhcp_status = str(current.get("dhcp_status", "unknown"))
        if previous_dhcp_status != current_dhcp_status:
            changed_count += 1
            logger.debug("[DHCP_STATUS_CHANGED] DHCP status changed")
            event = _build_event(
                "DHCP_STATUS_CHANGED",
                mac,
                device=current,
                old_value=previous_dhcp_status,
                new_value=current_dhcp_status,
            )
            events.append(event)
            _log_event(event)

        previous_dhcp_comment = str(previous.get("dhcp_comment", ""))
        current_dhcp_comment = str(current.get("dhcp_comment", ""))
        if previous_dhcp_comment != current_dhcp_comment:
            changed_count += 1
            logger.debug("[DHCP_COMMENT_CHANGED] DHCP comment changed")
            event = _build_event(
                "DHCP_COMMENT_CHANGED",
                mac,
                device=current,
                old_value=previous_dhcp_comment,
                new_value=current_dhcp_comment,
            )
            events.append(event)
            _log_event(event)

        previous_has_arp = "arp" in _source_value(previous).split("+")
        current_has_arp = "arp" in _source_value(current).split("+")
        if not previous_has_arp and current_has_arp:
            changed_count += 1
            logger.debug("[ARP_ADDED] ARP entry appeared")
            event = _build_event("ARP_ADDED", mac, device=current)
            events.append(event)
            _log_event(event)
        elif previous_has_arp and not current_has_arp:
            changed_count += 1
            logger.debug("[ARP_REMOVED] ARP entry removed")
            event = _build_event("ARP_REMOVED", mac, device=current)
            events.append(event)
            _log_event(event)

        previous_arp_dynamic = _get_nested_flag(previous, "arp_flags", "dynamic")
        current_arp_dynamic = _get_nested_flag(current, "arp_flags", "dynamic")
        if previous_arp_dynamic != current_arp_dynamic:
            changed_count += 1
            logger.debug("[ARP_DYNAMIC_CHANGED] ARP dynamic flag changed")
            event = _build_event(
                "ARP_DYNAMIC_CHANGED",
                mac,
                device=current,
                old_value=previous_arp_dynamic,
                new_value=current_arp_dynamic,
            )
            events.append(event)
            _log_event(event)

        previous_arp_flags = previous.get("arp_flags", {})
        current_arp_flags = current.get("arp_flags", {})
        if previous_arp_flags != current_arp_flags:
            changed_count += 1
            logger.debug("[ARP_FLAG_CHANGED] ARP flags changed")
            event = _build_event(
                "ARP_FLAG_CHANGED",
                mac,
                device=current,
                old_value=previous_arp_flags,
                new_value=current_arp_flags,
            )
            events.append(event)
            _log_event(event)

        previous_arp_status = normalize_arp_status(previous.get("arp_status", "unknown"))
        current_arp_status = normalize_arp_status(current.get("arp_status", "unknown"))
        if previous_arp_status != current_arp_status:
            changed_count += 1
            logger.debug("[arp_status_changed] ARP status changed: %s -> %s", previous_arp_status, current_arp_status)
            event = _build_arp_transition_event(
                "arp_status_changed",
                mac,
                device=current,
                old_key="old_status",
                new_key="new_status",
                old_value=previous_arp_status,
                new_value=current_arp_status,
            )
            events.append(event)
            _log_event(event)

        previous_bridge_host_present = bool(previous.get("bridge_host_present", False))
        current_bridge_host_present = bool(current.get("bridge_host_present", False))
        previous_arp_state = str(previous.get("arp_state", "")).strip().lower() or fused_device_state(
            previous_arp_status, previous_bridge_host_present
        )
        current_arp_state = str(current.get("arp_state", "")).strip().lower() or fused_device_state(
            current_arp_status, current_bridge_host_present
        )
        if previous_arp_state != current_arp_state:
            changed_count += 1
            logger.debug("[arp_state_changed] ARP state changed: %s -> %s", previous_arp_state, current_arp_state)
            event = _build_arp_transition_event(
                "arp_state_changed",
                mac,
                device=current,
                old_key="old_state",
                new_key="new_state",
                old_value=previous_arp_state,
                new_value=current_arp_state,
            )
            events.append(event)
            _log_event(event)

            if current_arp_state in {"online", "offline", "idle"}:
                reason = _state_reason(current_arp_state, current_arp_status, current_bridge_host_present)
                device_event = {
                    "timestamp": _iso_timestamp(),
                    "event_type": f"device_{current_arp_state}",
                    "type": f"device_{current_arp_state}",
                    "mac": mac,
                    "reason": reason,
                    "old_value": previous_arp_state,
                    "new_value": current_arp_state,
                }
                device_event.update(_event_context(current))
                events.append(device_event)
                _log_event(device_event)

            previous_presence_state, current_presence_state = _sanitize_presence_transition(
                previous_arp_state,
                current_arp_state,
            )
            if previous_presence_state != "unknown" and current_presence_state != "unknown":
                state_changed_event = {
                    "timestamp": _iso_timestamp(),
                    "event_type": "state_changed",
                    "type": "state_changed",
                    "mac": mac,
                    "old_state": previous_presence_state,
                    "new_state": current_presence_state,
                    "old_value": previous_presence_state,
                    "new_value": current_presence_state,
                }
                state_changed_event.update(_event_context(current))
                events.append(state_changed_event)
                _log_event(state_changed_event)

                if previous_presence_state == "offline" and current_presence_state in {"online", "idle"}:
                    session_started_event = {
                        "timestamp": _iso_timestamp(),
                        "event_type": "session_started",
                        "type": "session_started",
                        "mac": mac,
                        "new_state": current_presence_state,
                    }
                    session_started_event.update(_event_context(current))
                    events.append(session_started_event)
                    _log_event(session_started_event)
                elif previous_presence_state in {"online", "idle"} and current_presence_state == "offline":
                    session_ended_event = {
                        "timestamp": _iso_timestamp(),
                        "event_type": "session_ended",
                        "type": "session_ended",
                        "mac": mac,
                        "old_state": previous_presence_state,
                    }
                    session_ended_event.update(_event_context(current))
                    events.append(session_ended_event)
                    _log_event(session_ended_event)

        previous_evidence = {
            "arp_status": previous_arp_status,
            "bridge_host_present": previous_bridge_host_present,
            "bridge_host_last_seen": str(previous.get("bridge_host_last_seen", "")),
        }
        current_evidence = {
            "arp_status": current_arp_status,
            "bridge_host_present": current_bridge_host_present,
            "bridge_host_last_seen": str(current.get("bridge_host_last_seen", "")),
        }
        if previous_evidence != current_evidence:
            changed_count += 1
            evidence_event = _build_event(
                "evidence_changed",
                mac,
                device=current,
                old_value=previous_evidence,
                new_value=current_evidence,
            )
            events.append(evidence_event)
            _log_event(evidence_event)

        previous_source = _source_value(previous)
        current_source = _source_value(current)
        if previous_source != current_source:
            changed_count += 1
            logger.debug("[SOURCE_CHANGED] Device source changed: %s -> %s", previous_source, current_source)
            event = _build_event("SOURCE_CHANGED", mac, device=current, old_value=previous_source, new_value=current_source)
            events.append(event)
            _log_event(event)

        previous_entity_type = str(previous.get("entity_type", "")).strip().lower()
        current_entity_type = str(current.get("entity_type", "")).strip().lower()
        if previous_entity_type != current_entity_type and current_entity_type:
            changed_count += 1
            event = _build_event(
                "entity_type_detected",
                mac,
                device=current,
                old_value=previous_entity_type or "unknown",
                new_value=current_entity_type,
            )
            events.append(event)
            _log_event(event)

        previous_interface_name = str(previous.get("interface_name", "")).strip()
        current_interface_name = str(current.get("interface_name", "")).strip()
        if current_entity_type == "interface" and previous_interface_name != current_interface_name:
            changed_count += 1
            event = _build_event(
                "interface_detected",
                mac,
                device=current,
                old_value=previous_interface_name,
                new_value=current_interface_name,
            )
            events.append(event)
            _log_event(event)

    for mac, previous in previous_by_mac.items():
        if mac in current_by_mac:
            continue

        removed_count += 1
        logger.debug("[DEVICE_REMOVED] Device disappeared: %s (%s)", previous.get("ip_address", ""), mac)
        event = _build_event("DEVICE_REMOVED", mac, device=previous)
        events.append(event)
        _log_event(event)

    logger.info("Diff summary:")
    logger.info("- new: %d", new_count)
    logger.info("- removed: %d", removed_count)
    logger.info("- changed: %d", changed_count)
    logger.info("- events: %d", len(events))

    return events


def process_snapshot_diff(current_devices: list[dict[str, Any]]) -> list[Event]:
    previous_snapshot_path = _latest_snapshot_path()
    if previous_snapshot_path is None:
        logger.info("[DIFF_SKIPPED] No previous snapshot found")
        return []

    try:
        with previous_snapshot_path.open("r", encoding="utf-8") as snapshot_file:
            previous_devices = json.load(snapshot_file)
        if not isinstance(previous_devices, list):
            raise ValueError("Snapshot payload is not a list")

        events = _generate_diff_events(previous_devices, current_devices)
        _append_events(events)
        return events
    except Exception:
        logger.error("[DIFF_ERROR] Failed to process snapshots")
        logger.error("Recommendation: Verify snapshot format and integrity")
        return []


def save_snapshot(devices: list[dict]) -> None:
    devices_with_timestamps = _apply_stable_timestamps(devices)
    process_snapshot_diff(devices_with_timestamps)

    filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
    file_path = _persistence_path / filename

    with file_path.open("w", encoding="utf-8") as snapshot_file:
        json.dump(devices_with_timestamps, snapshot_file, indent=2, ensure_ascii=False)

    file_size = file_path.stat().st_size
    logger.info("Snapshot saved: %s", file_path)
    logger.debug("Snapshot file size: %d bytes", file_size)
    logger.debug("Snapshot device count: %d", len(devices_with_timestamps))

    removed_count = _cleanup_old_snapshots()
    logger.info("Retention cleanup done: removed %d files", removed_count)

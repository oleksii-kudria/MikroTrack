from __future__ import annotations

import json
import logging
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.arp_logic import fused_device_state, normalize_arp_status
from app.exceptions import MikroTrackError

logger = logging.getLogger("mikrotrack")
_persistence_path = Path("/data/snapshots")
_retention_days = 7
_idle_timeout_seconds = 900
_LOW_DISK_SPACE_THRESHOLD_BYTES = 50 * 1024 * 1024
_EVENTS_FILENAME = "events.jsonl"
_DATETIME_TYPE = datetime


Event = dict[str, Any]


def _now_aware() -> datetime:
    return datetime.now(UTC)


def configure_persistence(path: str, retention_days: int, *, idle_timeout_seconds: int = 900) -> None:
    global _persistence_path, _retention_days, _idle_timeout_seconds
    _persistence_path = Path(path)
    _retention_days = retention_days
    _idle_timeout_seconds = idle_timeout_seconds


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
        logger.warning("Persistence path may not be mounted to host")
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


def _device_mac(device: dict[str, Any]) -> str:
    return str(device.get("mac_address") or device.get("mac") or "").strip().upper()


def _index_devices_by_mac(devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for device in devices:
        mac = _device_mac(device)
        if not mac:
            logger.warning("persistence: skipping device without MAC key")
            continue
        indexed[mac] = device
    return indexed


def _iso_timestamp() -> str:
    return _now_aware().isoformat(timespec="seconds")


def _parse_snapshot_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
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


def _idle_timeout_exceeded(*, previous: dict[str, Any], now: datetime) -> bool:
    idle_since = _parse_snapshot_timestamp(previous.get("idle_since"))
    if idle_since is None:
        idle_since = _parse_snapshot_timestamp(previous.get("state_changed_at"))
    if idle_since is None:
        return False

    return (now - idle_since).total_seconds() >= _idle_timeout_seconds


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


def _build_field_change_event(
    mac: str,
    field_name: str,
    previous_value: Any,
    current_value: Any,
    *,
    device: dict[str, Any] | None = None,
) -> Event:
    event: Event = {
        "timestamp": _iso_timestamp(),
        "event_type": "FIELD_CHANGE",
        "mac": mac,
        "device_mac": mac,
        "field_name": field_name,
        "previous_value": previous_value,
        "current_value": current_value,
        "old_value": previous_value,
        "new_value": current_value,
    }
    event.update(_event_context(device))
    return event


def _log_event(event: Event) -> None:
    details: list[str] = []
    if "old_value" in event:
        details.append(f"old={event['old_value']}")
    if "new_value" in event:
        details.append(f"new={event['new_value']}")

    suffix = f" ({', '.join(details)})" if details else ""
    logger.debug("[%s] Event generated for %s%s", event["event_type"], event["mac"], suffix)


def _log_field_change(mac: str, field_name: str, previous_value: Any, current_value: Any) -> None:
    logger.info(
        "diff: detected change field=%s mac=%s old=%s new=%s",
        field_name,
        mac,
        previous_value,
        current_value,
    )


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


def _device_offline_reason(
    previous_state: str,
    current_state: str,
    arp_status: str,
    bridge_host_present: bool,
) -> str:
    previous_presence_state, current_presence_state = _sanitize_presence_transition(previous_state, current_state)
    if (
        previous_presence_state == "idle"
        and current_presence_state == "offline"
        and not bridge_host_present
        and normalize_arp_status(arp_status) in {"permanent", "unknown", "stale", "delay", "probe"}
    ):
        return "idle_timeout"
    return _state_reason(current_state, arp_status, bridge_host_present)


def _normalized_device_state(state: str) -> str:
    normalized = str(state).strip().lower()
    return normalized if normalized in {"online", "idle", "offline", "unknown"} else "unknown"


def _normalized_presence_state(state: str) -> str:
    normalized = str(state).strip().lower()
    return normalized if normalized in {"online", "idle", "offline"} else "unknown"


def _has_reconnect_evidence(
    *,
    arp_status: str,
    bridge_host_present: bool,
    evidence: dict[str, Any] | None = None,
) -> bool:
    if bridge_host_present:
        return True

    if normalize_arp_status(arp_status) in {"reachable", "complete"}:
        return True

    if isinstance(evidence, dict):
        if bool(evidence.get("bridge_host_present", False)):
            return True
        if normalize_arp_status(evidence.get("arp_status", "unknown")) in {"reachable", "complete"}:
            return True

    return False


def _sanitize_presence_transition(
    previous_state: str,
    current_state: str,
    *,
    has_reconnect_evidence: bool = False,
) -> tuple[str, str]:
    prev = _normalized_presence_state(previous_state)
    curr = _normalized_presence_state(current_state)

    # Idle is a sub-state of the online presence session.
    # Transition offline -> idle can only become online when fresh reconnect evidence exists.
    if prev == "offline" and curr == "idle":
        curr = "online" if has_reconnect_evidence else "offline"

    return prev, curr


def _derive_device_state(device: dict[str, Any]) -> str:
    bridge_host_present = bool(device.get("bridge_host_present", False))
    arp_status = normalize_arp_status(device.get("arp_status", "unknown"))
    if arp_status == "permanent":
        logger.info("ARP permanent entry is treated as STATIC metadata for MAC %s", str(device.get("mac_address", "")).strip().upper() or "unknown")

    if bridge_host_present:
        logger.debug("State resolved using generic presence rules for MAC %s (state=online)", str(device.get("mac_address", "")).strip().upper() or "unknown")
        return "online"

    fused_state = str(device.get("fused_state", "")).strip().lower()
    if fused_state:
        resolved = _normalized_device_state(fused_state)
        logger.debug("State resolved using generic presence rules for MAC %s (state=%s)", str(device.get("mac_address", "")).strip().upper() or "unknown", resolved)
        return resolved

    # Backward-compatible fallback for old snapshots without fused_state.
    resolved = _normalized_device_state(fused_device_state(arp_status, bridge_host_present))
    logger.debug("State resolved using generic presence rules for MAC %s (state=%s)", str(device.get("mac_address", "")).strip().upper() or "unknown", resolved)
    return resolved


def _resolve_previous_effective_state(
    *,
    previous: dict[str, Any],
    mac: str,
    now: datetime | None = None,
    logger_level: int = logging.DEBUG,
) -> str:
    previous_state = _derive_device_state(previous)
    previous_offline_since = _parse_snapshot_timestamp(previous.get("offline_since"))

    has_valid_offline_boundary = previous_offline_since is not None
    if has_valid_offline_boundary:
        logger.log(
            logger_level,
            "Previous snapshot contains offline_since for MAC %s, treating previous effective state as offline",
            mac,
        )
        return "offline"

    if previous_state == "idle" and now is not None and _idle_timeout_exceeded(previous=previous, now=now):
        return "offline"

    return previous_state


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


def _recalculate_state_on_bridge_host_loss(device: dict[str, Any]) -> str:
    arp_status = normalize_arp_status(device.get("arp_status", "unknown"))
    if arp_status in {"reachable", "complete"}:
        return "online"
    if arp_status in {"stale", "delay", "probe", "permanent"}:
        return "idle"
    if arp_status in {"failed", "incomplete", "unknown"}:
        return "offline"
    return "unknown"


_TRACKED_DEVICE_CHANGE_FIELDS: tuple[str, ...] = (
    "arp_type",
    "arp_flags",
    "dhcp_is_dynamic",
    "badges",
    "dhcp_comment",
    "arp_comment",
    "host_name",
    "primary_ip",
    "interface_name",
)


def _normalized_tracked_value(field: str, device: dict[str, Any]) -> Any:
    if field == "primary_ip":
        return str(device.get("ip_address", "")).strip()
    if field == "source":
        return _source_value(device)
    if field == "badges":
        badges = device.get("badges", [])
        if isinstance(badges, list):
            return tuple(sorted(str(item).strip().upper() for item in badges if str(item).strip()))
        return tuple()
    if field in {"dhcp_comment", "arp_comment", "host_name", "interface_name", "arp_type"}:
        return str(device.get(field, "")).strip()
    if field == "dhcp_is_dynamic":
        value = device.get(field)
        return value if isinstance(value, bool) else None
    if field == "arp_flags":
        value = device.get(field, {})
        return value if isinstance(value, dict) else {}
    return device.get(field)


def _changed_device_fields(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for field in _TRACKED_DEVICE_CHANGE_FIELDS:
        if _normalized_tracked_value(field, previous) != _normalized_tracked_value(field, current):
            changed.append(field)
    return changed


def _resolve_last_known_value(previous: dict[str, Any], current_key: str, last_known_key: str) -> str:
    current = str(previous.get(current_key, "")).strip()
    if current:
        return current
    return str(previous.get(last_known_key, "")).strip()


def _has_source(source_value: str, source_name: str) -> bool:
    return source_name in source_value.split("+")


def _normalized_optional_text(value: Any) -> str | None:
    text = str(value).strip()
    return text or None


def _dhcp_lease_type(device: dict[str, Any]) -> str | None:
    dhcp_flags = device.get("dhcp_flags", {})
    if not isinstance(dhcp_flags, dict) or "dynamic" not in dhcp_flags:
        return None
    return "dynamic" if bool(dhcp_flags.get("dynamic")) else "static"


def _extended_field_changes(
    *,
    mac: str,
    previous: dict[str, Any],
    current: dict[str, Any],
    previous_effective_state: str,
    current_state: str,
) -> list[Event]:
    previous_source = _source_value(previous)
    current_source = _source_value(current)

    previous_has_dhcp = _has_source(previous_source, "dhcp")
    current_has_dhcp = _has_source(current_source, "dhcp")

    previous_values: dict[str, Any] = {
        "state": previous_effective_state,
        "ip_address": _normalized_optional_text(previous.get("ip_address")),
        "hostname": _normalized_optional_text(previous.get("host_name")),
        "dhcp_lease_type": _dhcp_lease_type(previous),
        "dhcp_presence": previous_has_dhcp,
        "dhcp_flags": previous.get("dhcp_flags", {}) if isinstance(previous.get("dhcp_flags", {}), dict) else {},
        "arp_flags": previous.get("arp_flags", {}) if isinstance(previous.get("arp_flags", {}), dict) else {},
        "dhcp_comment": _normalized_optional_text(previous.get("dhcp_comment")),
        "arp_comment": _normalized_optional_text(previous.get("arp_comment")),
        "source": previous_source or None,
    }
    current_values: dict[str, Any] = {
        "state": current_state,
        "ip_address": _normalized_optional_text(current.get("ip_address")),
        "hostname": _normalized_optional_text(current.get("host_name")),
        "dhcp_lease_type": _dhcp_lease_type(current),
        "dhcp_presence": current_has_dhcp,
        "dhcp_flags": current.get("dhcp_flags", {}) if isinstance(current.get("dhcp_flags", {}), dict) else {},
        "arp_flags": current.get("arp_flags", {}) if isinstance(current.get("arp_flags", {}), dict) else {},
        "dhcp_comment": _normalized_optional_text(current.get("dhcp_comment")),
        "arp_comment": _normalized_optional_text(current.get("arp_comment")),
        "source": current_source or None,
    }

    events: list[Event] = []
    for field_name, previous_value in previous_values.items():
        current_value = current_values[field_name]
        if previous_value == current_value:
            continue

        _log_field_change(mac, field_name, previous_value, current_value)
        event = _build_field_change_event(
            mac,
            field_name,
            previous_value,
            current_value,
            device=current,
        )
        events.append(event)
        _log_event(event)

    return events


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
    now_dt = _parse_snapshot_timestamp(now_iso)
    enriched_devices: list[dict[str, Any]] = []

    for current in current_devices:
        mac = _device_mac(current)
        if not mac:
            enriched_devices.append(current)
            continue

        previous = previous_by_mac.get(mac)
        current_state = _derive_device_state(current)
        device = dict(current)
        device["ip_is_stale"] = False
        device["hostname_is_stale"] = False
        device["data_is_stale"] = False
        current_ip = str(device.get("ip_address", "")).strip()
        current_hostname = str(device.get("host_name", "")).strip()
        device["last_known_ip"] = current_ip
        device["last_known_hostname"] = current_hostname
        device.setdefault("state_changed_at", None)
        device.setdefault("online_since", None)
        device.setdefault("idle_since", None)
        device.setdefault("offline_since", None)

        if previous is None:
            if current_state in {"online", "idle"}:
                device["state_changed_at"] = now_iso
                device["online_since"] = now_iso
                device["idle_since"] = now_iso if current_state == "idle" else None
                device["offline_since"] = None
            elif current_state == "offline":
                device["state_changed_at"] = now_iso
                device["offline_since"] = now_iso
                device["online_since"] = None
                device["idle_since"] = None
            else:
                device["state_changed_at"] = None
                device["online_since"] = None
                device["idle_since"] = None
                device["offline_since"] = None
            _initialize_missing_session_timestamps(
                device=device,
                presence_state=current_state,
                now_iso=now_iso,
                mac=mac,
            )
            enriched_devices.append(device)
            continue

        previous_last_known_ip = _resolve_last_known_value(previous, "ip_address", "last_known_ip")
        previous_last_known_hostname = _resolve_last_known_value(previous, "host_name", "last_known_hostname")
        if previous_last_known_ip:
            device["last_known_ip"] = previous_last_known_ip
        if previous_last_known_hostname:
            device["last_known_hostname"] = previous_last_known_hostname

        if current_state == "offline":
            if not current_ip and previous_last_known_ip:
                logger.debug("Preserving last known IP for MAC %s", mac)
                device["ip_address"] = previous_last_known_ip
                device["ip_is_stale"] = True
                device["data_is_stale"] = True
            elif current_ip:
                device["last_known_ip"] = current_ip

            if not current_hostname and previous_last_known_hostname:
                logger.debug("Preserving last known hostname for MAC %s", mac)
                device["host_name"] = previous_last_known_hostname
                device["hostname_is_stale"] = True
                device["data_is_stale"] = True
            elif current_hostname:
                device["last_known_hostname"] = current_hostname

            if device["data_is_stale"]:
                logger.debug("Marking device data as stale for MAC %s", mac)
        else:
            if current_ip:
                device["last_known_ip"] = current_ip
            if current_hostname:
                device["last_known_hostname"] = current_hostname

        previous_state = _derive_device_state(previous)
        previous_effective_state = _resolve_previous_effective_state(
            previous=previous,
            mac=mac,
            now=now_dt,
            logger_level=logging.INFO,
        )
        previous_offline_boundary = _parse_snapshot_timestamp(previous.get("offline_since"))

        merge_current_state = current_state
        decision = "apply_transition_rules"
        current_arp_status = normalize_arp_status(device.get("arp_status", "unknown"))
        current_has_reconnect_evidence = _has_reconnect_evidence(
            arp_status=current_arp_status,
            bridge_host_present=bool(device.get("bridge_host_present", False)),
            evidence=device.get("evidence") if isinstance(device.get("evidence"), dict) else None,
        )
        previous_bridge_host_present = bool(previous.get("bridge_host_present", False))
        current_bridge_host_present = bool(device.get("bridge_host_present", False))
        bridge_host_lost = previous_bridge_host_present and not current_bridge_host_present
        idle_timeout_should_force_offline = (
            previous_state == "idle"
            and current_state != "online"
            and not current_bridge_host_present
            and isinstance(now_dt, datetime)
            and _idle_timeout_exceeded(previous=previous, now=now_dt)
        )

        if idle_timeout_should_force_offline:
            merge_current_state = "offline"
            device["arp_state"] = "offline"
            device["fused_state"] = "offline"
            decision = "idle_timeout_forced_offline"
            logger.info(
                "Idle timeout exceeded for MAC %s, forcing state to offline",
                mac,
            )
        elif bridge_host_lost:
            merge_current_state = _recalculate_state_on_bridge_host_loss(device)
            device["arp_state"] = merge_current_state
            device["fused_state"] = merge_current_state
            decision = "bridge_host_lost_recalculated_state"
        elif current_bridge_host_present:
            merge_current_state = "online"
            device["arp_state"] = "online"
            device["fused_state"] = "online"
            decision = "bridge_host_present_forced_online"
            if previous_effective_state == "offline":
                device["online_since"] = now_iso
                device["idle_since"] = None
                device["offline_since"] = None
                device["state_changed_at"] = now_iso
                previous_state = "offline"
                logger.info(
                    "Reconnect detected for MAC %s, starting new online session",
                    mac,
                )
                logger.info("Session timer reset for MAC %s", mac)
        elif current_state == "unknown" and _has_presence_evidence(device):
            merge_current_state = previous_effective_state
            decision = "unknown_with_evidence_preserved_previous_state"
        elif current_state == "idle" and previous_effective_state == "offline":
            merge_current_state = "offline"
            device["arp_state"] = "offline"
            device["fused_state"] = "offline"
            decision = "skip_idle_timeout_already_offline"
            logger.info("Skipping idle timeout, device already offline for MAC %s", mac)
        elif current_state == "idle" and previous_effective_state == "idle":
            logger.debug("Idle within threshold for MAC %s", mac)

        if (
            previous_effective_state == "offline"
            and merge_current_state == "offline"
            and previous_offline_boundary is not None
        ):
            transition_previous_state = previous_effective_state
            logger.debug("Device remains offline, preserving offline_since for MAC %s", mac)
            logger.debug("Skipping offline transition, state unchanged")
        else:
            transition_previous_state = previous_state if idle_timeout_should_force_offline else previous_effective_state
        previous_presence_state, current_presence_state = _sanitize_presence_transition(
            transition_previous_state,
            merge_current_state,
            has_reconnect_evidence=current_has_reconnect_evidence,
        )
        previous_state_changed_at = previous.get("state_changed_at")
        previous_online_since = previous.get("online_since")
        previous_idle_since = previous.get("idle_since")
        previous_offline_since = previous.get("offline_since")
        previous_source = _source_value(previous)
        current_source = _source_value(device)
        changed_fields = _changed_device_fields(previous, device)
        device_changed = bool(changed_fields)

        if previous_source != current_source:
            logger.debug(
                "identity merge: MAC=%s old_source=%s new_source=%s identity=preserved",
                mac,
                previous_source,
                current_source,
            )

        if transition_previous_state != merge_current_state:
            device["state_changed_at"] = now_iso

            if previous_presence_state == "offline" and current_presence_state in {"online", "idle"}:
                device["online_since"] = now_iso
                device["idle_since"] = now_iso if current_presence_state == "idle" else None
                device["offline_since"] = None
                decision = "transition_offline_to_online"
                logger.info(
                    "Reconnect detected for MAC %s, starting new online session",
                    mac,
                )
                logger.info("Session timer reset for MAC %s", mac)
            elif previous_presence_state in {"online", "idle"} and current_presence_state == "offline":
                device["online_since"] = None
                device["idle_since"] = None
                device["offline_since"] = now_iso
                decision = "transition_online_to_offline"
            elif previous_presence_state in {"online", "idle"} and current_presence_state in {"online", "idle"}:
                device["online_since"] = previous_online_since
                device["idle_since"] = now_iso if current_presence_state == "idle" else None
                device["offline_since"] = None
                decision = "transition_online_idle"
            else:
                device["online_since"] = previous_online_since
                device["idle_since"] = previous_idle_since
                device["offline_since"] = previous_offline_since
                decision = "transition_other"

            _initialize_missing_session_timestamps(
                device=device,
                presence_state=current_presence_state,
                now_iso=now_iso,
                mac=mac,
            )
            if current_presence_state == "offline" and not bool(device.get("bridge_host_present", False)):
                device["status"] = "offline"
                device["active"] = False

            logger.debug(
                "state timestamp merge: mac=%s old_state=%s new_state=%s device_changed=%s changed_fields=%s "
                "old_online_since=%s new_online_since=%s "
                "old_idle_since=%s new_idle_since=%s "
                "old_offline_since=%s new_offline_since=%s "
                "old_state_changed_at=%s new_state_changed_at=%s decision=%s",
                mac,
                previous_state,
                current_state,
                device_changed,
                changed_fields,
                previous_online_since,
                device.get("online_since"),
                previous_idle_since,
                device.get("idle_since"),
                previous_offline_since,
                device.get("offline_since"),
                previous_state_changed_at,
                device.get("state_changed_at"),
                decision,
            )
            enriched_devices.append(device)
            continue

        if device_changed:
            device["state_changed_at"] = now_iso
            if merge_current_state in {"online", "idle"}:
                device["online_since"] = previous_online_since
                device["idle_since"] = previous_idle_since if merge_current_state == "idle" else None
                device["offline_since"] = None
            elif merge_current_state == "offline":
                device["online_since"] = None
                device["idle_since"] = None
                device["offline_since"] = previous_offline_since
            else:
                device["online_since"] = previous_online_since
                device["idle_since"] = previous_idle_since
                device["offline_since"] = previous_offline_since
            _initialize_missing_session_timestamps(
                device=device,
                presence_state=current_presence_state,
                now_iso=now_iso,
                mac=mac,
            )
            if current_presence_state == "offline" and not bool(device.get("bridge_host_present", False)):
                device["status"] = "offline"
                device["active"] = False
            logger.debug(
                "state timestamp merge: mac=%s old_state=%s new_state=%s device_changed=%s changed_fields=%s "
                "old_online_since=%s new_online_since=%s "
                "old_idle_since=%s new_idle_since=%s "
                "old_offline_since=%s new_offline_since=%s "
                "old_state_changed_at=%s new_state_changed_at=%s decision=%s",
                mac,
                previous_state,
                current_state,
                device_changed,
                changed_fields,
                previous_online_since,
                device.get("online_since"),
                previous_idle_since,
                device.get("idle_since"),
                previous_offline_since,
                device.get("offline_since"),
                previous_state_changed_at,
                device.get("state_changed_at"),
                "device_change_update_timestamp",
            )
            enriched_devices.append(device)
            continue

        else:
            device["state_changed_at"] = previous_state_changed_at
            if merge_current_state in {"online", "idle"}:
                device["online_since"] = previous_online_since
                device["idle_since"] = previous_idle_since if merge_current_state == "idle" else None
                device["offline_since"] = None
            elif merge_current_state == "offline":
                device["online_since"] = None
                device["idle_since"] = None
                device["offline_since"] = previous_offline_since
            else:
                device["online_since"] = previous_online_since
                device["idle_since"] = previous_idle_since
                device["offline_since"] = previous_offline_since
            _initialize_missing_session_timestamps(
                device=device,
                presence_state=current_presence_state,
                now_iso=now_iso,
                mac=mac,
            )
            if current_presence_state == "offline" and not bool(device.get("bridge_host_present", False)):
                device["status"] = "offline"
                device["active"] = False
            logger.debug(
                "state timestamp merge: mac=%s old_state=%s new_state=%s device_changed=%s changed_fields=%s "
                "old_online_since=%s new_online_since=%s "
                "old_idle_since=%s new_idle_since=%s "
                "old_offline_since=%s new_offline_since=%s "
                "old_state_changed_at=%s new_state_changed_at=%s decision=%s",
                mac,
                previous_state,
                current_state,
                device_changed,
                changed_fields,
                previous_online_since,
                device.get("online_since"),
                previous_idle_since,
                device.get("idle_since"),
                previous_offline_since,
                device.get("offline_since"),
                previous_state_changed_at,
                device.get("state_changed_at"),
                "preserved",
            )
            enriched_devices.append(device)
            continue

    return enriched_devices


def _initialize_missing_session_timestamps(
    *,
    device: dict[str, Any],
    presence_state: str,
    now_iso: str,
    mac: str,
) -> None:
    initialized_online_since = False
    initialized_idle_since = False
    initialized_offline_since = False
    initialized_state_changed_at = False

    if presence_state in {"online", "idle"} and not device.get("online_since"):
        device["online_since"] = now_iso
        initialized_online_since = True

    if presence_state == "idle" and not device.get("idle_since"):
        device["idle_since"] = now_iso
        initialized_idle_since = True

    if presence_state != "idle":
        device["idle_since"] = None

    if presence_state == "offline" and not device.get("offline_since"):
        device["offline_since"] = now_iso
        initialized_offline_since = True

    if (initialized_online_since or initialized_idle_since or initialized_offline_since) and not device.get("state_changed_at"):
        device["state_changed_at"] = now_iso
        initialized_state_changed_at = True

    if initialized_online_since or initialized_idle_since or initialized_offline_since or initialized_state_changed_at:
        logger.debug(
            "session timestamp initialized: mac=%s state=%s online_since_initialized=%s "
            "idle_since_initialized=%s offline_since_initialized=%s state_changed_at_initialized=%s",
            mac,
            presence_state,
            initialized_online_since,
            initialized_idle_since,
            initialized_offline_since,
            initialized_state_changed_at,
        )


def _append_events(events: list[Event]) -> None:
    if not events:
        return

    events_path = _persistence_path / _EVENTS_FILENAME
    persisted_count = 0
    with events_path.open("a", encoding="utf-8") as events_file:
        for event in events:
            safe_event = _make_json_safe(event)
            try:
                events_file.write(json.dumps(safe_event, ensure_ascii=False) + "\n")
                persisted_count += 1
            except Exception:
                event_type = str(event.get("event_type", "unknown"))
                mac = str(event.get("mac", "unknown"))
                logger.exception("Failed to serialize event event_type=%s mac=%s", event_type, mac)
                logger.error("Event payload: %s", safe_event)

    if persisted_count:
        logger.info("Events persisted: %d -> %s", persisted_count, events_path)
    else:
        logger.warning("No events were persisted after serialization attempts: %s", events_path)


def _make_json_safe(value: Any) -> Any:
    if isinstance(value, _DATETIME_TYPE):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_make_json_safe(item) for item in value]
    if isinstance(value, tuple | set):
        return [_make_json_safe(item) for item in value]
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return repr(value)
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def _generate_diff_events(previous_devices: list[dict[str, Any]], current_devices: list[dict[str, Any]]) -> list[Event]:
    previous_by_mac = _index_devices_by_mac(previous_devices)
    current_by_mac = _index_devices_by_mac(current_devices)
    now = _now_aware()

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

        previous_effective_state = _resolve_previous_effective_state(
            previous=previous,
            mac=mac,
            now=now,
            logger_level=logging.DEBUG,
        )
        current_fused_state = _derive_device_state(current)
        extended_events = _extended_field_changes(
            mac=mac,
            previous=previous,
            current=current,
            previous_effective_state=previous_effective_state,
            current_state=current_fused_state,
        )
        if extended_events:
            events.extend(extended_events)

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
        if previous_effective_state != current_fused_state:
            changed_count += 1
            logger.debug("[arp_state_changed] Fused state changed: %s -> %s", previous_effective_state, current_fused_state)
            event = _build_arp_transition_event(
                "arp_state_changed",
                mac,
                device=current,
                old_key="old_state",
                new_key="new_state",
                old_value=previous_effective_state,
                new_value=current_fused_state,
            )
            events.append(event)
            _log_event(event)

            if current_fused_state in {"online", "offline", "idle"}:
                reason = _device_offline_reason(
                    previous_effective_state,
                    current_fused_state,
                    current_arp_status,
                    current_bridge_host_present,
                )
                if current_fused_state != "offline":
                    reason = _state_reason(current_fused_state, current_arp_status, current_bridge_host_present)
                device_event = {
                    "timestamp": _iso_timestamp(),
                    "event_type": f"device_{current_fused_state}",
                    "type": f"device_{current_fused_state}",
                    "mac": mac,
                    "reason": reason,
                    "old_value": previous_effective_state,
                    "new_value": current_fused_state,
                }
                device_event.update(_event_context(current))
                events.append(device_event)
                _log_event(device_event)

            previous_presence_state, current_presence_state = _sanitize_presence_transition(
                previous_effective_state,
                current_fused_state,
                has_reconnect_evidence=_has_reconnect_evidence(
                    arp_status=current_arp_status,
                    bridge_host_present=current_bridge_host_present,
                    evidence=current.get("evidence") if isinstance(current.get("evidence"), dict) else None,
                ),
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
        logger.exception("diff processing failed with traceback")
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

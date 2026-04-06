from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

app = FastAPI(title="MikroTrack API", version="0.1.0")


def _persistence_path() -> Path:
    return Path(os.getenv("PERSISTENCE_PATH", "/data/snapshots"))


def _snapshot_files() -> list[Path]:
    path = _persistence_path()
    if not path.exists():
        return []
    return sorted(path.glob("*.json"), reverse=True)


def _load_latest_snapshot() -> tuple[list[dict[str, Any]], float] | tuple[None, None]:
    files = _snapshot_files()
    if not files:
        return None, None

    latest = files[0]
    with latest.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise HTTPException(status_code=500, detail="Invalid snapshot format")

    return payload, latest.stat().st_mtime


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


def _is_active(device: dict[str, Any]) -> bool:
    dhcp_status = str(device.get("dhcp_status", "")).lower()
    arp_status = str(device.get("arp_status", "")).lower()
    arp_flags = device.get("arp_flags") if isinstance(device.get("arp_flags"), dict) else {}

    if bool(arp_flags.get("disabled")) or bool(arp_flags.get("invalid")):
        return False

    if dhcp_status == "bound":
        return True

    return arp_status in {"reachable", "stale"}


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
    snapshot, snapshot_mtime = _load_latest_snapshot()
    if snapshot is None:
        return {"items": []}

    now = datetime.now(UTC)
    events = _read_events()
    last_change_by_mac: dict[str, datetime] = {}

    for event in events:
        mac = str(event.get("mac", "")).strip()
        timestamp = _parse_ts(str(event.get("timestamp", "")))
        if not mac or timestamp is None:
            continue

        previous = last_change_by_mac.get(mac)
        if previous is None or timestamp > previous:
            last_change_by_mac[mac] = timestamp

    snapshot_ts = datetime.fromtimestamp(snapshot_mtime, tz=UTC)
    items: list[dict[str, Any]] = []

    for device in snapshot:
        if not isinstance(device, dict):
            continue

        mac = str(device.get("mac_address", ""))
        last_change = last_change_by_mac.get(mac, snapshot_ts)
        elapsed_seconds = max(0, int((now - last_change).total_seconds()))
        source = device.get("source")
        source_text = "+".join(source) if isinstance(source, list) else str(source or "-")

        dhcp_flags = device.get("dhcp_flags") if isinstance(device.get("dhcp_flags"), dict) else {}
        arp_flags = device.get("arp_flags") if isinstance(device.get("arp_flags"), dict) else {}
        arp_flag_list = [key for key, value in arp_flags.items() if bool(value)]
        active = _is_active(device)

        items.append(
            {
                "mac": mac,
                "ip": device.get("ip_address", ""),
                "hostname": device.get("host_name", ""),
                "comments": _comment_text(
                    str(device.get("dhcp_comment", "")),
                    str(device.get("arp_comment", "")),
                ),
                "flags": {
                    "source": source_text,
                    "ip_assignment": "dynamic" if bool(dhcp_flags.get("dynamic")) else "static",
                    "dhcp_status": str(device.get("dhcp_status", "unknown")),
                    "arp_flags": ", ".join(arp_flag_list) if arp_flag_list else "-",
                    "state": "active" if active else "inactive",
                },
                "active": active,
                "last_change": last_change.isoformat(),
                "elapsed_seconds": elapsed_seconds,
            }
        )

    items.sort(key=lambda item: (not bool(item.get("active")), int(item.get("elapsed_seconds", 0))))
    return {"items": items, "generated_at": now.isoformat()}

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("mikrotrack")
_persistence_path = Path("/data/snapshots")
_retention_days = 7


def configure_persistence(path: str, retention_days: int) -> None:
    global _persistence_path, _retention_days
    _persistence_path = Path(path)
    _retention_days = retention_days


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


def save_snapshot(devices: list[dict]) -> None:
    _persistence_path.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
    file_path = _persistence_path / filename

    with file_path.open("w", encoding="utf-8") as snapshot_file:
        json.dump(devices, snapshot_file, indent=2, ensure_ascii=False)

    file_size = file_path.stat().st_size
    logger.info("Snapshot saved: %s", file_path)
    logger.debug("Snapshot file size: %d bytes", file_size)
    logger.debug("Snapshot device count: %d", len(devices))

    removed_count = _cleanup_old_snapshots()
    logger.info("Retention cleanup done: removed %d files", removed_count)

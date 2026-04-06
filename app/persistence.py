from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from app.exceptions import MikroTrackError

logger = logging.getLogger("mikrotrack")
_persistence_path = Path("/data/snapshots")
_retention_days = 7
_LOW_DISK_SPACE_THRESHOLD_BYTES = 50 * 1024 * 1024


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


def save_snapshot(devices: list[dict]) -> None:
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

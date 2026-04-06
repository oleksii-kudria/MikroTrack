from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="MikroTrack API", version="0.1.0")


def _persistence_path() -> Path:
    return Path(os.getenv("PERSISTENCE_PATH", "/data/snapshots"))


def _snapshot_files() -> list[Path]:
    path = _persistence_path()
    if not path.exists():
        return []
    return sorted(path.glob("*.json"), reverse=True)


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

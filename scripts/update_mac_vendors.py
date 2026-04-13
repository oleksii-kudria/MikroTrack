#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.mac_metadata import _VENDOR_MAP_PATH, build_vendor_payload  # noqa: E402

_OUI_PATTERN = re.compile(r"^[0-9A-F]{6}$")


def _normalize_vendors(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError("vendors payload must be an object")

    normalized: dict[str, str] = {}
    for key, value in raw.items():
        oui = str(key).strip().upper().replace(":", "").replace("-", "")
        if not _OUI_PATTERN.fullmatch(oui):
            continue
        if not isinstance(value, str):
            continue
        vendor = value.strip()
        if not vendor:
            continue
        normalized[oui] = vendor
    return normalized


def _load_input(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("vendors"), dict):
        return _normalize_vendors(payload["vendors"])
    return _normalize_vendors(payload)


def _atomic_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=path.parent, encoding="utf-8"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        tmp_path = Path(handle.name)
    tmp_path.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update offline MAC vendors database")
    parser.add_argument(
        "--from-json",
        type=Path,
        help="Optional JSON file with vendors map or mac_vendors.json-compatible payload",
    )
    parser.add_argument("--source", default="offline snapshot", help="source field value")
    args = parser.parse_args()

    src_path = args.from_json or _VENDOR_MAP_PATH
    vendors = _load_input(src_path)
    payload = build_vendor_payload(vendors, source=args.source)
    _atomic_write(_VENDOR_MAP_PATH, payload)
    print(f"Updated {_VENDOR_MAP_PATH} with {len(vendors)} vendors")


if __name__ == "__main__":
    main()

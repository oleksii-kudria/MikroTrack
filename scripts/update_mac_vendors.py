#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("mac_vendor_update")
DEFAULT_IEEE_OUI_URL = "https://standards-oui.ieee.org/oui/oui.csv"
DEFAULT_TIMEOUT_SECONDS = 20.0
OUI_PATTERN = re.compile(r"^[0-9A-F]{6}$")
TXT_HEX_LINE_PATTERN = re.compile(
    r"^\s*([0-9A-F]{2}(?:[-:][0-9A-F]{2}){2})\s+\(hex\)\s+(.+?)\s*$",
    re.IGNORECASE,
)

ROOT = Path(__file__).resolve().parents[1]
VENDOR_MAP_PATH = ROOT / "app" / "data" / "mac_vendors.json"


def _normalize_oui(raw_oui: str) -> str:
    return raw_oui.strip().upper().replace("-", "").replace(":", "")


def download_registry(url: str, timeout_seconds: float) -> str:
    LOGGER.info("Downloading IEEE OUI registry")
    request = urllib.request.Request(url=url, headers={"User-Agent": "MikroTrack/1.0"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        charset = response.headers.get_content_charset("utf-8")
        return response.read().decode(charset, errors="replace")


def parse_ieee_csv(payload_text: str) -> dict[str, str]:
    vendors: dict[str, str] = {}
    reader = csv.DictReader(StringIO(payload_text))

    for row in reader:
        if not isinstance(row, dict):
            continue
        assignment = row.get("Assignment") or row.get("assignment") or ""
        organization = (
            row.get("Organization Name")
            or row.get("organizationName")
            or row.get("Registry")
            or ""
        )
        oui = _normalize_oui(assignment)
        vendor = str(organization).strip()
        if OUI_PATTERN.fullmatch(oui) and vendor:
            vendors[oui] = vendor

    return vendors


def parse_ieee_txt(payload_text: str) -> dict[str, str]:
    vendors: dict[str, str] = {}
    for line in payload_text.splitlines():
        match = TXT_HEX_LINE_PATTERN.match(line)
        if not match:
            continue
        oui = _normalize_oui(match.group(1))
        vendor = match.group(2).strip()
        if OUI_PATTERN.fullmatch(oui) and vendor:
            vendors[oui] = vendor
    return vendors


def parse_ieee_registry(payload_text: str) -> dict[str, str]:
    csv_vendors = parse_ieee_csv(payload_text)
    if csv_vendors:
        return csv_vendors
    return parse_ieee_txt(payload_text)


def validate_vendors(vendors: Any) -> dict[str, str]:
    if not isinstance(vendors, dict) or not vendors:
        raise ValueError("vendors must be a non-empty object")

    validated: dict[str, str] = {}
    for key, value in vendors.items():
        oui = _normalize_oui(str(key))
        if not OUI_PATTERN.fullmatch(oui):
            raise ValueError(f"invalid OUI key: {key}")
        if not isinstance(value, str):
            raise ValueError(f"vendor for {oui} must be string")
        vendor = value.strip()
        if not vendor:
            raise ValueError(f"vendor for {oui} must be non-empty")
        validated[oui] = vendor

    return validated


def build_payload(vendors: dict[str, str], source: str) -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": source,
        "vendors": dict(sorted(vendors.items())),
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as tmp_file:
        json.dump(payload, tmp_file, ensure_ascii=False, indent=2)
        tmp_file.write("\n")
        tmp_path = Path(tmp_file.name)

    tmp_path.replace(path)


def run(url: str, output_path: Path, timeout_seconds: float, source: str) -> int:
    try:
        payload_text = download_registry(url=url, timeout_seconds=timeout_seconds)
        parsed_vendors = parse_ieee_registry(payload_text)
        vendors = validate_vendors(parsed_vendors)
    except (urllib.error.URLError, TimeoutError, OSError):
        LOGGER.error("Failed to download data")
        return 1
    except ValueError as exc:
        LOGGER.error("Failed to parse IEEE OUI registry: %s", exc)
        return 1

    LOGGER.info("Vendors loaded")
    payload = build_payload(vendors=vendors, source=source)
    atomic_write_json(output_path, payload)
    LOGGER.info("mac_vendors.json updated successfully")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download IEEE OUI registry and update local mac_vendors.json"
    )
    parser.add_argument(
        "--url",
        default=os.getenv("IEEE_OUI_URL", DEFAULT_IEEE_OUI_URL),
        help="IEEE OUI registry URL",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=VENDOR_MAP_PATH,
        help="Path to output mac_vendors.json",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--source",
        default="ieee",
        help="source field value for generated JSON",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()
    raise SystemExit(
        run(
            url=args.url,
            output_path=args.output,
            timeout_seconds=args.timeout,
            source=args.source,
        )
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("mikrotrack.mac_metadata")
_VENDOR_MAP_PATH = Path(__file__).resolve().parent / "data" / "mac_vendors.json"


def normalize_mac(mac_raw: Any) -> str:
    return str(mac_raw or "").strip().upper()


def is_random_mac(mac_raw: Any) -> bool:
    mac_text = normalize_mac(mac_raw)
    parts = mac_text.split(":")
    if len(parts) != 6:
        return False

    try:
        first_octet = int(parts[0], 16)
    except ValueError:
        return False

    # Locally administered bit (bit1, where bit0 is multicast bit)
    return bool(first_octet & 0b00000010)


def _oui_key(mac_raw: Any) -> str | None:
    mac_text = normalize_mac(mac_raw)
    parts = mac_text.split(":")
    if len(parts) != 6:
        logger.debug("Invalid MAC format skipped for vendor lookup: %s", mac_text)
        return None

    normalized_parts: list[str] = []
    for part in parts:
        if len(part) != 2:
            logger.debug("Invalid MAC octet skipped for vendor lookup: %s", mac_text)
            return None
        try:
            int(part, 16)
        except ValueError:
            logger.debug("Invalid MAC octet skipped for vendor lookup: %s", mac_text)
            return None
        normalized_parts.append(part)

    return "".join(normalized_parts[:3])


@lru_cache(maxsize=1)
def load_vendor_map() -> dict[str, str]:
    if not _VENDOR_MAP_PATH.exists():
        logger.warning("MAC vendor mapping file is missing: %s", _VENDOR_MAP_PATH)
        return {}

    try:
        payload = json.loads(_VENDOR_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to load MAC vendor mapping file: %s", _VENDOR_MAP_PATH)
        return {}

    if not isinstance(payload, dict):
        logger.warning("Invalid MAC vendor mapping payload type: %s", type(payload).__name__)
        return {}

    vendor_map: dict[str, str] = {}
    for key, value in payload.items():
        normalized_key = str(key).strip().upper().replace(":", "").replace("-", "")
        if len(normalized_key) != 6:
            continue
        vendor_text = str(value).strip()
        if not vendor_text:
            continue
        vendor_map[normalized_key] = vendor_text

    logger.info(
        "MAC vendor mapping loaded from %s with %d OUI entries",
        _VENDOR_MAP_PATH,
        len(vendor_map),
    )
    return vendor_map


def lookup_mac_vendor(mac_raw: Any) -> str | None:
    if is_random_mac(mac_raw):
        return None

    oui_key = _oui_key(mac_raw)
    if oui_key is None:
        return None

    vendor = load_vendor_map().get(oui_key)
    if vendor is None:
        logger.debug("Vendor not found for OUI: %s", oui_key)
    return vendor

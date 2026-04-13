from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("mac_vendor_db")
_VENDOR_MAP_PATH = Path(__file__).resolve().parent / "data" / "mac_vendors.json"
_OUI_PATTERN = re.compile(r"^[0-9A-F]{6}$")


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
    normalized = mac_text.replace(":", "").replace("-", "")
    if len(normalized) != 12:
        logger.debug("Invalid MAC format skipped for vendor lookup: %s", mac_text)
        return None

    if not all(ch in "0123456789ABCDEF" for ch in normalized):
        logger.debug("Invalid MAC format skipped for vendor lookup: %s", mac_text)
        return None

    return normalized[:6]


def _validated_vendors(payload: Any) -> dict[str, str] | None:
    if not isinstance(payload, dict):
        return None

    vendors = payload.get("vendors")
    if not isinstance(vendors, dict):
        return None

    validated: dict[str, str] = {}
    for key, value in vendors.items():
        oui = str(key).strip().upper()
        if not _OUI_PATTERN.fullmatch(oui):
            logger.debug("Skipping invalid OUI key in vendor DB: %s", key)
            continue
        if not isinstance(value, str):
            logger.debug("Skipping invalid vendor value type for OUI %s", oui)
            continue
        vendor = value.strip()
        if not vendor:
            logger.debug("Skipping empty vendor value for OUI %s", oui)
            continue
        validated[oui] = vendor
    return validated


@lru_cache(maxsize=1)
def load_vendor_map() -> dict[str, str]:
    if not _VENDOR_MAP_PATH.exists():
        logger.error("mac_vendors.json not found")
        return {}

    try:
        payload = json.loads(_VENDOR_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.error("invalid JSON format")
        return {}

    vendors = _validated_vendors(payload)
    if vendors is None:
        logger.error("invalid JSON format")
        return {}

    logger.info("Loaded MAC vendors database")
    return vendors


def reload_vendor_map() -> dict[str, str]:
    load_vendor_map.cache_clear()
    return load_vendor_map()


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


def build_vendor_payload(
    vendors: dict[str, str], source: str = "offline snapshot"
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    return {
        "version": 1,
        "updated_at": now,
        "source": source,
        "vendors": dict(sorted(vendors.items())),
    }

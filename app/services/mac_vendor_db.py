from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("mac_vendor_db")
_VENDOR_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "mac_vendors.json"
_OUI_PATTERN = re.compile(r"^[0-9A-F]{6}$")


class MacVendorDBError(RuntimeError):
    """Controlled error raised when local MAC vendors DB cannot be loaded."""


def _normalize_mac(mac: str) -> str:
    return str(mac or "").strip().upper()


def _extract_oui(mac: str) -> str | None:
    normalized = _normalize_mac(mac).replace(":", "").replace("-", "")
    if len(normalized) != 12:
        return None

    if not all(ch in "0123456789ABCDEF" for ch in normalized):
        return None

    return normalized[:6]


def _validate_structure(payload: object) -> dict[str, str] | None:
    if not isinstance(payload, dict):
        return None

    vendors = payload.get("vendors")
    if not isinstance(vendors, dict):
        return None

    validated: dict[str, str] = {}
    for key, value in vendors.items():
        oui = str(key).strip().upper()
        if not _OUI_PATTERN.fullmatch(oui):
            return None
        if not isinstance(value, str):
            return None
        validated[oui] = value.strip()

    return validated


@lru_cache(maxsize=1)
def load() -> dict[str, str]:
    if not _VENDOR_DB_PATH.exists():
        logger.error("mac_vendors.json not found")
        return {}

    try:
        payload = json.loads(_VENDOR_DB_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.error("invalid structure")
        return {}

    vendors = _validate_structure(payload)
    if vendors is None:
        logger.error("invalid structure")
        return {}

    logger.info("Loaded MAC vendors database")
    return vendors


def reload() -> dict[str, str]:
    load.cache_clear()
    return load()


def get_vendor(mac: str) -> str | None:
    oui = _extract_oui(mac)
    if oui is None:
        return None

    return load().get(oui)

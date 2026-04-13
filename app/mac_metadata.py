from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services import mac_vendor_db


load_vendor_map = mac_vendor_db.load
reload_vendor_map = mac_vendor_db.reload
lookup_mac_vendor = mac_vendor_db.get_vendor


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

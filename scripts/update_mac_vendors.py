#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import time
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
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 3.0
MIN_VENDOR_COUNT = 1000
OUI_PATTERN = re.compile(r"^[0-9A-F]{6}$")
PLACEHOLDER_VENDOR_PATTERN = re.compile(r"^IEEE MA-L Vendor \d{5}$", re.IGNORECASE)
TXT_HEX_LINE_PATTERN = re.compile(
    r"^\s*([0-9A-F]{2}(?:[-:][0-9A-F]{2}){2})\s+\(hex\)\s+(.+?)\s*$",
    re.IGNORECASE,
)

ROOT = Path(__file__).resolve().parents[1]
VENDOR_MAP_PATH = ROOT / "app" / "data" / "mac_vendors.json"


def _normalize_oui(raw_oui: str) -> str:
    return raw_oui.strip().upper().replace("-", "").replace(":", "")


def download_registry(
    url: str,
    timeout_seconds: float,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
) -> str:
    LOGGER.info("Downloading IEEE OUI registry")
    request = urllib.request.Request(url=url, headers={"User-Agent": "MikroTrack/1.0"})
    for attempt in range(1, retry_attempts + 1):
        try:
                with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                    charset = response.headers.get_content_charset("utf-8")
                    headers_get = getattr(response.headers, "get", None)
                    content_type = (
                        headers_get("Content-Type", "") if callable(headers_get) else ""
                    )
                status = getattr(response, "status", "unknown")
                payload = response.read()
                LOGGER.info(
                    "IEEE OUI registry downloaded, bytes=%s, status=%s, content_type=%s, charset=%s",
                    len(payload),
                    status,
                    content_type,
                    charset,
                )
                return payload.decode(charset, errors="replace")
        except urllib.error.HTTPError as exc:
            LOGGER.error(
                "IEEE OUI registry returned HTTP error: status=%s, reason=%s, url=%s",
                exc.code,
                exc.reason,
                url,
            )
            if attempt >= retry_attempts:
                raise
        except TimeoutError:
            LOGGER.error(
                "IEEE OUI registry download timeout: timeout=%ss, url=%s",
                timeout_seconds,
                url,
            )
            if attempt >= retry_attempts:
                raise
        except urllib.error.URLError as exc:
            LOGGER.error(
                "IEEE OUI registry DNS/connection error: error=%s, url=%s",
                exc.reason,
                url,
            )
            if attempt >= retry_attempts:
                raise
        except OSError as exc:
            LOGGER.error(
                "IEEE OUI registry download failed due to OS/network error: error=%s, url=%s",
                exc,
                url,
            )
            if attempt >= retry_attempts:
                raise

        LOGGER.warning(
            "Download attempt failed, attempt=%s/%s, url=%s",
            attempt,
            retry_attempts,
            url,
        )
        if attempt < retry_attempts:
            time.sleep(retry_delay_seconds)

    raise RuntimeError("unreachable")


def parse_ieee_csv(payload_text: str) -> dict[str, str]:
    vendors: dict[str, str] = {}
    reader = csv.DictReader(StringIO(payload_text))
    fields = reader.fieldnames or []
    required_assignment = "Assignment"
    candidate_org_fields = ("Organization Name", "organizationName", "Registry")
    if required_assignment not in fields or not any(
        field in fields for field in candidate_org_fields
    ):
        if len(fields) > 1:
            raise ValueError(f"Unsupported IEEE CSV header, fields={fields}")
        return {}

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
        LOGGER.info("IEEE OUI registry parsed, entries=%s", len(csv_vendors))
        return csv_vendors
    txt_vendors = parse_ieee_txt(payload_text)
    LOGGER.info("IEEE OUI registry parsed, entries=%s", len(txt_vendors))
    return txt_vendors


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


def _is_placeholder_vendor_name(vendor: str, oui: str) -> bool:
    normalized_vendor = vendor.strip()
    if PLACEHOLDER_VENDOR_PATTERN.fullmatch(normalized_vendor):
        return True
    normalized_lower = normalized_vendor.lower()
    return oui.lower() in normalized_lower and "vendor" in normalized_lower


def sanity_check_vendors(vendors: dict[str, str]) -> None:
    if not vendors:
        raise ValueError("vendors list is empty")
    if len(vendors) < MIN_VENDOR_COUNT:
        raise ValueError(
            f"vendors count too low: count={len(vendors)}, min_required={MIN_VENDOR_COUNT}"
        )

    placeholder_count = sum(
        1 for oui, vendor in vendors.items() if _is_placeholder_vendor_name(vendor, oui)
    )
    if placeholder_count > 0:
        raise ValueError(
            f"Placeholder vendor names detected, aborting update: count={placeholder_count}"
        )

    if not any("apple" in vendor.lower() for vendor in vendors.values()):
        raise ValueError("Known vendor not found in dataset: Apple")


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


def run(
    url: str,
    output_path: Path,
    timeout_seconds: float,
    source: str,
    input_file: Path | None = None,
) -> int:
    LOGGER.info(
        "Starting MAC vendors update, source_url=%s, output=%s, timeout=%s, input_file=%s",
        url,
        output_path,
        timeout_seconds,
        input_file,
    )
    try:
        if input_file:
            LOGGER.info(
                "Loading IEEE OUI registry from local file, path=%s",
                input_file,
            )
            payload_text = input_file.read_text(encoding="utf-8")
        else:
            payload_text = download_registry(url=url, timeout_seconds=timeout_seconds)
        parsed_vendors = parse_ieee_registry(payload_text)
        vendors = validate_vendors(parsed_vendors)
        sanity_check_vendors(vendors)
    except FileNotFoundError:
        LOGGER.error("Input file not found: path=%s", input_file)
        return 1
    except (urllib.error.URLError, TimeoutError, OSError):
        LOGGER.error(
            "Failed to download IEEE OUI registry: url=%s, error_type=%s",
            url,
            "network",
        )
        return 1
    except ValueError as exc:
        LOGGER.error("Failed to parse/validate IEEE OUI registry: %s", exc)
        return 1

    LOGGER.info("Vendors loaded, count=%s", len(vendors))
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
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Read IEEE OUI registry from local file and skip network download",
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
            input_file=args.input_file,
        )
    )


if __name__ == "__main__":
    main()

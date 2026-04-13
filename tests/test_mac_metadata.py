from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from app import mac_metadata
from app.services import mac_vendor_db


@pytest.fixture(autouse=True)
def _clear_vendor_cache() -> None:
    mac_vendor_db.load.cache_clear()
    yield
    mac_vendor_db.load.cache_clear()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_vendor_map_with_valid_file(tmp_path: Path, monkeypatch) -> None:
    vendor_file = tmp_path / "mac_vendors.json"
    _write_json(
        vendor_file,
        {
            "version": 1,
            "updated_at": "2026-04-13T12:00:00+03:00",
            "source": "offline snapshot",
            "vendors": {"D850E6": "Apple, Inc."},
        },
    )

    monkeypatch.setattr(mac_vendor_db, "_VENDOR_DB_PATH", vendor_file)

    assert mac_metadata.load_vendor_map() == {"D850E6": "Apple, Inc."}


def test_load_vendor_map_when_file_missing(tmp_path: Path, monkeypatch, caplog) -> None:
    vendor_file = tmp_path / "missing.json"
    monkeypatch.setattr(mac_vendor_db, "_VENDOR_DB_PATH", vendor_file)
    caplog.set_level(logging.ERROR, logger="mac_vendor_db")

    assert mac_metadata.load_vendor_map() == {}
    assert "mac_vendors.json not found" in caplog.text


def test_load_vendor_map_when_json_invalid(tmp_path: Path, monkeypatch, caplog) -> None:
    vendor_file = tmp_path / "mac_vendors.json"
    vendor_file.write_text("{ invalid", encoding="utf-8")

    monkeypatch.setattr(mac_vendor_db, "_VENDOR_DB_PATH", vendor_file)
    caplog.set_level(logging.ERROR, logger="mac_vendor_db")

    assert mac_metadata.load_vendor_map() == {}
    assert "invalid structure" in caplog.text


def test_load_vendor_map_when_structure_invalid(tmp_path: Path, monkeypatch, caplog) -> None:
    vendor_file = tmp_path / "mac_vendors.json"
    _write_json(vendor_file, {"vendors": {"BAD-KEY": "Vendor"}})

    monkeypatch.setattr(mac_vendor_db, "_VENDOR_DB_PATH", vendor_file)
    caplog.set_level(logging.ERROR, logger="mac_vendor_db")

    assert mac_metadata.load_vendor_map() == {}
    assert "invalid structure" in caplog.text


def test_lookup_by_oui(tmp_path: Path, monkeypatch) -> None:
    vendor_file = tmp_path / "mac_vendors.json"
    _write_json(
        vendor_file,
        {
            "version": 1,
            "updated_at": "2026-04-13T12:00:00+03:00",
            "source": "offline snapshot",
            "vendors": {"08BBCC": "Vendor B"},
        },
    )

    monkeypatch.setattr(mac_vendor_db, "_VENDOR_DB_PATH", vendor_file)

    assert mac_metadata.lookup_mac_vendor("08:bb:cc:11:22:33") == "Vendor B"
    assert mac_metadata.lookup_mac_vendor("11:22:33:11:22:33") is None

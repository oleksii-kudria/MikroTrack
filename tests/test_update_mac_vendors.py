from __future__ import annotations

import importlib.util
import json
import urllib.error
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_mac_vendors.py"
SPEC = importlib.util.spec_from_file_location("update_mac_vendors", MODULE_PATH)
assert SPEC and SPEC.loader
update_mac_vendors = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(update_mac_vendors)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self._content = content.encode("utf-8")
        self.headers = self

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    def get_content_charset(self, default: str) -> str:
        return default

    def read(self) -> bytes:
        return self._content


def test_download_ok(monkeypatch) -> None:
    def _fake_urlopen(request, timeout):  # noqa: ANN001
        return _FakeResponse(
            "Registry,Assignment,Organization Name\nMA-L,00-11-22,Vendor A\n"
        )

    monkeypatch.setattr(update_mac_vendors.urllib.request, "urlopen", _fake_urlopen)

    payload = update_mac_vendors.download_registry("https://example.com/oui.csv", 2.0)

    assert "Vendor A" in payload


def test_download_fail(monkeypatch, tmp_path: Path) -> None:
    original_content = '{"version":1,"updated_at":"2026-01-01T00:00:00+00:00","source":"x","vendors":{"001122":"Old"}}\n'
    output = tmp_path / "mac_vendors.json"
    output.write_text(original_content, encoding="utf-8")

    def _fake_download(url: str, timeout_seconds: float) -> str:
        raise urllib.error.URLError("network error")

    monkeypatch.setattr(update_mac_vendors, "download_registry", _fake_download)

    code = update_mac_vendors.run(
        url="https://example.com/oui.csv",
        output_path=output,
        timeout_seconds=2.0,
        source="ieee",
    )

    assert code == 1
    assert output.read_text(encoding="utf-8") == original_content


def test_parse_and_normalize_from_csv() -> None:
    payload = "Registry,Assignment,Organization Name\nMA-L,00-11-22,Vendor A\n"

    parsed = update_mac_vendors.parse_ieee_registry(payload)

    assert parsed == {"001122": "Vendor A"}


def test_parse_from_txt() -> None:
    payload = "00-11-22   (hex)\tVendor A\nAA-BB-CC   (hex)\tVendor B\n"

    parsed = update_mac_vendors.parse_ieee_registry(payload)

    assert parsed == {"001122": "Vendor A", "AABBCC": "Vendor B"}


def test_save_builds_valid_json(tmp_path: Path) -> None:
    output = tmp_path / "mac_vendors.json"

    payload = update_mac_vendors.build_payload({"AABBCC": "Vendor B"}, source="ieee")
    update_mac_vendors.atomic_write_json(output, payload)

    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["version"] == 1
    assert loaded["source"] == "ieee"
    assert loaded["vendors"] == {"AABBCC": "Vendor B"}


def test_validate_non_empty_and_types() -> None:
    with pytest.raises(ValueError):
        update_mac_vendors.validate_vendors({})

    with pytest.raises(ValueError):
        update_mac_vendors.validate_vendors({"001122": 123})

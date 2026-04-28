from __future__ import annotations

from pathlib import Path


TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "web" / "templates" / "timeline.html"


def test_hostname_vendor_is_rendered_in_hostname_cell_without_extra_vendor_column():
    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert 'data-sort-key="hostname"' in content
    assert 'data-sort-key="vendor"' not in content
    assert ">Vendor<" not in content
    assert "hostname-vendor" in content


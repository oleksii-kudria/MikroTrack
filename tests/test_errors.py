from __future__ import annotations

import ssl

from app.errors import (
    UnexpectedMikroTikResponseError,
    format_error,
    to_mikrotrack_error,
)


def test_format_error_connection_error() -> None:
    payload = format_error(ConnectionRefusedError("connection refused"))

    assert payload["error"] == "connection_error"
    assert "Unable to connect" in payload["message"]


def test_format_error_tls_error() -> None:
    payload = format_error(ssl.SSLError("tls handshake failure"))

    assert payload["error"] == "tls_error"


def test_format_error_authentication_failed() -> None:
    payload = format_error(RuntimeError("invalid username or password"))

    assert payload["error"] == "authentication_failed"


def test_format_error_access_denied() -> None:
    payload = format_error(RuntimeError("access denied"))

    assert payload["error"] == "access_denied"


def test_format_error_unexpected_response() -> None:
    payload = format_error(UnexpectedMikroTikResponseError("bad payload"))

    assert payload["error"] == "unexpected_response"


def test_to_mikrotrack_error_uses_error_category() -> None:
    wrapped = to_mikrotrack_error(ConnectionRefusedError("connection refused"))

    assert wrapped.error_code == "connection_error"

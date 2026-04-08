from __future__ import annotations

import errno
import socket
import ssl
from typing import Any

from routeros_api.exceptions import (
    RouterOsApiCommunicationError,
    RouterOsApiConnectionClosedError,
    RouterOsApiConnectionError,
    RouterOsApiFatalCommunicationError,
    RouterOsApiParsingError,
)

from app.exceptions import MikroTrackError


class DhcpFetchError(RuntimeError):
    """Raised when DHCP lease retrieval fails after API connection succeeded."""


class EmptyDhcpLeasesError(RuntimeError):
    """Raised when MikroTik returns no DHCP lease records."""


class UnexpectedMikroTikResponseError(RuntimeError):
    """Raised when MikroTik API returns a response in an unexpected format."""


def _message(exception: Exception) -> str:
    return str(exception).strip().lower()


def _is_connection_error(exception: Exception, error_message: str) -> bool:
    if isinstance(
        exception,
        (
            ConnectionRefusedError,
            TimeoutError,
            socket.timeout,
            socket.gaierror,
            RouterOsApiConnectionError,
        ),
    ):
        return True

    if isinstance(exception, OSError) and not isinstance(exception, ssl.SSLError):
        return True

    return any(
        marker in error_message
        for marker in (
            "connection refused",
            "timed out",
            "timeout",
            "no route to host",
            "name or service not known",
            "temporary failure in name resolution",
            "network is unreachable",
            "cannot assign requested address",
        )
    )


def _is_tls_error(exception: Exception, error_message: str) -> bool:
    if isinstance(exception, ssl.SSLError):
        return True

    return any(
        marker in error_message
        for marker in (
            "tls",
            "ssl",
            "handshake",
            "certificate verify failed",
            "self signed certificate",
            "hostname mismatch",
            "wrong version number",
            "unknown ca",
        )
    )


def _is_authentication_error(error_message: str) -> bool:
    return any(
        marker in error_message
        for marker in (
            "invalid user name or password",
            "invalid username or password",
            "authentication failed",
            "login failure",
            "wrong username or password",
            "cannot log in",
        )
    )


def _is_access_denied(exception: Exception, error_message: str) -> bool:
    if "not allowed (9)" in error_message or "not enough permissions" in error_message:
        return True

    if any(marker in error_message for marker in ("access denied", "forbidden")):
        return True

    return isinstance(exception, RouterOsApiConnectionClosedError) and any(
        marker in error_message
        for marker in (
            "connection closed",
            "closed by remote host",
            "connection reset by peer",
            "unexpected eof",
            "eof occurred in violation of protocol",
        )
    )


def format_error(exception: Exception) -> dict[str, str]:
    """Return a user-friendly error payload for known MikroTik failure scenarios."""

    error_message = _message(exception)

    if _is_connection_error(exception, error_message):
        os_error_number = getattr(exception, "errno", None)
        if os_error_number in (errno.ECONNREFUSED, errno.ETIMEDOUT, errno.EHOSTUNREACH, errno.ENETUNREACH):
            return {
                "error": "connection_error",
                "message": "Unable to connect to MikroTik API. Check IP/port.",
                "recommendation": "Verify host, port, firewall, and api/api-ssl service status.",
            }

        return {
            "error": "connection_error",
            "message": "Unable to connect to MikroTik API. Check IP/port.",
            "recommendation": "Verify host, port, firewall, and api/api-ssl service status.",
        }

    if _is_tls_error(exception, error_message):
        return {
            "error": "tls_error",
            "message": "TLS connection failed. Verify certificates.",
            "recommendation": "Check certificate validity, trust chain, and api-ssl TLS configuration.",
        }

    if _is_authentication_error(error_message):
        return {
            "error": "authentication_failed",
            "message": "Authentication failed. Verify credentials.",
            "recommendation": "Verify username/password and account status.",
        }

    if _is_access_denied(exception, error_message):
        return {
            "error": "access_denied",
            "message": "MikroTik API-SSL access denied.",
            "recommendation": (
                "Ensure collector IP is allowed in /ip service api-ssl address and user has required permissions."
            ),
        }

    if isinstance(exception, (RouterOsApiCommunicationError, RouterOsApiFatalCommunicationError, RouterOsApiParsingError)):
        return {
            "error": "api_protocol_error",
            "message": "MikroTik API protocol error.",
            "recommendation": "Verify RouterOS/API compatibility and service health.",
        }

    if isinstance(exception, DhcpFetchError):
        return {
            "error": "api_protocol_error",
            "message": "Connected to MikroTik, but failed to retrieve DHCP leases.",
            "recommendation": "Verify read access and DHCP configuration.",
        }

    if isinstance(exception, EmptyDhcpLeasesError):
        return {
            "error": "api_protocol_error",
            "message": "No DHCP leases were returned.",
            "recommendation": "Verify DHCP server is running and has active leases.",
        }

    if isinstance(exception, UnexpectedMikroTikResponseError):
        return {
            "error": "unexpected_response",
            "message": "Unexpected response from MikroTik API.",
            "recommendation": "Verify RouterOS compatibility and API response format.",
        }

    return {
        "error": "api_protocol_error",
        "message": "MikroTik API protocol error.",
        "recommendation": "Review connection settings and RouterOS API configuration.",
    }


def to_mikrotrack_error(exception: Exception) -> MikroTrackError:
    """Wrap exception into MikroTrackError using a known user-friendly payload."""

    payload: dict[str, Any] = format_error(exception)
    return MikroTrackError(
        error_code=payload["error"],
        message=payload["message"],
        recommendation=payload["recommendation"],
        original_exception=exception,
    )

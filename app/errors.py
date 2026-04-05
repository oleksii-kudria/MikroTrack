from __future__ import annotations

import errno
import socket
import ssl
from typing import Any


class DhcpFetchError(RuntimeError):
    """Raised when DHCP lease retrieval fails after API connection succeeded."""


class EmptyDhcpLeasesError(RuntimeError):
    """Raised when MikroTik returns no DHCP lease records."""


class UnexpectedMikroTikResponseError(RuntimeError):
    """Raised when MikroTik API returns a response in an unexpected format."""


def format_error(exception: Exception) -> dict[str, str]:
    """Return a user-friendly error payload for known MikroTik failure scenarios."""

    error_message = str(exception).lower()

    if isinstance(exception, ConnectionRefusedError) or "connection refused" in error_message:
        return {
            "error_code": "CONNECTION_REFUSED",
            "message": "Failed to connect to MikroTik API SSL: TCP connection was refused.",
            "recommendation": (
                "Verify that api-ssl is enabled, correct port is used, "
                "and firewall allows access."
            ),
        }

    if isinstance(exception, (TimeoutError, socket.timeout)) or "timed out" in error_message:
        return {
            "error_code": "CONNECTION_TIMEOUT",
            "message": "Connection to MikroTik API SSL timed out.",
            "recommendation": "Verify network connectivity, IP address, and allowed address list.",
        }

    if isinstance(exception, ssl.SSLCertVerificationError) or any(
        marker in error_message
        for marker in (
            "certificate verify failed",
            "self signed certificate",
            "hostname mismatch",
        )
    ):
        return {
            "error_code": "SSL_CERT_VERIFICATION_FAILED",
            "message": "SSL certificate verification failed.",
            "recommendation": (
                "Verify certificate validity or disable verification for lab environments."
            ),
        }

    if isinstance(exception, ssl.SSLError) and any(
        marker in error_message
        for marker in ("handshake", "tlsv1", "wrong version number", "sslv3")
    ):
        return {
            "error_code": "SSL_HANDSHAKE_FAILURE",
            "message": "Failed to establish SSL/TLS session with MikroTik API SSL.",
            "recommendation": "Verify certificate is generated and assigned to api-ssl service.",
        }

    if any(
        marker in error_message
        for marker in (
            "invalid user name or password",
            "invalid username or password",
            "authentication failed",
            "login failure",
        )
    ):
        return {
            "error_code": "AUTHENTICATION_FAILED",
            "message": "Authentication failed for MikroTik user.",
            "recommendation": "Verify username and password.",
        }

    if "not allowed (9)" in error_message or "not enough permissions" in error_message:
        return {
            "error_code": "INSUFFICIENT_PERMISSIONS",
            "message": "User does not have sufficient permissions for API access.",
            "recommendation": "Ensure user group has 'read' and 'api' policies.",
        }

    if isinstance(exception, DhcpFetchError):
        return {
            "error_code": "DHCP_FETCH_FAILED",
            "message": "Connected to MikroTik, but failed to retrieve DHCP leases.",
            "recommendation": "Verify read access and DHCP configuration.",
        }

    if isinstance(exception, EmptyDhcpLeasesError):
        return {
            "error_code": "EMPTY_DHCP_RESULT",
            "message": "No DHCP leases were returned.",
            "recommendation": "Verify DHCP server is running and has active leases.",
        }

    if isinstance(exception, UnexpectedMikroTikResponseError):
        return {
            "error_code": "UNEXPECTED_RESPONSE",
            "message": "Unexpected response from MikroTik API.",
            "recommendation": "Verify RouterOS compatibility and API response.",
        }

    os_error_number = getattr(exception, "errno", None)
    if os_error_number == errno.ECONNREFUSED:
        return {
            "error_code": "CONNECTION_REFUSED",
            "message": "Failed to connect to MikroTik API SSL: TCP connection was refused.",
            "recommendation": (
                "Verify that api-ssl is enabled, correct port is used, "
                "and firewall allows access."
            ),
        }

    return {
        "error_code": "UNEXPECTED_ERROR",
        "message": "Unexpected response from MikroTik API.",
        "recommendation": "Verify RouterOS compatibility and API response.",
    }


def error_summary(exception: Exception) -> tuple[str, str, str]:
    """Convenience tuple for logging and CLI output."""

    payload: dict[str, Any] = format_error(exception)
    return (
        str(payload["error_code"]),
        str(payload["message"]),
        str(payload["recommendation"]),
    )

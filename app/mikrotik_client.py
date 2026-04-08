from __future__ import annotations

import logging
from typing import Any

import routeros_api

from app.errors import to_mikrotrack_error


class MikroTikClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 8729,
        use_ssl: bool = True,
        ssl_verify: bool = False,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.ssl_verify = ssl_verify

        self._connection: routeros_api.RouterOsApiPool | None = None
        self.api: Any = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self) -> None:
        self.logger.info("Connecting to MikroTik %s:%s", self.host, self.port)
        self.logger.debug(
            "Connection settings: host=%s, port=%s, username=%s, use_ssl=%s, ssl_verify=%s",
            self.host,
            self.port,
            self.username,
            self.use_ssl,
            self.ssl_verify,
        )
        try:
            self._connection = routeros_api.RouterOsApiPool(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                use_ssl=self.use_ssl,
                ssl_verify=self.ssl_verify,
                plaintext_login=True,
            )
            self.api = self._connection.get_api()
            self.logger.info("Connected to MikroTik API")
            self.logger.debug("RouterOS API session initialized")
        except Exception as error:
            wrapped_error = to_mikrotrack_error(error)
            self.logger.error(
                "MikroTik connection failed: %s %s:%s",
                wrapped_error.error_code,
                self.host,
                self.port,
            )
            self.disconnect()
            raise wrapped_error from error

    def disconnect(self) -> None:
        if self._connection is None:
            return

        try:
            self._connection.disconnect()
            self.logger.info("Disconnected from MikroTik API")
        except Exception:
            self.logger.exception("Failed to disconnect cleanly from MikroTik API")
        finally:
            self._connection = None
            self.api = None
            self.logger.debug("Client state has been reset after disconnect")

    def get_resource(self, path: str) -> Any:
        if self.api is None:
            raise RuntimeError("MikroTik API is not connected")
        self.logger.debug("Requesting API resource path: %s", path)
        return self.api.get_resource(path)

    def __enter__(self) -> "MikroTikClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

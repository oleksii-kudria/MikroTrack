from __future__ import annotations

import json
import logging
import sys

from app.collector import collect_dhcp_leases
from app.config import load_config
from app.errors import to_mikrotrack_error
from app.exceptions import MikroTrackError
from app.logging_config import setup_logging
from app.mikrotik_client import MikroTikClient


def _debug_log_exception(logger: logging.Logger, error: MikroTrackError) -> None:
    if error.original_exception is None:
        return

    original_exception = error.original_exception
    logger.debug(
        "Raw exception details",
        exc_info=(
            type(original_exception),
            original_exception,
            original_exception.__traceback__,
        ),
    )


def main() -> None:
    try:
        config = load_config()
    except Exception as error:
        setup_logging("INFO")
        logger = logging.getLogger("mikrotrack")
        wrapped_error = to_mikrotrack_error(error)
        logger.error("[%s] %s", wrapped_error.error_code, wrapped_error.message)
        logger.error("Recommendation: %s", wrapped_error.recommendation)
        _debug_log_exception(logger, wrapped_error)
        sys.exit(1)

    setup_logging(config.log_level)
    logger = logging.getLogger("mikrotrack")

    try:
        with MikroTikClient(
            host=config.mikrotik_host,
            port=config.mikrotik_port,
            username=config.mikrotik_username,
            password=config.mikrotik_password,
            use_ssl=config.mikrotik_use_ssl,
            ssl_verify=config.mikrotik_ssl_verify,
        ) as client:
            leases = collect_dhcp_leases(client)
            logger.info("Collected %d DHCP lease records", len(leases))
            print(json.dumps(leases, ensure_ascii=False, indent=2))
    except MikroTrackError as error:
        logger.error("[%s] %s", error.error_code, error.message)
        logger.error("Recommendation: %s", error.recommendation)
        _debug_log_exception(logger, error)
        sys.exit(1)
    except Exception as error:
        wrapped_error = to_mikrotrack_error(error)
        logger.error("[%s] %s", wrapped_error.error_code, wrapped_error.message)
        logger.error("Recommendation: %s", wrapped_error.recommendation)
        _debug_log_exception(logger, wrapped_error)
        sys.exit(1)


if __name__ == "__main__":
    main()

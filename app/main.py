from __future__ import annotations

import json
import logging
import sys

from app.collector import get_arp_entries, get_dhcp_leases
from app.config import load_config
from app.device_builder import build_devices
from app.errors import to_mikrotrack_error
from app.exceptions import MikroTrackError
from app.logging_config import setup_logging
from app.mikrotik_client import MikroTikClient
from app.sanitizer import sanitize


def _debug_log_exception(logger: logging.Logger, error: MikroTrackError) -> None:
    if error.original_exception is None:
        return

    original_exception = error.original_exception
    logger.debug("Raw exception: %s", sanitize(str(original_exception)))


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
    logger.info("MikroTrack application started")
    logger.debug(
        (
            "Loaded config: host=%s, port=%s, username=%s, use_ssl=%s, "
            "ssl_verify=%s, log_level=%s, print_result_to_stdout=%s"
        ),
        config.mikrotik_host,
        config.mikrotik_port,
        config.mikrotik_username,
        config.mikrotik_use_ssl,
        config.mikrotik_ssl_verify,
        config.log_level,
        config.print_result_to_stdout,
    )

    try:
        with MikroTikClient(
            host=config.mikrotik_host,
            port=config.mikrotik_port,
            username=config.mikrotik_username,
            password=config.mikrotik_password,
            use_ssl=config.mikrotik_use_ssl,
            ssl_verify=config.mikrotik_ssl_verify,
        ) as client:
            dhcp = get_dhcp_leases(client)
            arp = get_arp_entries(client)
            devices = build_devices(dhcp, arp)

            logger.info("Collected %d DHCP lease records", len(dhcp))
            logger.info("Collected %d ARP records", len(arp))
            logger.info("Built %d devices", len(devices))
            if config.print_result_to_stdout:
                logger.debug("Printing JSON result to stdout")
                sys.stdout.write(f"{json.dumps(devices, ensure_ascii=False, indent=2)}\n")
            else:
                logger.info("PRINT_RESULT_TO_STDOUT is disabled, skipping JSON output")
        logger.info("MikroTrack application finished successfully")
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

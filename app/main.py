from __future__ import annotations

import json
import logging
import signal
import sys
import threading
import time
from types import FrameType

import uvicorn

from app.collector import get_arp_entries, get_bridge_hosts, get_dhcp_leases, get_interface_macs
from app.config import Config, load_config
from app.device_builder import build_devices
from app.errors import to_mikrotrack_error
from app.exceptions import MikroTrackError
from app.logging_config import setup_logging
from app.mikrotik_client import MikroTikClient
from app.persistence import configure_persistence, save_snapshot, validate_persistence
from app.sanitizer import sanitize

RETRY_BACKOFF_SECONDS = 10


def _debug_log_exception(logger: logging.Logger, error: MikroTrackError) -> None:
    if error.original_exception is None:
        return

    original_exception = error.original_exception
    logger.debug("Raw exception: %s", sanitize(str(original_exception)))


def _run_once(config: Config, logger: logging.Logger) -> list[dict[str, object]]:
    logger.info("Starting collection cycle")
    cycle_started_at = time.monotonic()
    logger.debug("Collecting DHCP leases")
    with MikroTikClient(
        host=config.mikrotik_host,
        port=config.mikrotik_port,
        username=config.mikrotik_username,
        password=config.mikrotik_password,
        use_ssl=config.mikrotik_use_ssl,
        ssl_verify=config.mikrotik_ssl_verify,
    ) as client:
        dhcp = get_dhcp_leases(client)
        logger.debug("Collecting ARP entries")
        arp = get_arp_entries(client)
        logger.debug("Collecting bridge host entries")
        bridge_hosts = get_bridge_hosts(client)
        logger.debug("Collecting local interface MAC entries")
        interface_macs = get_interface_macs(client)
        logger.debug("Building devices from collected data")
        devices = build_devices(dhcp, arp, bridge_hosts, interface_macs)

    logger.info("Collected %d DHCP lease records", len(dhcp))
    logger.info("Collected %d ARP records", len(arp))
    logger.info("Collected %d bridge host records", len(bridge_hosts))
    logger.info("Collected %d interface MAC records", len(interface_macs))
    logger.info("Built %d devices", len(devices))

    elapsed = time.monotonic() - cycle_started_at
    logger.info("Collection finished")
    logger.debug("Collection cycle duration: %.2fs", elapsed)
    return devices



def _run_api_server(config: Config, logger: logging.Logger) -> threading.Thread:
    def _serve() -> None:
        uvicorn.run(
            "app.api.main:app",
            host=config.api_host,
            port=config.api_port,
            log_level=config.log_level.lower(),
        )

    logger.info("Starting API server on %s:%s", config.api_host, config.api_port)
    thread = threading.Thread(target=_serve, daemon=True, name="mikrotrack-api")
    thread.start()
    return thread

def _register_signal_handlers(logger: logging.Logger) -> list[bool]:
    should_stop = [False]

    def _signal_handler(signum: int, _: FrameType | None) -> None:
        signal_name = signal.Signals(signum).name
        logger.info("Received %s, stopping scheduler gracefully", signal_name)
        should_stop[0] = True

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    return should_stop


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
            "ssl_verify=%s, log_level=%s, print_result_to_stdout=%s, "
            "run_mode=%s, collection_interval=%ss, persistence_enabled=%s, "
            "persistence_path=%s, persistence_retention_days=%s, api_enabled=%s, api_host=%s, api_port=%s, backend_api_url=%s"
        ),
        config.mikrotik_host,
        config.mikrotik_port,
        config.mikrotik_username,
        config.mikrotik_use_ssl,
        config.mikrotik_ssl_verify,
        config.log_level,
        config.print_result_to_stdout,
        config.run_mode,
        config.collection_interval,
        config.persistence_enabled,
        config.persistence_path,
        config.persistence_retention_days,
        config.api_enabled,
        config.api_host,
        config.api_port,
        config.backend_api_url,
    )

    if config.persistence_enabled:
        configure_persistence(
            config.persistence_path,
            config.persistence_retention_days,
        )
        validate_persistence()

    if config.api_enabled:
        _run_api_server(config, logger)

    if config.run_mode == "once":
        logger.info("Starting in ONCE mode")
        try:
            result = _run_once(config, logger)
            if config.persistence_enabled:
                save_snapshot(result)

            if config.print_result_to_stdout:
                logger.info("Result printed to stdout (optional)")
                logger.debug("Output size: %d devices", len(result))
                logger.debug("Sample device: %s", result[0] if result else {})
                print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            else:
                logger.info("PRINT_RESULT_TO_STDOUT is disabled, skipping JSON output")
            logger.info("MikroTrack application finished successfully")
            return
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

    logger.info("Starting in LOOP mode (interval=%ss)", config.collection_interval)
    should_stop = _register_signal_handlers(logger)
    while not should_stop[0]:
        try:
            result = _run_once(config, logger)
            if config.persistence_enabled:
                save_snapshot(result)

            if config.print_result_to_stdout:
                logger.info("Result printed to stdout (optional)")
                logger.debug("Output size: %d devices", len(result))
                logger.debug("Sample device: %s", result[0] if result else {})
                print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            else:
                logger.info("PRINT_RESULT_TO_STDOUT is disabled, skipping JSON output")
            sleep_for = config.collection_interval
        except Exception as error:
            wrapped_error = to_mikrotrack_error(error)
            logger.error(
                "Collection failed: [%s] %s",
                wrapped_error.error_code,
                wrapped_error.message,
            )
            logger.error("Recommendation: %s", wrapped_error.recommendation)
            _debug_log_exception(logger, wrapped_error)
            sleep_for = RETRY_BACKOFF_SECONDS

        if should_stop[0]:
            break

        logger.info("Sleeping for %d seconds", sleep_for)
        for _ in range(sleep_for):
            if should_stop[0]:
                break
            time.sleep(1)

    logger.info("MikroTrack scheduler stopped gracefully")


if __name__ == "__main__":
    main()

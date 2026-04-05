from __future__ import annotations

import json
import logging
import sys

from app.collector import collect_dhcp_leases
from app.config import load_config
from app.logging_config import setup_logging
from app.mikrotik_client import MikroTikClient


def main() -> None:
    try:
        config = load_config()
    except Exception as error:
        setup_logging("INFO")
        logging.getLogger("mikrotrack").error("Configuration error: %s", error)
        sys.exit(1)

    setup_logging(config.log_level)
    logger = logging.getLogger("mikrotrack")

    try:
        with MikroTikClient(
            host=config.mikrotik_host,
            port=config.mikrotik_port,
            username=config.mikrotik_username,
            password=config.mikrotik_password,
        ) as client:
            leases = collect_dhcp_leases(client)
            logger.info("Collected %d DHCP lease records", len(leases))
            print(json.dumps(leases, ensure_ascii=False, indent=2))
    except Exception as error:
        logger.error("MikroTrack execution failed: %s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()

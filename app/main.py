import logging


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("mikrotrack")

    logger.info("MikroTrack started")
    logger.info("MikroTrack stopped")


if __name__ == "__main__":
    main()

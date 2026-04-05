from dataclasses import dataclass
import os


@dataclass(slots=True)
class Config:
    mikrotik_host: str
    mikrotik_port: int
    mikrotik_username: str
    mikrotik_password: str
    mikrotik_use_ssl: bool
    mikrotik_ssl_verify: bool
    log_level: str = "INFO"
    print_result_to_stdout: bool = True
    run_mode: str = "once"
    collection_interval: int = 60
    persistence_enabled: bool = True
    persistence_path: str = "/data/snapshots"
    persistence_retention_days: int = 7


def str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_run_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in {"once", "loop"}:
        raise ValueError("RUN_MODE must be either 'once' or 'loop'")
    return normalized


def _parse_positive_int(value: str, *, variable_name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{variable_name} must be an integer") from error

    if parsed <= 0:
        raise ValueError(f"{variable_name} must be greater than zero")

    return parsed


def _parse_non_negative_int(value: str, *, variable_name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{variable_name} must be an integer") from error

    if parsed < 0:
        raise ValueError(f"{variable_name} must be zero or greater")

    return parsed


def load_config() -> Config:
    host = os.getenv("MIKROTIK_HOST", "").strip()
    username = os.getenv("MIKROTIK_USERNAME", "").strip()
    password = os.getenv("MIKROTIK_PASSWORD", "").strip()

    if not host:
        raise ValueError("MIKROTIK_HOST is required")
    if not username:
        raise ValueError("MIKROTIK_USERNAME is required")
    if not password:
        raise ValueError("MIKROTIK_PASSWORD is required")

    return Config(
        mikrotik_host=host,
        mikrotik_port=int(os.getenv("MIKROTIK_PORT", "8729")),
        mikrotik_username=username,
        mikrotik_password=password,
        mikrotik_use_ssl=str_to_bool(os.getenv("MIKROTIK_USE_SSL", "true")),
        mikrotik_ssl_verify=str_to_bool(os.getenv("MIKROTIK_SSL_VERIFY", "false")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        print_result_to_stdout=str_to_bool(
            os.getenv("PRINT_RESULT_TO_STDOUT", "true")
        ),
        run_mode=_parse_run_mode(os.getenv("RUN_MODE", "once")),
        collection_interval=_parse_positive_int(
            os.getenv("COLLECTION_INTERVAL", "60"),
            variable_name="COLLECTION_INTERVAL",
        ),
        persistence_enabled=str_to_bool(os.getenv("PERSISTENCE_ENABLED", "true")),
        persistence_path=os.getenv("PERSISTENCE_PATH", "/data/snapshots").strip()
        or "/data/snapshots",
        persistence_retention_days=_parse_non_negative_int(
            os.getenv("PERSISTENCE_RETENTION_DAYS", "7"),
            variable_name="PERSISTENCE_RETENTION_DAYS",
        ),
    )

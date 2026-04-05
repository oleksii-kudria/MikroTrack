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


def _parse_bool(value: str, *, variable_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{variable_name} must be a boolean value")



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
        mikrotik_use_ssl=_parse_bool(
            os.getenv("MIKROTIK_USE_SSL", "true"),
            variable_name="MIKROTIK_USE_SSL",
        ),
        mikrotik_ssl_verify=_parse_bool(
            os.getenv("MIKROTIK_SSL_VERIFY", "false"),
            variable_name="MIKROTIK_SSL_VERIFY",
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

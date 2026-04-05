from dataclasses import dataclass
import os


@dataclass(slots=True)
class Config:
    mikrotik_host: str
    mikrotik_port: int
    mikrotik_username: str
    mikrotik_password: str
    log_level: str = "INFO"



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
        mikrotik_port=int(os.getenv("MIKROTIK_PORT", "8728")),
        mikrotik_username=username,
        mikrotik_password=password,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

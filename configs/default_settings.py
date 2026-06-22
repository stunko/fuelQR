from dataclasses import asdict

from configs.fuels import *

SIMPLE_SETTINGS = {"OVERRIDE_BY_ENV": True}


@dataclass
class RegistrationStates:
    closed: str = "not_open"


@dataclass
class ErrCode:
    Unauthorized: int = 401


@dataclass
class UILabels:
    start_mini_app: str = "Открыть miniapp"
    create_session: str = "Поделиться"


@dataclass
class QrSessions:
    """QR session storage"""
    number: str
    fuel_types: list[type(BaseFuel)]
    phone_number: str
    email: str

    def json(self) -> dict:
        """"""
        return asdict(self)


# relative path to logs dir,
LOG_PATH = "logs"
# log size formats
# B — bytes
# K / KB / Kb
# M / MB / Mb
LOG_SIZE = "1M"
LOG_LEVEL = "DEBUG"
STREAM_HANDLER = True

POLL_TIMEOUT = 1
POLL_INTERVAL = 1

USE_SMTP = False
SMTP_SERVER = None
SMTP_PORT = 465
SMTP_LOGIN = None
SMTP_PASSWORD = None
SMTP_TIMEOUT = 30

DEFAULT_ENDPOINT = "https://fuel.sevtech.org"
DEFAULT_MESSENGER_ENDPOINT = "https://web.max.ru/14835064"
auth_payload = None

# UI
CHANNEL = "chrome"
HEADLESS = True
USER_DATA = ".user_data"
PAGE_RESOLUTION = {"width": 1280, "height": 800}

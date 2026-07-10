from dataclasses import asdict

from configs.fuels import *

SIMPLE_SETTINGS = {"OVERRIDE_BY_ENV": True}


@dataclass
class RegistrationStates:
    closed: str = "not_open"
    open: str = "open"


@dataclass
class ErrCodes:

    @property
    def items(self) -> list:
        return asdict(self).values()


@dataclass
class ErrCodesSessionReload(ErrCodes):
    BadRequest: int = 400
    Unauthorized: int = 401
    Forbidden: int = 403
    TooManyRequests: int = 429


@dataclass
class ErrCodesRequestRetry(ErrCodes):
    InternalServerError: int = 500
    BadGateway: int = 502
    ServiceUnavailable: int = 503
    GatewayTimeout: int = 504


@dataclass
class UILabels:
    start_mini_app: str = "Открыть miniapp"
    create_session: str = "Поделиться"


@dataclass
class QrSessions:
    """QR session storage"""
    number: str
    fuel_types: list[type(BaseFuel)]
    email: str

    def json(self) -> dict:
        """"""
        return asdict(self)


SESSION_TTL = 1800

# relative path to logs dir,
LOG_PATH = "logs"
# log size formats
# B — bytes
# K / KB / Kb
# M / MB / Mb
LOG_SIZE = "1M"
LOG_LEVEL = "DEBUG"
STREAM_HANDLER = True
# utilize the fuel from the maximum remaining volume
GET_FUEL_WITH_MAXIMUM_BALANCES = False

# how long bot polling fuel qr code
POLL_LIMIT = 1
POLL_INTERVAL = 1
# how many times bot polling qr code
POLL_COUNT = None

USE_SMTP = True
SMTP_SERVER = None
SMTP_PORT = 465
SMTP_LOGIN = None
SMTP_PASSWORD = None
SMTP_TIMEOUT = 30

# UI
CHANNEL = "chrome"
HEADLESS = True
USER_DATA = ".user_data"
PAGE_RESOLUTION = {"width": 1280, "height": 800}

# QR code
QR_BOX_SIZE = 10
QR_BORDER = 2
QR_FILL_COLOR = "#000000"
QR_BACK_COLOR = "#ffffff"
QR_IMAGE_SIZE = (260, 260)
QR_IMAGE_FORMAT = "PNG"
QR_OUTPUT = ".qr_codes"

# DataBase
DB_PATH = ".tinydb"
DB_NAME = "users.json"

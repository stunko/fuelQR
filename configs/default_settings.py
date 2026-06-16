from configs.fuels import Diesel, DieselUltra, A92, A95, A95Ultra

SIMPLE_SETTINGS = {"OVERRIDE_BY_ENV": True}

USERS = []

# relative path to logs dir,
LOG_PATH = "logs"
# log size formats
# B — bytes
# K / KB / Kb
# M / MB / Mb
LOG_SIZE = "1M"
LOG_LEVEL = "DEBUG"
STREAM_HANDLER = False

POLL_TIMEOUT = 1
POLL_INTERVAL = 1

SMTP_SERVER = None
SMTP_PORT = 465
SMTP_LOGIN = None
SMTP_PASSWORD = None
SMTP_TIMEOUT = 30

DEFAULT_ENDPOINT = "https://fuel.sevtech.org"

INIT_DATA = None
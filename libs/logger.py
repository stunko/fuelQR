import pathlib
from logging import Formatter, getLogger, Logger, StreamHandler
from logging.handlers import RotatingFileHandler

from humanfriendly import parse_size

from configs import config


def get_log(name: str) -> Logger:
    log = getLogger(name)
    if not log.handlers:
        log.propagate = False
        formatter = Formatter(
            "%(asctime)s [%(levelname)-8s] [%(name)-25s] %(message)s",
            datefmt="%Y-%d-%m %H:%M:%S",
        )

        log.setLevel(config.LOG_LEVEL.upper())
        log_path = pathlib.Path(config.LOG_PATH).joinpath("qr.log")

        # set file handler
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=parse_size(
                config.LOG_SIZE,
                binary=True
            ),
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)
        # set stream handler
        if config.STREAM_HANDLER:
            handler = StreamHandler()
            handler.setFormatter(formatter)
            log.addHandler(handler)
    return log

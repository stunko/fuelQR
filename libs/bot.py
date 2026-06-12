import json
import pathlib
from multiprocessing import current_process
from typing import Any

import requests

from configs import config
from libs.helpers import try_until
from libs.logger import get_log
from libs.smtp import SMTPClient

LOG = get_log(__name__).getChild(current_process().name)


class QrGetter:
    """"""

    def __init__(
            self,
            number: str,
            phone_number: str,
            fuel: str,
            email: str = None,
    ) -> None:
        """"""
        self.email = email
        self._number = number
        self._phone_number = phone_number
        self._fuel = fuel
        self._session = requests.Session()

    def __do_call(
            self,
            method: str,
            url: str = None,
            *args,
            **kwargs
    ) -> requests.Response:
        """"""
        url = url or config.BOT_ENDPOINT
        LOG.debug(
            f"call `{method}` for `{url}` with params {args}, {kwargs}...")
        method = getattr(self._session, method)
        response = method(url, *args, **kwargs)
        response.raise_for_status()
        try:
            LOG.debug(f"response status code -  `[{response.status_code}]`...")
            raw = response.json()
        except json.JSONDecodeError:
            raw = response.content
        LOG.debug(f"response raw - `{raw}`")
        return response

    def generate(self) -> Any:
        """"""
        LOG.info(f"Get fuel `QR` for `{self._number.upper()}`...")
        response = self.__do_call(method="get")
        data = response.json().get("data", {})
        if data.get("wait"):
            LOG.info(f"Fuel tanks is empty, try tomorrow...")
            return pathlib.Path(config.LOG_PATH).joinpath("qr.log")


def worker_wrapper(kwargs) -> None:
    """warker wrapper """
    qr_code = None
    worker = QrGetter(**kwargs)
    try:
        # qr code poller
        qr_code = try_until(
            worker.generate,
            interval=config.POLL_INTERVAL,
            timeout=config.POLL_TIMEOUT
        )
    except Exception as e:
        LOG.error(e)
    if not qr_code:
        LOG.warning(f"No `QR code` obtained...")
        return
    SMTPClient().send(
        address=worker.email,
        file_path=qr_code,
    )

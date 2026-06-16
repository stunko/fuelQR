import json
import pathlib
from typing import Any

import requests

from configs import config
from configs.fuels import BaseFuel
from libs.helpers import try_until
from libs.logger import get_log
from libs.smtp import SMTPClient

LOG = get_log(__name__)


class QrGetter:
    """"""

    def __init__(
            self,
            number: str,
            phone_number: str,
            fuel_types: list | BaseFuel,
            email: str = None,
    ) -> None:
        """"""
        self.email = email
        self._number = number.upper()
        self._phone_number = phone_number
        self._fuel_types = [fuel_types] if not isinstance(fuel_types,
                                                          list) else fuel_types
        self._session = requests.Session()
        self._init_fake_session()
        self._fuel = None

    @property
    def _default_headers(self) -> dict:
        """"""
        return {
            "authority": config.DEFAULT_ENDPOINT,
            "accept": "*/*",
            "content-type": "application/json",
            "referer": f"{config.DEFAULT_ENDPOINT}/clientapp?mode=max-mini-app"
        }

    def __do_call(
            self,
            uri: str,
            method: str,
            headers: dict = None,
            *args,
            **kwargs
    ) -> requests.Response:
        """"""
        url = f"{config.DEFAULT_ENDPOINT}/{uri}"
        headers = {**self._default_headers, **headers} \
            if headers else self._default_headers
        self._session.headers = headers

        LOG.debug(
            f"call `{method}` for `{uri}` with params {args}, {kwargs}...")
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

    def _init_fake_session(self) -> bool:
        """"""
        uri = "fuel/qr/session/max"
        payload = config.INIT_DATA
        response = self.__do_call(uri=uri, method="post", json=payload)
        return response.ok

    def _get_fuel_type(self) -> dict:
        """"""
        uri = "fuel/qr/fuel-types"
        response = self.__do_call(method="get", uri=uri)
        return response.json().get("data")

    def _get_available_fuel(self) -> list:
        """"""
        uri = "map/a"
        response = self.__do_call(method="get", uri=uri)
        return response.json().get("gas_stations", [])

    def _plate_check(self, confirmation: bool = True) -> bool:
        """"""
        uri = "fuel/qr/plate/check"
        payload = {
            "car_plate": self._number,
            "plate_format_confirmed": confirmation
        }
        response = self.__do_call(uri=uri, method="post", json=payload)
        return response.ok

    @property
    def fuel(self) -> BaseFuel:
        if self._fuel is None:
            LOG.info(f"Get preferred fuel from {self._fuel_types}...")
            available_fuels = self._get_available_fuel()
            fuel_types = (f(available_fuels) for f in self._fuel_types)
            self._fuel = max(fuel_types, key=lambda f: f.percent)
            LOG.debug(f"Set preferred fuel type `{self._fuel}`")
        return self._fuel

    def generate_qr(self) -> Any:
        """"""
        LOG.info(f"Get fuel `QR` for `{self._number.upper()}`...")
        self._plate_check()
        fuel_type = self._get_fuel_type()
        fuel = self.fuel
        if fuel_type.get("wait"):
            LOG.info(f"Fuel tanks is empty, try tomorrow...")
        return False


def worker_wrapper(kwargs) -> None:
    """warker wrapper """
    qr_code = None
    worker = QrGetter(**kwargs)
    try:
        # qr code poller
        qr_code = try_until(
            worker.generate_qr,
            interval=config.POLL_INTERVAL,
            timeout=config.POLL_TIMEOUT
        )
    except Exception as e:
        LOG.error(e)
    if not qr_code:
        LOG.warning(f"No `QR code` obtained...")
        # return
    SMTPClient().send(
        address=worker.email,
        file_path=pathlib.Path(config.LOG_PATH).joinpath("qr.log"),
    )

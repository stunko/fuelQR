import json
import pathlib
from typing import Any

import requests

from configs import config
from configs.fuels import BaseFuel
from libs.helpers import try_until
from libs.logger import get_log
from libs.smtp import SMTPClient
from libs.ui import FakeWebMessenger

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
        self._fuel = None
        self.__session = None

    @property
    def _session(self) -> requests.Session:
        """"""
        if self.__session is None:
            self.__session = requests.Session()
            self.__session.verify = False
            # get session payload
            with FakeWebMessenger() as messenger:
                payload = messenger.init_fake_session()
            self._init_fake_session(payload)
        return self.__session

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

    def _init_fake_session(self, payload: dict) -> bool:
        """"""
        uri = "fuel/qr/session/max"
        response = self.__do_call(
            uri=uri,
            method="post",
            json=payload
        )
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
        try:
            self._plate_check()
            fuel_type = self._get_fuel_type()
            LOG.info(f"Persistent fuel is `{self.fuel}`...")
            if fuel_type.get(
                    "registration_state") == config.RegistrationStates.closed:
                LOG.info(f"Fuel tanks is empty, try later...")
        except requests.HTTPError as e:
            LOG.error(e)
            if e.response.status_code == config.ErrCode.Unauthorized:
                self.close()
        return False

    def close(self) -> None:
        """"""
        if self.__session:
            LOG.info(f"Close session `{self.__session}`...")
            self.__session.close()
        self.__session = None


def worker_wrapper(payloads) -> None:
    """worker wrapper """
    worker = QrGetter(**payloads)
    try:
        # qr code poller
        try_until(
            worker.generate_qr,
            interval=config.POLL_INTERVAL,
            timeout=config.POLL_TIMEOUT,
            times=1,
            error_msg="No `QR code` obtained..."
        )
    except Exception as e:
        LOG.error(e)
    if config.USE_SMTP:
        SMTPClient().send(
            address=worker.email,
            file_path=pathlib.Path(config.LOG_PATH).joinpath("qr.log"),
        )

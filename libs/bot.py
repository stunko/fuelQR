import json
import pathlib
import time
from datetime import datetime
from typing import Any

import qrcode
import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from configs import config
from configs.fuels import BaseFuel
from libs.helpers import try_until
from libs.logger import get_log
from libs.smtp import SMTPClient
from libs.ui import FakeWebMessenger

LOG = get_log(__name__)


class FuelQrCodeManager:
    """"""

    def __init__(
            self,
            number: str,
            fuel_types: list | BaseFuel,
            email: str = None,
    ) -> None:
        """"""
        self.email = email
        self._number = number
        if not isinstance(fuel_types, (list, tuple)):
            fuel_types = [fuel_types]
        self._fuel_types = fuel_types
        self.__fuel = None
        self.__session = None
        self.__ttl_start = None

    @property
    def _session(self) -> requests.Session:
        """"""
        if self.__session is None:
            self.__session = requests.Session()
            self.__session.verify = False
            # setup request retries
            retries = Retry(
                # Retry attempts
                total=5,
                # Pause between attempts (1 sec, 2 sec, 4 sec...)
                backoff_factor=1,
                # Retries only server errors
                status_forcelist=config.ErrCodesRequestRetry().items,
                raise_on_status=False
            )
            adapter = HTTPAdapter(max_retries=retries)
            self.__session.mount("http://", adapter)
            self.__session.mount("https://", adapter)
            # get fake session payload
            with FakeWebMessenger() as messenger:
                payload = messenger.init_fake_session()
            self._init_fake_session(payload)
            self.__ttl_start = time.monotonic()
        return self.__session

    @property
    def _default_headers(self) -> dict:
        """"""
        return {
            "Authority": config.DEFAULT_ENDPOINT,
            "Accept": "*/*",
            "Content-type": "application/json",
            "Referer": f"{config.DEFAULT_ENDPOINT}/clientapp?mode=max-mini-app",
            "X-Fuel-Client-App": "clientapp",
            "X-Fuel-Client-Mode": "max-mini-app",
            "X-Fuel-Client-Ua-Mobile": "0",
            "Origin": config.DEFAULT_ENDPOINT
        }

    def _do_call(
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
            f"call `{method}` for `{url}` with params {args}, {kwargs} headers {self._session.headers}...")
        method = getattr(self._session, method)

        response = method(url, *args, **kwargs)
        try:
            LOG.debug(f"response status code -  `[{response.status_code}]`...")
            raw = response.json()
        except json.JSONDecodeError:
            raw = response.content
        LOG.debug(f"response raw - `{raw}`")
        response.raise_for_status()
        return response

    def _init_fake_session(self, payload: dict) -> bool:
        """"""
        uri = "fuel/qr/session/max"
        response = self._do_call(
            uri=uri,
            method="post",
            json=payload
        )
        return response.ok

    def _session_status(self) -> bool:
        """"""
        uri = "fuel/qr/session/status"
        response = self._do_call(
            uri,
            method="get"
        )
        return response.ok

    def _plate_check(self, confirmation: bool = False) -> bool:
        """"""
        uri = "fuel/qr/plate/check"
        payload = {
            "car_plate": self._number,
            "plate_format_confirmed": confirmation
        }
        response = self._do_call(uri=uri, method="post", json=payload)
        return response.ok

    def _check_ttl(self) -> None:
        """"""
        LOG.debug(f"check session ttl state...")
        if time.monotonic() - self.__ttl_start >= config.SESSION_TTL:
            response = requests.Response()
            response.status_code = config.ErrCodesSessionReload.Unauthorized
            raise requests.HTTPError(
                f"session exceeded ttl `{config.SESSION_TTL}`...",
                response=response)

    def _create_fuel_qr(self,
                        plate_format_confirmed: bool = False) -> str | None:
        """"""
        uri = "fuel/qr/create"
        payload = {
            "car_plate": self._number,
            "fuel_type_id": self.__fuel.id,
            "plate_format_confirmed": plate_format_confirmed
        }
        response = self._do_call(
            uri=uri,
            method="post",
            json=payload
        )
        data = response.json().get("data", {})
        if data:
            return data["ticket"]["deeplink"]

    def _get_fuel_types(self) -> bool | None:
        """"""
        uri = "fuel/qr/fuel-types"
        if not self.__fuel:
            response = self._do_call(method="get", uri=uri)
            data = response.json().get("data", {})
            if data.get("registration_state",
                        "") != config.RegistrationStates.open:
                return
            self.__fuel = self._get_preferred_fuel()
        return True

    def _get_available_fuel(self) -> list:
        """"""
        uri = "map/a"
        response = self._do_call(method="get", uri=uri)
        return response.json().get("gas_stations", [])

    def _get_preferred_fuel(self) -> BaseFuel:
        if config.GET_FUEL_WITH_MAXIMUM_BALANCES:
            available_fuels = self._get_available_fuel()
            LOG.info(f"Get preferred fuel from {self._fuel_types}...")
            fuel_types = (f(available_fuels) for f in self._fuel_types)
            fuel = max(fuel_types, key=lambda f: f.percent)
        else:
            fuel = self._fuel_types[0]()
        LOG.debug(f"Set preferred fuel type `{fuel}`")
        return fuel

    def get_fuel_qr(self) -> Any:
        """"""
        LOG.info(f"create `fuel Qr code` for `{self._number}`...")
        try:
            if self.__ttl_start is None:
                self._session_status()
                self._plate_check()
            if self._get_fuel_types():
                LOG.info(
                    f"Persistent and preferred fuel is `{self.__fuel.title}`...")
                if link := self._create_fuel_qr():
                    LOG.debug(f"qr code created {link}...")
                    return self._generate_qr(link)
            # reload session triggering if ttl exceeded
            self._check_ttl()
        except requests.HTTPError as e:
            LOG.error(e)
            if e.response.status_code in config.ErrCodesSessionReload().items:
                self.close()
        return False

    def _generate_qr(self, link: str) -> str:
        """"""
        qr = qrcode.QRCode(
            version=1,
            # errorCorrectionLevel: 'M'
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=config.QR_BOX_SIZE,
            # margin: 2
            border=config.QR_BORDER,
        )

        qr.add_data(link)
        qr.make(fit=True)
        qr_img = qr.make_image(
            fill_color=config.QR_FILL_COLOR,
            back_color=config.QR_BACK_COLOR
        ).convert("RGB")
        qr_img = qr_img.resize(config.QR_IMAGE_SIZE, Image.Resampling.LANCZOS)

        output_dir = pathlib.Path(__file__).resolve().parents[
                         1] / config.QR_OUTPUT
        output_dir.mkdir(exist_ok=True, parents=True)

        file_name = f"{self.__fuel.title}_{datetime.now().strftime('%d%m%y')}.{config.QR_IMAGE_FORMAT.lower()}"
        output = output_dir / file_name
        LOG.info(f"save obtained fue qr to `{output}`...")
        qr_img.save(output, format=config.QR_IMAGE_FORMAT)
        return output.as_posix()

    def close(self) -> None:
        """"""
        if self.__session:
            LOG.info(f"Close session `{self.__session}`...")
            self.__session.close()
            self.__session = None
        self.__fuel = None
        self.__ttl_start = None


def worker_wrapper(person: dict) -> None:
    """worker wrapper """
    worker = FuelQrCodeManager(**person)
    qr_code = None
    try:
        # qr code poller
        qr_code = try_until(
            worker.get_fuel_qr,
            interval=config.POLL_INTERVAL,
            timeout=config.POLL_LIMIT,
            times=config.POLL_COUNT,
            error_msg="No `QR code` obtained..."
        )
    except Exception as e:
        LOG.error(e)
    if config.USE_SMTP and qr_code:
        SMTPClient().send(
            address=worker.email,
            file_path=qr_code,
        )

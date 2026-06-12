import datetime
import mimetypes
import pathlib
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from configs import config
from libs.logger import get_log

LOG = get_log(__name__)


class SMTPClient:

    def __init__(
        self,
        server: str = None,
        login: str = None,
        password: int | str = None,
        port: int = None,
        timeout: int = 30
    ) -> None:
        """"""
        self._server = server or config.SMTP_SERVER
        self._port = port or config.SMTP_PORT
        self._login = login or config.SMTP_LOGIN
        self._password = password or config.SMTP_PASSWORD
        self._timeout = timeout or config.SMTP_TIMEOUT

    def _prepare_msg(
            self,
            address: str,
            subject: str = None,
            body_text: str = None,
            file_path: str | pathlib.Path = None
    ) -> MIMEMultipart:
        """"""
        msg = MIMEMultipart()
        msg["From"] = self._login
        msg["To"] = address
        msg["Subject"] = (
                subject or
                f"Fuel `QR code` - `{datetime.datetime.now().strftime('%d %B %Y')}`")

        if body_text:
            LOG.debug(f"prepare msg, add body `{body_text}`...")
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
        if file_path:
            if not isinstance(file_path, pathlib.Path):
                file_path = pathlib.Path(file_path)
            if file_path.exists():
                LOG.debug(f"prepare msg, attachment `{file_path}`...")
                ctype, encoding = mimetypes.guess_type(file_path)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"

                with file_path.open("rb") as fd:
                    attachment = MIMEBase(*ctype.split("/", 1))
                    attachment.set_payload(fd.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename={file_path.name}"
                )
                msg.attach(attachment)
        return msg

    def send(
            self,
            address: str,
            subject: str = None,
            body_text: str = None,
            file_path: str | pathlib.Path = None
    ) -> None:
        """Send message"""
        try:
            LOG.debug(f"init smtp client `{self._server}:{self._port}`")
            with smtplib.SMTP_SSL(host=self._server, port=self._port, timeout=self._timeout) as smtp:
                LOG.debug(f"login to smtp as `{self._login}:{self._password}`")
                smtp.login(self._login, self._password)
                msg = self._prepare_msg(address, subject, body_text, file_path)
                LOG.debug(f"send email to `{address}`...")
                smtp.sendmail(
                    from_addr=self._login,
                    to_addrs=address,
                    msg=msg.as_string()
                )
        except Exception as e:
            LOG.error(f"can't send email to `{address}` - {e}")

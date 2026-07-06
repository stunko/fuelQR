import pathlib

from playwright.sync_api import sync_playwright, Page, Locator, expect

from configs import config
from libs.logger import get_log

ROOT = pathlib.Path(__file__).parents[1]
LOG = get_log(__name__)


class FakeWebMessenger:
    """Implements user session initialization from messenger web ui"""

    def __init__(
            self,
            base_url: str = None,
    ) -> None:
        """"""
        self._url = base_url or config.DEFAULT_MESSENGER_ENDPOINT
        self.__pw = None
        self.__context = None

    def __enter__(self) -> "FakeWebMessenger":
        """"""
        self.__init_pw()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """"""
        self.__close()

    def __init_pw(self) -> None:
        if self.__pw is None:
            LOG.debug("Start playwright session...")
            self.__pw = sync_playwright().start()

    @property
    def _context(self):
        """"""
        if self.__context is None:
            LOG.debug("Initialize persistent context...")
            self.__context = self.__pw.chromium.launch_persistent_context(
                user_data_dir=ROOT.joinpath(config.USER_DATA),
                headless=config.HEADLESS,
                channel=config.CHANNEL,
                viewport=config.PAGE_RESOLUTION,
            )
        return self.__context

    @property
    def _page(self) -> Page:
        if not self._context.pages:
            LOG.debug("Create new page...")
            self._context.new_page()
        return self._context.pages[0]

    def _get_button(self, name: str, timeout=10) -> Locator:
        """"""
        button = self._page.get_by_role("button", name=name, exact=False)
        expect(button).to_be_visible(
            timeout=timeout * 1000
        )
        return button

    def __close(self) -> None:
        """"""
        try:

            if self.__context:
                LOG.debug("Close persistent context...")
                self.__context.close()
        except Exception as e:
            LOG.error(e)
        finally:
            if self.__pw:
                LOG.debug("Stop playwright session...")
                self.__pw.stop()

    def init_fake_session(self, endpoint: str = None) -> dict:
        endpoint = endpoint or "fuel/qr/session/max"
        try:
            LOG.debug(f"Go to page `{self._url}`...")
            self._page.goto(self._url)
            LOG.debug(f"Open messenger mini-app...")
            mini_app = self._get_button(
                name=config.UILabels.start_mini_app)
            mini_app.click()
            LOG.debug(f"Create mini-app auth session...")
            session = self._get_button(
                name=config.UILabels.create_session)
            with (self._page.expect_response(
                    lambda r: endpoint in r.url) as response_info):
                session.click()
                response = response_info.value
                request = response.request
                return request.post_data_json
        except Exception as e:
            LOG.error(
                f"An error occurred, can't initialize mini-app session: {e}...")
            raise

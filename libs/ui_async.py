import pathlib

from playwright.async_api import async_playwright, Page, Locator, expect

from configs import config
from libs.logger import get_log

ROOT = pathlib.Path(__file__).parents[1]
LOG = get_log(__name__)


class FakeWebMessengerAsync:
    """Implements user session initialization from messenger web ui"""

    def __init__(
            self,
            base_url: str = None,
    ) -> None:
        """"""
        self._url = base_url or config.DEFAULT_MESSENGER_ENDPOINT
        self.__pw = None
        self.__context = None

    async def __aenter__(self) -> "FakeWebMessengerAsync":
        """"""
        await self.__init_pw()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """"""
        await self.__close()

    async def __init_pw(self) -> None:
        if self.__pw is None:
            LOG.debug("Start playwright session...")
            self.__pw = await async_playwright().start()

    async def __get_context(self):
        """"""
        if self.__context is None:
            LOG.debug("Initialize persistent context...")
            self.__context = await self.__pw.chromium.launch_persistent_context(
                user_data_dir=ROOT.joinpath(config.USER_DATA),
                headless=config.HEADLESS,
                channel=config.CHANNEL,
                viewport=config.PAGE_RESOLUTION,
            )
        return self.__context

    async def __get_page(self) -> Page:
        context = await self.__get_context()
        if not context.pages:
            LOG.debug("Create new page...")
            await context.new_page()
        return context.pages[0]

    async def __get_button(self, name: str, timeout=10) -> Locator:
        """"""
        page = await self.__get_page()
        button = page.get_by_role("button", name=name, exact=False)
        await expect(button).to_be_visible(
            timeout=timeout * 1000
        )
        return button

    async def __close(self) -> None:
        """"""
        try:

            if self.__context:
                if self.__context.browser and self.__context.browser.is_connected:
                    LOG.debug("Close persistent context...")
                    await self.__context.close()
        except Exception as e:
            LOG.error(e)
            raise
        finally:
            LOG.debug("Stop playwright session...")
            await self.__pw.stop()

    async def init_fake_session(self, endpoint: str = None) -> dict:
        endpoint = endpoint or "fuel/qr/session/max"
        page = await self.__get_page()
        try:
            LOG.debug(f"Go to page `{self._url}`...")
            await page.goto(self._url)
            LOG.debug(f"Open messenger mini-app...")
            mini_app = await self.__get_button(
                name=config.UILabels.start_mini_app)
            await mini_app.click()
            LOG.debug(f"Create mini-app auth session...")
            session = await self.__get_button(
                name=config.UILabels.create_session)
            async with page.expect_request(lambda r: endpoint in r.url) as request_info:
                await session.click()
                request = await request_info.value
                return request.post_data_json
        except Exception as e:
            LOG.error(
                f"An error occurred, can't initialize mini-app session: {e}...")
            raise

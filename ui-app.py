import time

from libs.logger import get_log
from libs.ui import FakeWebMessenger

LOG = get_log(__name__)


def main() -> None:
    """"""
    LOG.debug("Initialize `max` messenger...")
    with FakeWebMessenger() as messenger:
        session = messenger.init_fake_session()
        LOG.info(f"Obtained session payloads {session}...")
        time.sleep(10)


if __name__ == "__main__":
    main()

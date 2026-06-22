from configs import config
from libs.bot import worker_wrapper
from libs.logger import get_log


LOG = get_log(__name__)


if __name__ == "__main__":
    worker_wrapper(config.QrSession.json())

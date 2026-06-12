from multiprocessing import Pool

from configs import config
from libs.bot import worker_wrapper
from libs.helpers import number2words, plural
from libs.logger import get_log

LOG = get_log(__name__)


def main():
    """app wrapper"""
    payloads = config.USERS
    process_count = len(payloads)
    LOG.info(
        f"Initialize {number2words(process_count)} `QR` code {plural(process_count, 'worker')}...")
    try:
        with Pool(processes=process_count) as pool:
                pool.map(worker_wrapper, payloads)
    except Exception as e:
        LOG.error(e)


if __name__ == "__main__":
    main()

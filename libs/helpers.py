import itertools
import time
from typing import Callable

import inflect

from libs.logger import get_log

ENGINE = inflect.engine()
LOG = get_log(__name__)


def try_until(
        func: Callable,
        try_msg: str = None,
        error_msg: str = None,
        log: Callable = None,
        interval: int = 1,
        timeout: int = 360,
        times: int = None,
        pass_num: bool = False,
):
    """
    repeat call func while it returns False
    raises exc.TimeoutError if timeout expired or call times reached
    """
    log = log or LOG
    begin_msg = (
        f"Trying {func} until: "
        f"(timeout: {timeout} "
        f"interval: {interval} "
        f"times: {times or 'unlimited'})"
    )
    try_msg = try_msg or f"{func} returns false"
    error_msg = error_msg or f"Try {try_msg} Failed!"

    start_time = time.monotonic()
    log.debug(begin_msg)
    for num in itertools.count(0):
        log.debug("%s (%s) ...", try_msg, num)
        try:
            result = func() if not pass_num else func(num)
            if result:
                return result
        except Exception as e:
            msg = f"{error_msg}: got error: {e}"
            e.args = (msg,)
            raise e
        else:
            if time.monotonic() - start_time > timeout:
                msg = f"{error_msg}: timeout {timeout} seconds exceeded"
                raise TimeoutError(msg)
            if times and num >= times - 1:
                msg = f"{error_msg}: call count {times} times exceeded"
                raise TimeoutError(msg)

        log.debug(f"Wait {interval:.2f} seconds before the next attempt")
        time.sleep(interval)


def number2words(num: int | str) -> str:
    """"""
    return ENGINE.number_to_words(num)


def plural(num: int, word: str) -> str:
    """"""
    return ENGINE.plural_noun(word, num)

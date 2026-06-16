from mitmproxy import http

from configs import config
from libs.bot import worker_wrapper
from libs.logger import get_log

LOG = get_log(__name__)


def response(flow: http.HTTPFlow):
    """app wrapper"""
    if "fuel/qr/session/max" in flow.request.pretty_url:
        config.configure(**{"INIT_DATA": flow.request.json()})
        try:
            payloads = config.USERS
            worker_wrapper(payloads)
        except Exception as e:
            LOG.error(e)

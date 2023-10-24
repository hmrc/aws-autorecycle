import itertools
import logging
import time

logger = logging.getLogger(__name__)


def fails_with(fn):
    try:
        fn()
    except Exception as e:
        return e


def poll(fn, max_iters=50, sleep_for_seconds=None):
    for i in itertools.count(start=1):
        error = fails_with(fn)
        if error is None:
            logger.info("Polling Succeeded")
            return
        else:
            logger.info("poll failed {} with: {}".format(i, error))

        if i >= max_iters:
            logger.warning("Giving up polling after {}".format(max_iters))
            raise error

        if sleep_for_seconds:
            time.sleep(sleep_for_seconds)


def run_until(fn, sentinel_value, max_iters=50):
    for i in range(0, max_iters):
        if fn() == sentinel_value:
            return

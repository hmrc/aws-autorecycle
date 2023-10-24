import itertools
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


def fails_with(fn: Any) -> Any:
    try:
        fn()
        return
    except Exception as e:
        return e


def poll(fn: Any, max_iters: int = 50, sleep_for_seconds: Optional[int] = None) -> Any:
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

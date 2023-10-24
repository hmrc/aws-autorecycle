import datetime
import logging
from typing import Any

import pytz
import rfc3339

from src.autorecycle_delayer.common import json_logger_config

logger = logging.getLogger(__name__)


def str_to_time(time_str: str) -> datetime.time:
    try:
        h, m, s = time_str.split(":")
    except ValueError as err:
        raise err
    try:
        return datetime.time(int(h), int(m), int(s))
    except ValueError as err:
        raise err


def lambda_handler(event: Any, context: Any) -> Any:
    json_logger_config(event, context)
    component = event["component"]
    logger.info(f"Checking event for a recycle window for {component}")

    output = {}
    output["wait"] = False

    if "recycle_window" in event:
        london_time = pytz.timezone("Europe/London")
        now_datetime = london_time.localize(datetime.datetime.now())
        time_now = now_datetime.time()

        recycle_window = event["recycle_window"].split(",")
        start = str_to_time(recycle_window[0])
        end = str_to_time(recycle_window[1])
        logger.info(f"Found recycle window for {component}")
        logger.info(f"Recycle window is Start: {start}, End: {end} for {component}")

        if start < end:
            if time_now < start:
                output["wait"] = True
                recycle_time = london_time.localize(datetime.datetime.combine(now_datetime, start))
                output["time_wait"] = rfc3339.rfc3339(recycle_time)
            elif time_now > end:
                output["wait"] = True
                recycle_time = london_time.localize(datetime.datetime.combine(now_datetime, start))
                recycle_time += datetime.timedelta(1)
                output["time_wait"] = rfc3339.rfc3339(recycle_time)
            else:
                logger.info(f"The time is within the recycle window for {component}, recycling.")

        elif start > end:
            if start > time_now > end:
                output["wait"] = True
                recycle_time = london_time.localize(datetime.datetime.combine(now_datetime, start))
                output["time_wait"] = rfc3339.rfc3339(recycle_time)
            else:
                logger.info(f"The time is within the recycle window for {component}, recycling.")

    else:
        logger.info(f"No recycle window found for {component}, recycling.")

    if output["wait"]:
        logger.info(
            f"The time is outside the recycle window for {component}, "
            f"the next permitted recycle time is {output['time_wait']}"
        )

    return output

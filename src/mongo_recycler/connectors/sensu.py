import logging
import re

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


def silence_sensu_alerts(component, duration_seconds):
    _silence_sensu_alert_type(component, duration_seconds, check_type="warning")
    _silence_sensu_alert_type(component, duration_seconds, check_type="critical")


def _silence_sensu_alert_type(component, duration_seconds, check_type):
    check_name = re.sub(r"_mongo(_[abc])?$", "", component)
    final_check_name = "infra_check_mongo_replica_set_health_" + check_name + "_" + check_type + "_aggregates"

    payload = {"check": final_check_name, "expire": duration_seconds}

    return _post_to_sensu(payload, final_check_name)


@retry(
    wait=wait_fixed(60),
    stop=stop_after_attempt(8),
    retry=retry_if_exception(ConnectionError),
    reraise=False,
)
def _post_to_sensu(payload, final_check_name):
    headers = {"Content-Type": "application/json"}
    url = "http://sensu:4567/silenced"
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if response:
        if response.status_code == 201:
            logger.info("Sensu check silenced successfully: " + final_check_name)
        else:
            logger.warning("Sensu silencing failed for: " + final_check_name)
        return response

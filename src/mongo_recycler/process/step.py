import logging
from typing import Any

import src.mongo_recycler.models.decision
import src.mongo_recycler.process.decision as decision
import src.mongo_recycler.process.execute as execute
import src.mongo_recycler.process.instances
import src.mongo_recycler.process.pre_step_checks as pre_step_checks
import src.mongo_recycler.process.replica_set_health as replica_set_health
from src.mongo_recycler.connectors.aws import AWS
from src.mongo_recycler.connectors.mongo import Mongo
from src.mongo_recycler.connectors.sensu import silence_sensu_alerts
from src.mongo_recycler.models.decision import Decision
from src.mongo_recycler.utils.logger import json_logger_config

logger = logging.getLogger(__name__)


def step(component: str) -> Decision:
    aws = AWS(component)
    mongo = Mongo(component)
    cluster_health = replica_set_health.ReplicaSetHealth(aws, mongo)

    target_ami = pre_step_checks.get_ami_and_check_all_amis_match(component, aws)

    replica_set_status = list(src.mongo_recycler.process.instances.fetch_replica_set_status(aws, mongo))

    pre_step_checks.assert_all_nodes_in_same_replica_set(replica_set_status)

    logger.info(decision.report_cluster_status(replica_set_status, target_ami))
    outcome = decision.decide_on_action(replica_set_status, target_ami)

    logger.info(decision.report_outcome(outcome))
    execute.execute_action(outcome, aws, mongo, cluster_health)

    return outcome


def increment_counter(event: Any) -> Any:
    if "counter" not in event:
        event["counter"] = 0
    event["counter"] += 1
    return event


def is_first_run(event: Any) -> Any:
    return not event.get("counter")


def lambda_handler(event: Any, context: Any) -> Any:
    json_logger_config(event, context)
    component = event["component"]

    if is_first_run(event):
        silence_sensu_alerts(component, 900)

    step_result = step(component)
    event["decision"] = {"action": step_result.action, "instance": step_result.instance}

    if step_result.action == decision.DONE:
        if "counter" in event:
            event["message_content"]["text"] = (
                "Autorecycling has successfully completed. " f"Recycled {event['counter']} mongo instances."
            )
        else:
            event["message_content"]["text"] = "No instances were recycled, because there was nothing to do"

    increment_counter(event)

    return event

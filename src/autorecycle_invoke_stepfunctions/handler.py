#!/usr/bin/env python
import logging
from typing import Any, Union

from src.autorecycle_invoke_stepfunctions.aws import get_asg, get_autorecycling_tags
from src.autorecycle_invoke_stepfunctions.get_account_details import get_account_id, get_slack_channel
from src.autorecycle_invoke_stepfunctions.get_component_details import assert_recyclable, get_component_name
from src.autorecycle_invoke_stepfunctions.get_environment import get_current_environment
from src.autorecycle_invoke_stepfunctions.logger import json_logger_config
from src.autorecycle_invoke_stepfunctions.sf_start_execution import sf_start_execution

logger = logging.getLogger(__name__)

payload_to_asg_tag_map: dict[str, str] = dict(
    strategy="autorecycle_strategy",
    monitoring_slack_channel="autorecycle_slack_monitoring_channel",
    notify_pager_duty="autorecycle_notify_pager_duty",
    team="autorecycle_team",
    step_function_name="autorecycle_step_function_name",
    dry_run="autorecycle_dry_run",
)


def lambda_handler(event: Any, context: Any) -> None:
    json_logger_config(event, context)

    component: Any = get_component_name(event)
    if component is None:
        logger.info("No action to take as component was not set")
        return

    environment: Union[str, None] = get_current_environment()
    account_id: str = get_account_id()
    slack_channel: str = get_slack_channel()

    asg_name: Any = get_asg(component)["AutoScalingGroupName"]
    asg_tags: dict[Any, Any] = get_autorecycling_tags(asg_name)
    if assert_recyclable(asg_tags, component, environment):
        override_component_name = asg_tags.get("autorecycle_override_component_name", component)
        payload: dict[Any, Any] = construct_payload(
            account_id, slack_channel, override_component_name, asg_name, asg_tags
        )
        sf_start_execution(payload)


def construct_payload(
    account_id: Any, slack_channel: Any, component: Any, autoscaling_group_name: Any, asg_tags: Any
) -> dict[Any, Any]:
    payload: dict[Any, Any] = dict()
    payload["account_id"] = account_id
    payload["success_channel"] = slack_channel
    payload["component"] = component
    payload["auto_scaling_group_name"] = autoscaling_group_name
    payload["emoji"] = ":robot_face:"

    for payload_key, tag_name in payload_to_asg_tag_map.items():
        if tag_name in asg_tags:
            payload[payload_key] = asg_tags[tag_name]

    return payload

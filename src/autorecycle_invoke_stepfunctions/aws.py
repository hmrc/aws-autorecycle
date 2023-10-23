import logging
from typing import Any, List, Union

import boto3
import botocore.exceptions

logger = logging.getLogger(__name__)

sf_client = None
sf_exceptions = botocore.exceptions

autorecycle_tag_names = dict(
    autorecycle_override_component_name="string",
    autorecycle_recycle_on_asg_update="boolean",
    autorecycle_strategy="string",
    autorecycle_slack_monitoring_channel="string",
    autorecycle_notify_pager_duty="boolean",
    autorecycle_team="string",
    autorecycle_step_function_name="string",
    autorecycle_dry_run="boolean",
)


def get_stepfunctions_client() -> Any:
    global sf_client
    if sf_client is None:
        sf_client = boto3.client("stepfunctions", "eu-west-2")
    return sf_client


def get_asg(component: Any) -> Any:
    client: Any = boto3.client("autoscaling", "eu-west-2")
    paginator: Any = client.get_paginator("describe_auto_scaling_groups")
    page_iterator: Any = paginator.paginate(PaginationConfig={"PageSize": 100})

    filtered_asgs: Any = page_iterator.search(
        "AutoScalingGroups[] | [?contains(Tags[?Key==`{}`].Value, `{}`)]".format("Name", component)
    )

    logger.info(f"Found ASGs with tag Name: {component} = {filtered_asgs}")

    return next(filtered_asgs)


def get_autorecycling_tags(asg_name: str) -> dict[Any, Any]:
    autoscaling_client: Any = boto3.client("autoscaling", "eu-west-2")
    logger.info("asg_name, {}".format(asg_name))
    autorecycling_tags_filters: list[dict[str, Union[str, list[str]]]] = [
        dict(Name="auto-scaling-group", Values=[asg_name]),
        dict(Name="key", Values=list(autorecycle_tag_names.keys())),
    ]
    responseTags: Any = autoscaling_client.describe_tags(Filters=autorecycling_tags_filters)["Tags"]

    logger.info("ASG Tags, {}".format(responseTags))
    tags: dict[Any, Any] = dict()

    for string_tag in [k for k, v in autorecycle_tag_names.items() if v == "string"]:
        _add_tag(string_tag, responseTags, tags)

    for boolean_tag in [k for k, v in autorecycle_tag_names.items() if v == "boolean"]:
        _add_boolean_tag(boolean_tag, responseTags, tags)

    return tags


def _add_tag(tag_name: str, responseTags: List[dict], tags: dict) -> None:
    values: list[Any] = _get_tag_values(responseTags, tag_name)
    if values:
        tags[tag_name] = values[0]


def _add_boolean_tag(tag_name: str, responseTags: List[dict], tags: dict) -> None:
    values: list[Any] = _get_tag_values(responseTags, tag_name)
    if values:
        tags[tag_name] = values[0].lower() == "true"


def _get_tag_values(tagsList: List[dict], tagName: str) -> list[Any]:
    values: list[Any] = [tag["Value"] for tag in tagsList if tag["Key"] == tagName]
    return values

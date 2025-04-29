#!/usr/bin/env python

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def get_component_name(event: dict[str, Any]) -> Optional[str]:
    """
    Extracts the component name from the event, if we determine the component should be recycled.

    The component name is derived from the Auto Scaling Group (ASG) name.
    If a component name was not found, None is returned.

    This actually only returns the component name if the ASG tags were updated,
    or the launchconfig/template was updated.
    Any other ASG update event will not trigger a recycle.
    """

    component_name: str

    if "detail" not in event or not isinstance(event["detail"], dict):
        logger.info("No detail in event")
        return None

    if "requestParameters" not in event["detail"] or not isinstance(event["detail"]["requestParameters"], dict):
        logger.info("No requestParameters in event")
        return None

    if event["detail"].get("eventName") in ["CreateOrUpdateTags", "DeleteTags"]:
        if "tags" not in event["detail"]["requestParameters"]:
            logger.info("No tags in event")
            return None

        component_name = event["detail"]["requestParameters"]["tags"][0]["resourceId"].split("-asg-")[0]
        if not component_name:
            logger.info("No component name in event")
            return None

        logger.info(f"Component name was set to: {component_name}")
        return component_name

    component_name = event["detail"]["requestParameters"]["autoScalingGroupName"].split("-asg-")[0]
    if not component_name:
        logger.info("No component name in event")
        return None

    logger.info(f"Component name was set to: {component_name}")

    if (
        "launchConfigurationName" not in event["detail"]["requestParameters"]
        and "launchTemplate" not in event["detail"]["requestParameters"]
    ):
        logger.info("The launchConfiguration/launchTemplate is unchanged. Skipping recycling")
        return None

    return component_name


def assert_recyclable(asg_tags: Any, component: Any, environment: Any) -> bool:
    required_tags = ["autorecycle_recycle_on_asg_update", "autorecycle_strategy"]
    missing_tags = [tag for tag in required_tags if tag not in asg_tags]
    if missing_tags:
        logger.info(
            f"The component {component} is not recycleable in {environment} - missing required tags {missing_tags}"
        )
        return False
    if not asg_tags["autorecycle_recycle_on_asg_update"]:
        logger.info(f"The component {component} is not recycleable in {environment}")
        return False
    logger.info(f"The component {component} is recycleable in {environment}")
    return True

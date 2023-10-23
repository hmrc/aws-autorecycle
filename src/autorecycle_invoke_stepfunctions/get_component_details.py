#!/usr/bin/env python

import logging
from typing import Any, Tuple, Union

logger = logging.getLogger(__name__)


class NotRecyclable(Exception):
    pass


class EventDetailNotFound(Exception):
    pass


class ComponentNameNotSet(Exception):
    pass


class RequestParametersNotFound(Exception):
    pass


def get_component_name(event: Any) -> Any:
    try:
        if event["detail"]:
            if "requestParameters" in event["detail"]:
                component_name = event["detail"]["requestParameters"]["autoScalingGroupName"].split("-asg-")[0]
                if component_name:
                    logger.info("Component name was set to: {}".format(component_name))
                    if "launchConfigurationName" in event["detail"]["requestParameters"]:
                        logger.info("This component: {} is using a launchConfiguration".format(component_name))
                    elif "launchTemplate" in event["detail"]["requestParameters"]:
                        logger.info("This component: {} is using a launchTemplate".format(component_name))
                    else:
                        logger.info("The ASG was updated, but did not change the launchConfiguration or launchTemplate")
                        raise SystemExit
                    return component_name
                else:
                    raise ComponentNameNotSet
            else:
                raise RequestParametersNotFound
        else:
            raise EventDetailNotFound
    except Exception as e:
        logger.info("The event detail was not found when attempting to extract the component's name")
        raise e


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

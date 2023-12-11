#!/usr/bin/env python
import itertools
import logging
from datetime import timedelta
from typing import Any, Dict, List

import aws_lambda_logging
import boto3
from botocore.config import Config

config = Config(retries={"max_attempts": 60, "mode": "standard"})
logger = logging.getLogger("monitor_autorecycle")
logger.setLevel(logging.INFO)

class ScaledDownASGException(Exception): pass

def lambda_handler(event: Any, context: Any) -> Any:
    aws_lambda_logging.setup(
        level="INFO",
        aws_request_id=context.aws_request_id,
        function=context.function_name,
        tags="monitor_autorecycle",
    )

    if "component" not in event:
        logger.info("No component in event")
        raise Exception("No component in event")

    result = _monitor_autorecycle(event)
    return result


def check(component: str) -> bool:
    asg = _describe_asg(component)
    scaling_activities = _describe_scaling_activities(asg["AutoScalingGroupName"])
    launching_activities = _get_launching_activities(scaling_activities)

    if not launching_activities:
        logger.warning(f"No 'launching' scaling activities found on the asg: {asg['AutoScalingGroupName']}")
        return False

    return check_instances(asg, launching_activities)


def check_instances(asg: Dict, launching_activities: List[dict]) -> bool:
    # If all instances in the ASG are healthy, InService and launched at the same time, then recycling is done
    last_launching_activity_times = []

    for instance in asg["Instances"]:
        instance_id = instance["InstanceId"]
        health_status = instance["HealthStatus"]
        lifecycle_state = instance["LifecycleState"]

        logger.info(f"Found an instance: {instance_id}")
        logger.info(f"{instance_id} has a HealthStatus of {health_status}")
        logger.info(f"{instance_id} has a LifecycleState of {lifecycle_state}")

        if health_status != "Healthy" or lifecycle_state != "InService":
            logger.info(f"auto-recycling is not complete because {instance_id} is not in a healthy state")
            return False

        last_activity_time = _last_instance_activity_time(launching_activities, instance_id)
        if last_activity_time is None:
            logger.info(
                f"auto-recycling is not complete because last_activity_time could not be determined for {instance_id}"
            )
            return False

        last_launching_activity_times.append(last_activity_time)

    if not _compare_start_times(last_launching_activity_times, 2):
        logger.info(
            "auto-recycling is not complete because the instances were not launched within 2 minutes of each other"
        )
        return False

    return True


def _compare_start_times(last_launching_activity_times: List[Any], delta: int) -> bool:
    for a, b in itertools.combinations(last_launching_activity_times, 2):
        diff = timedelta(minutes=delta)
        if a - b > diff or b - a > diff:
            return False
    else:
        return True


def _monitor_autorecycle(event: Any) -> Any:
    output = event
    if "message_content" not in output:
        output["message_content"] = {}

    if "counter" not in output:
        output["counter"] = 0

    output["counter"] += 1

    if output["counter"] > 20:
        output["message_content"]["color"] = "danger"
        output["message_content"]["text"] = "Autorecycling appears to be taking too long :scream: please investigate."
        output["channels"] = event["channels"]
        output["status"] = "fail"
        output["recycle_success"] = False
        return output

    try:
        if check(event["component"]):
            logger.info("All Instances in the ASG are Healthy and InService")
            output["message_content"]["text"] = "Autorecycling has successfully completed"
            output["recycle_success"] = True
        else:
            output["recycle_success"] = False
    except ScaledDownASGException:
        output["message_content"]["text"] = "The ASG is scaled down to 0 instances, auto-recycling is not required"
        output["recycle_success"] = True

    return output


def _describe_asg(component: str) -> Any:
    asg_client = boto3.client("autoscaling", "eu-west-2", config=config)

    auto_scaling_groups = []
    for page in asg_client.get_paginator("describe_auto_scaling_groups").paginate(PaginationConfig={"PageSize": 100}):
        auto_scaling_groups += page["AutoScalingGroups"]
    groups = {"AutoScalingGroups": auto_scaling_groups}

    logger.info("Finding a matching ASG for: {}".format(component))

    lookup = [asg for asg in groups["AutoScalingGroups"] if asg["AutoScalingGroupName"].startswith(f"{component}-asg")]

    if lookup:
        logger.info("Found an ASG called: {}".format(lookup[0]["AutoScalingGroupName"]))

        if lookup[0]["MaxSize"] == 0:
            logger.info("The ASG is scaled down to 0 instances - not attempting to recycle")
            raise ScaledDownASGException()

        if lookup[0]["Instances"]:
            logger.info("We have found {} instances in the ASG".format(len(lookup[0]["Instances"])))
            return lookup[0]
        else:
            logger.info("We have found 0 instances in the ASG, maybe this is in-out recycling")
    else:
        logger.info("Could not find an ASG for: {}".format(component))

    raise Exception("No ASG found for {}".format(component))


def _describe_scaling_activities(asg_name: str) -> Any:
    asg_client = boto3.client("autoscaling", "eu-west-2", config=config)
    response = asg_client.describe_scaling_activities(
        AutoScalingGroupName=asg_name,
        MaxRecords=20,
    )
    return response["Activities"]


def _get_launching_activities(scaling_activities: Any) -> List[Dict]:
    return [activity for activity in scaling_activities if "Launching" in activity["Description"]]


def _last_instance_activity_time(scaling_activities: List[Dict], instance_id: str) -> Any:
    instance_activities = [activity for activity in scaling_activities if instance_id in activity["Description"]]

    if instance_activities:
        return sorted([activity["StartTime"] for activity in instance_activities])[-1]

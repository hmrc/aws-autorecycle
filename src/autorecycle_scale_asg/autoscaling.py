from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, List

import boto3

if TYPE_CHECKING:
    from mypy_boto3_autoscaling import AutoScalingClient
    from mypy_boto3_autoscaling.type_defs import ActivityTypeDef, AutoScalingGroupTypeDef, EmptyResponseMetadataTypeDef

from src.autorecycle_scale_asg.logger import logger


def describe_asg(component_name_maybe_with_az_suffix: str) -> List[AutoScalingGroupTypeDef]:
    asg_client: AutoScalingClient = boto3.client("autoscaling", "eu-west-2")

    auto_scaling_groups: List[AutoScalingGroupTypeDef] = []
    for page in asg_client.get_paginator("describe_auto_scaling_groups").paginate(PaginationConfig={"PageSize": 100}):
        auto_scaling_groups += page["AutoScalingGroups"]  # type: ignore

    (component_name, number_of_subs_made) = re.subn("_[abc]$", "", component_name_maybe_with_az_suffix)
    extension_re = ""
    if number_of_subs_made == 1:
        extension_re = "(?:_[abc])"

    matching_asgs: List[AutoScalingGroupTypeDef] = []
    matcher = re.compile(rf"(^{component_name}){extension_re}-asg-[a-z\d]+$")
    for asg in auto_scaling_groups:
        if matcher.match(asg["AutoScalingGroupName"]):
            matching_asgs.append(asg)

    if not matching_asgs:
        msg = rf"Could not find ASGs matching: `^{component_name}(_[abc])?-asg-[a-z\d]+$`."
        logger.info(msg)
        raise Exception(msg)

    return matching_asgs


def execute_scaling_policy(asg_name: str, policy_name: str) -> EmptyResponseMetadataTypeDef:
    try:
        asg_client: AutoScalingClient = boto3.client("autoscaling", "eu-west-2")
        logger.info("Executing scaling policy: " + policy_name + " on this ASG: " + asg_name)

        response = asg_client.execute_policy(AutoScalingGroupName=asg_name, PolicyName=policy_name)
        return response
    except Exception as e:
        logger.info("Could not execute scaling policy: {} on this ASG: {} ".format(policy_name, asg_name))
        raise e


def describe_scaling_activities(asg_name: str) -> ActivityTypeDef:
    asg_client: AutoScalingClient = boto3.client("autoscaling", "eu-west-2")
    logger.info("Checking latest scaling activity on this ASG: " + asg_name)

    response = asg_client.describe_scaling_activities(AutoScalingGroupName=asg_name, MaxRecords=1)

    # If there have been no scaling activities for six weeks then the response
    # will be broken.
    if len(response["Activities"]) == 0:
        return {
            "ActivityId": ".",
            "AutoScalingGroupName": asg_name,
            "Cause": "?",
            "Progress": 100,
            "StartTime": datetime.datetime.now() - datetime.timedelta(weeks=6),
            "StatusCode": "Successful",
        }

    return response["Activities"][0]

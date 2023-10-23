from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union

import pytz

if TYPE_CHECKING:
    from mypy_boto3_autoscaling.type_defs import ActivityTypeDef, AutoScalingGroupTypeDef, InstanceTypeDef

from src.autorecycle_scale_asg.lambda_types import Event
from src.autorecycle_scale_asg.logger import logger


@dataclass
class NextAsgAction:
    asg_name: str
    action: Literal["in", "out"]


def get_overall_progress(activities: List[ActivityTypeDef]) -> bool:
    for activity in activities:
        if activity.get("Progress") != 100:
            return False
    return True


def get_overall_statuscode(activities: List[ActivityTypeDef]) -> bool:
    for activity in activities:
        if activity.get("StatusCode") != "Successful":
            return False
    return True


def recently_scaled(activity: ActivityTypeDef, min_age: int = 10) -> bool:
    utc = pytz.UTC
    lc_age = utc.localize(datetime.now() - timedelta(minutes=min_age))
    if "EndTime" not in activity:
        return False
    return bool(activity["EndTime"] > lc_age)


def get_launch_template_version(asg_or_instance: Union[AutoScalingGroupTypeDef, InstanceTypeDef]) -> Optional[str]:
    # TODO: Remove this, all ASGs/instances should have a version now we no longer have launch configs
    if "LaunchTemplate" not in asg_or_instance:
        return None

    return str(asg_or_instance["LaunchTemplate"]["Version"])


def get_next_asg_action(
    asgs: List[AutoScalingGroupTypeDef], last_activities: Dict[str, ActivityTypeDef]
) -> Optional[NextAsgAction]:
    for asg in asgs:
        asg_name = asg["AutoScalingGroupName"]
        logger.info("Checking {} for instances to use out strategy".format(asg_name))
        if len(asg["Instances"]) == 0:
            logger.info("{} has no instances, setting scaling strategy to out".format(asg_name))
            return NextAsgAction(action="out", asg_name=asg_name)

    for asg in asgs:
        asg_name = asg["AutoScalingGroupName"]
        asg_recently_scaled = recently_scaled(last_activities[asg_name])
        asg_launch_template_version = get_launch_template_version(asg)

        for instance in asg["Instances"]:
            logger.info("Checking {} instances for Launch Config/Templates".format(asg_name))
            instance_launch_template_version = get_launch_template_version(instance)

            if (
                asg_launch_template_version is not None
                and instance_launch_template_version is not None
                and asg_launch_template_version == instance_launch_template_version
                and asg_recently_scaled
            ):
                logger.info(
                    f"The launch template version {instance_launch_template_version} for {instance['InstanceId']} matches ASG's {asg_launch_template_version}"
                )
            else:
                logger.info(
                    f"Instance {instance['InstanceId']} in {asg_name} will be terminated. Setting scale strategy to in"
                )
                return NextAsgAction(action="in", asg_name=asg_name)

    return None


def create_output_params(event: Event) -> Event:
    return Event(
        channels=event.channels,
        component=event.component,
        counter=event.counter + 1 if event.counter else 1,
        emoji=":robot_face:",
        monitoring_slack_channel=event.monitoring_slack_channel,
        notify_pager_duty=event.notify_pager_duty,
        status=True,
        success_channel=event.success_channel,
        team=event.team,
        text=f"*{event.component}*",
        username="AutoRecycling",
    )

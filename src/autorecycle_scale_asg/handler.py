#!/usr/bin/env python
import os
from typing import List, Dict, Any

from src.autorecycle_scale_asg import autorecycle, autoscaling
from src.autorecycle_scale_asg.lambda_types import Event
from src.autorecycle_scale_asg.logger import logger


@logger.inject_lambda_context(log_event=True)
def lambda_handler(lambda_event: Event, context: Any) -> Dict:
    result = handle_event(lambda_event)
    return result.model_dump(exclude_unset=True)


def handle_event(lambda_event: Event) -> Event:
    event = Event.model_validate(lambda_event)
    logger.debug("Initiating with the following event")
    logger.debug(event)

    if not event.counter:
        event.counter = 0
        event.channels = event.success_channel
        return scale_asg(event)
    elif event.counter < 60:
        return scale_asg(event)
    elif event.counter == 60:
        return Event(
            component=event.component,
            channels=event.monitoring_slack_channel,
            message_content = Event.MessageContent(
                color="danger",
                text=f"Autorecycling of {event.component} appears to be taking too long :scream: please investigate.",
            ),
            monitoring_slack_channel=event.monitoring_slack_channel,
            pager_duty_description=f"Autorecycling of {event.component} appears to be taking too long. Please investigate.",
            pager_duty_event_type="trigger",
            success_channel=event.success_channel,
            status="fail",
        )
    else:
        raise Exception


def scale_asg(event: Event) -> Event:
    output = autorecycle.create_output_params(event)

    message_content_fields: List[Dict[str, Any]] = [
        {
            "title": "Component",
            "value": event.component,
            "short": True,
        },
        {
            "title": "Environment",
            "value": os.getenv("ENVIRONMENT"),
            "short": True,
        },
    ]

    try:
        asgs = autoscaling.describe_asg(event.component)
        asg_activity_details = {}

        for asg in asgs:
            asg_name = asg["AutoScalingGroupName"]
            asg_activity_details[asg_name] = autoscaling.describe_scaling_activities(asg_name)

        overall_progress = autorecycle.get_overall_progress(list(asg_activity_details.values()))
        overall_statuscode = autorecycle.get_overall_statuscode(list(asg_activity_details.values()))

        if not overall_progress:
            logger.debug("Scaling activity is in progress...")
            output.message_content = Event.MessageContent(
                color="good",
                fields=message_content_fields,
                text="Auto-recycling has successfully initiated",
            )
            output.recycle_success = False
            return output

        if not overall_statuscode:
            logger.debug("The last scaling event was not Successful")
            output.message_content = Event.MessageContent(
                color="danger",
                fields=message_content_fields,
                text="The last scaling event was not Successful. Please investigate",
            )
            output.recycle_success = False
            output.pager_duty_description = "The last scaling event was not Successful. Please investigate"
            output.pager_duty_event_type = "trigger"
            output.status = "fail"
            return output

        next_step = autorecycle.get_next_asg_action(asgs, asg_activity_details)
        if next_step:
            logger.info(f"Initiating scale {next_step.action} policy")
            scale_policy = f"recycle-scale-{next_step.action}"
            autoscaling.execute_scaling_policy(next_step.asg_name, scale_policy)
            if output.counter == 1:
                output.message_content = Event.MessageContent(
                    color="good",
                    fields=message_content_fields,
                    text="Auto-recycling has successfully initiated",
                )
                output.recycle_success = False
            else:
                output.recycle_success = False
            return output

        logger.info("Autorecycling has successfully completed")
        output.recycle_success = True
        output.message_content = Event.MessageContent(
            color="good",
            fields=message_content_fields,
            text="Auto-recycling has successfully initiated",
        )
        # Doesn't make much sense, recycle_success and status both mean similar things. Keeping
        # the behaviour for now as I don't want to break anything else and there aren't many tests
        output.status = True
        return output

    except Exception as err:
        logger.debug(f"Caught the exception {err}")
        output.recycle_success = False
        output.message_content = Event.MessageContent(
            color="danger",
            fields=message_content_fields,
            text="The last scaling event was not Successful. Please investigate",
        )
        output.pager_duty_description = "The last scaling event was not Successful. Please investigate"
        output.pager_duty_event_type = "trigger"
        output.exception = repr(err)
        output.status = "fail"
        return output

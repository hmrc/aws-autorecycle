import json
import os
import unittest
from datetime import datetime
from unittest import mock

from dateutil.tz import tzutc
from freezegun import freeze_time

from src.autorecycle_scale_asg.autorecycle import (
    NextAsgAction,
    create_output_params,
    get_next_asg_action,
    get_overall_progress,
    get_overall_statuscode,
    recently_scaled,
)
from src.autorecycle_scale_asg.lambda_types import Event


def load_json(name):
    with open(f"tests/test_data/autorecycle_scale_asg/{name}.json", "r") as event:
        return json.load(event)


class TestGetOverallProgress(unittest.TestCase):
    def test_get_overall_progress(self):
        """
        Test get overall progress
        """
        test_details = []
        test_details.append(load_json("describe-last-scaling-activity"))
        response = get_overall_progress(test_details)
        self.assertTrue(response)

    def test_get_overall_statuscode(self):
        """
        Test get overall statuscode
        """
        test_details = []
        test_details.append(load_json("describe-last-scaling-activity"))
        response = get_overall_statuscode(test_details)
        self.assertTrue(response)


@mock.patch("src.autorecycle_scale_asg.autorecycle.recently_scaled", return_value=True)
class TestGetNextASGActionWithRecentlyScaled(unittest.TestCase):
    def test_all_up_to_date_instances_should_do_nothing(self, recently_scaled):
        """
        Test that when all instances are up-to-date (i.e. each instance's launch template version
        matches the ASGs' version) no action should take place.
        """
        test_asgs = load_json("describe-2-asgs-2-up-to-date-instances")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertIsNone(response)

    def test_one_out_of_date_instance_should_scale_in(self, recently_scaled):
        """
        Test that when one ASG's instance(s) is out-of-date (i.e. each instance's launch template
        version does not match the ASG's version) scaling in should take place.
        """
        test_asgs = load_json("describe-2-asgs-2-instances-1-out-of-date")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertEqual(NextAsgAction(action="in", asg_name="test_component_b"), response)

    def test_no_instances_should_scale_out(self, recently_scaled):
        """
        Test that when there are no running instances, scale-out should take place.
        """
        test_asgs = load_json("describe-2-asgs-no-instances")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertEqual(NextAsgAction(action="out", asg_name="test_component_a"), response)


@mock.patch("src.autorecycle_scale_asg.autorecycle.recently_scaled", return_value=True)
class TestGetNextASGUsingLaunchTemplatesActionWithRecentlyScaled(unittest.TestCase):
    def test_instances_out_of_date_should_scale_in(self, recently_scaled):
        test_asgs = load_json("describe-asg-launch-template-2-out-of-date")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertEqual(
            NextAsgAction(action="in", asg_name="admin_frontend_proxy-asg-00d8db81999d264f72da684c9b"), response
        )

    def test_instances_moving_from_launch_configuration_to_launch_templates_should_scale_in(self, recently_scaled):
        test_asgs = load_json("describe-asg-launch-template-from-launch-configuration")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertEqual(
            NextAsgAction(action="in", asg_name="admin_frontend_proxy-asg-00d8db81999d264f72da684c9b"), response
        )


@mock.patch("src.autorecycle_scale_asg.autorecycle.recently_scaled", return_value=False)
class TestGetNextASGActionWithNotRecentlyScaled(unittest.TestCase):
    def test_all_up_to_date_instances_should_scale_in(self, recently_scaled):
        """
        Test that when the last scaling activity was not recent and all instances
        are up-to-date (i.e. each instance has a launch config) scaling in should
        take place.
        """
        test_asgs = load_json("describe-2-asgs-2-up-to-date-instances")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertEqual(NextAsgAction(action="in", asg_name="test_component_a"), response)

    def test_one_out_of_date_instance_should_scale_in(self, recently_scaled):
        """
        Test that when the last scaling activity was not recent and one ASG's instance(s)
        is out-of-date (i.e. does not have a launch config entry) scaling in should take
        place.
        """
        test_asgs = load_json("describe-2-asgs-2-instances-1-out-of-date")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertEqual(NextAsgAction(action="in", asg_name="test_component_a"), response)

    def test_no_instances_should_scale_out(self, recently_scaled):
        """
        Test that when the last scaling activity was not recent and there are no running
        instances, scale-out should take place.
        """
        test_asgs = load_json("describe-2-asgs-no-instances")
        response = get_next_asg_action(test_asgs, recently_scaled)
        self.assertEqual(NextAsgAction(action="out", asg_name="test_component_a"), response)


class TestRecentlyScaled(unittest.TestCase):
    @freeze_time("2022-01-26 14:21:34", tz_offset=-0)
    def test_recently_scaled_true_if_not_older(self):
        details = {"EndTime": datetime(2022, 1, 26, 14, 15, 5, tzinfo=tzutc())}
        self.assertTrue(recently_scaled(details))

    @freeze_time("2022-01-26 14:21:34", tz_offset=-0)
    def test_recently_scaled_false_if_older(self):
        details = {"EndTime": datetime(2022, 1, 26, 13, 15, 5, tzinfo=tzutc())}
        self.assertFalse(recently_scaled(details))

    @freeze_time("2022-01-26 14:21:34", tz_offset=-1)
    def test_recently_scaled_true_if_bst(self):
        details = {"EndTime": datetime(2022, 1, 26, 14, 15, 5, tzinfo=tzutc())}
        self.assertTrue(recently_scaled(details))

    @freeze_time("2022-01-26 14:21:34", tz_offset=-0)
    def test_recently_scaled_false_if_no_recent_activity(self):
        details = {"Progress": 100, "StatusCode": "Successful"}
        self.assertFalse(recently_scaled(details))


class TestRecycling(unittest.TestCase):
    def test_creates_expected_output_params_from_event(self):
        output = create_output_params(
            Event(
                component="thecomponent",
                counter=1,
                channels="event-integ-recycle",
                success_channel="event-integ-recycle_success",
                monitoring_slack_channel="monitoring_slack_channel",
                notify_pager_duty=True,
                team="telemetry",
            )
        )
        output.message_content = Event.MessageContent(
            color="good",
            fields=[
                {
                    "title": "Component",
                    "value": "{}".format("thecomponent"),
                    "short": True,
                },
                {
                    "title": "Environment",
                    "value": os.getenv("ENVIRONMENT"),
                    "short": True,
                },
            ],
            text="Auto-recycling has successfully initiated",
        )
        self.assertEqual(
            Event(
                component="thecomponent",
                counter=2,
                status=True,
                username="AutoRecycling",
                channels="event-integ-recycle",
                success_channel="event-integ-recycle_success",
                message_content={
                    "color": "good",
                    "fields": [
                        {
                            "title": "Component",
                            "value": "thecomponent",
                            "short": True,
                        },
                        {
                            "title": "Environment",
                            "value": os.getenv("ENVIRONMENT"),
                            "short": True,
                        },
                    ],
                    "text": "Auto-recycling has successfully initiated",
                },
                text="*thecomponent*",
                emoji=":robot_face:",
                monitoring_slack_channel="monitoring_slack_channel",
                notify_pager_duty=True,
                team="telemetry",
            ),
            output,
        )

    def test_creates_expected_output_params_from_event_when_optional_not_present(self):
        output = create_output_params(
            Event(
                component="thecomponent",
                counter=1,
                channels="event-integ-recycle",
                success_channel="event-integ-recycle_success",
            )
        )
        output.message_content = Event.MessageContent(
            color="good",
            fields=[
                {
                    "title": "Component",
                    "value": "{}".format("thecomponent"),
                    "short": True,
                },
                {
                    "title": "Environment",
                    "value": os.getenv("ENVIRONMENT"),
                    "short": True,
                },
            ],
            text="Auto-recycling has successfully initiated",
        )
        self.assertEqual(
            Event(
                component="thecomponent",
                counter=2,
                status=True,
                username="AutoRecycling",
                channels="event-integ-recycle",
                success_channel="event-integ-recycle_success",
                message_content={
                    "color": "good",
                    "fields": [
                        {
                            "title": "Component",
                            "value": "{}".format("thecomponent"),
                            "short": True,
                        },
                        {
                            "title": "Environment",
                            "value": os.getenv("ENVIRONMENT"),
                            "short": True,
                        },
                    ],
                    "text": "Auto-recycling has successfully initiated",
                },
                text=f"*thecomponent*",
                emoji=":robot_face:",
            ),
            output,
        )

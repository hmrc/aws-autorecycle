import logging
import unittest

from unittest.mock import patch, MagicMock
from src.autorecycle_scale_asg.handler import lambda_handler
from src.autorecycle_scale_asg.lambda_types import Event
from tests.unit.autorecycle_scale_asg.fixtures import lambda_context


class MockException(Exception):
    pass


class TestMain(unittest.TestCase):
    def test_overrides_monitoring_slack_channel_if_supplied(self):
        """
        Test override Slack channel
        """
        event = Event(
            component="sensu", counter=60, monitoring_slack_channel="telemetry", success_channel="event-test-recycle"
        )
        result = lambda_handler(event, lambda_context())
        self.assertEqual("telemetry", result["channels"])
        self.assertEqual("telemetry", result["monitoring_slack_channel"])

    def test_defaults_to_infra_internal_if_no_monitoring_channel_supplied(self):
        """
        Test default Slack channel
        """
        event = Event(component="sensu", counter=60, success_channel="event-test-recycle")
        result = lambda_handler(event, lambda_context())
        self.assertEqual("team-infra-alerts", result["channels"])

    def test_constructs_pager_duty_message_on_failure(self):
        event = Event(
            component="sensu",
            counter=60,
            monitoring_slack_channel="telemetry",
            success_channel="event-test-recycle",
        )
        result = lambda_handler(event, lambda_context())
        self.assertEqual(
            "Autorecycling of sensu appears to be taking too long. Please investigate.",
            result["pager_duty_description"],
        )
        self.assertEqual("trigger", result["pager_duty_event_type"])

    @patch("boto3.client")
    def test_when_exception_thrown_during_scaling_it_is_handled_and_output_preserved(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.side_effect = MockException
        result = lambda_handler(
            Event(counter=5, component="sensu", channels="telemetry-alerts", success_channel="telemetry_success"),
            lambda_context(),
        )
        logger = logging.getLogger("autorecycle_scale_asg")
        logger.setLevel(logging.DEBUG)
        logger.debug("Result was {}".format(result))
        self.assertEqual(result["counter"], 6)
        self.assertEqual(result["recycle_success"], False)
        self.assertEqual(
            result["message_content"]["text"],
            "The last scaling event was not Successful. Please investigate",
        )
        self.assertEqual(
            result["pager_duty_description"],
            "The last scaling event was not Successful. Please investigate",
        )
        self.assertEqual(result["pager_duty_event_type"], "trigger")
        self.assertEqual(result["exception"], "MockException()")
        self.assertEqual(result["status"], "fail")

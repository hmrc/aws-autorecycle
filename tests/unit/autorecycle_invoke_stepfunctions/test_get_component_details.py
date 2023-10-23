import json
import os
import unittest

from mock import patch
from parameterized import parameterized

from src.autorecycle_invoke_stepfunctions.get_component_details import assert_recyclable, get_component_name


class GetComponentDetails(unittest.TestCase):
    def test_get_component_name_with_valid_json(self):
        """
        With valid event json
        """
        with open("tests/test_data/test-event.json", "rb") as f:
            test_event = json.load(f)
        self.result = get_component_name(test_event)
        assert self.result == "test-protected-mdtp"

    def test_get_component_name_with_launch_template(self):
        """
        With a component which is recyclable and using a launch template
        """
        with open("tests/test_data/test-event-launch-template.json", "rb") as f:
            test_event_lt = json.load(f)

        self.assertEqual("test-protected-mdtp", get_component_name(test_event_lt))

    def test_exception_is_raised_with_no_event_detail(self):
        """
        When there is no event detail we should raise an exception
        """
        with open("tests/test_data/test-event-launch-template.json", "rb") as f:
            test_event_lt = json.load(f)

        test_event_lt.pop("detail", None)
        with self.assertRaises(KeyError):
            get_component_name(test_event_lt)

    @patch.dict(os.environ, {"ACCOUNT_ID": "1234567890", "SLACK_CHANNEL": "event-test-recycle"})
    def test_system_exit_is_raised_with_no_update(self):
        """
        When launchConfiguration or launchTemplate update not present UpdateAutoScalingGroup event
        """
        with open("tests/test_data/test-event-no-update-present.json", "rb") as f:
            test_event_lt = json.load(f)

        with self.assertRaises(SystemExit):
            get_component_name(test_event_lt)

    def test_assert_recyclable_logs_message_when_component_is_recyclable(self):
        with self.assertLogs("src.autorecycle_invoke_stepfunctions.get_component_details", level="INFO") as logger:
            self.assertTrue(
                assert_recyclable(
                    {
                        "autorecycle_recycle_on_asg_update": True,
                        "autorecycle_strategy": "meh",
                    },
                    "my_component",
                    "qa",
                )
            )
            self.assertEqual(len(logger.output), 1)
            self.assertEqual(
                logger.output[0],
                "INFO:src.autorecycle_invoke_stepfunctions.get_component_details:The component my_component is recycleable in qa",
            )

    def test_assert_recyclable_logs_message_when_not_recycleable(self):
        with self.assertLogs("src.autorecycle_invoke_stepfunctions.get_component_details", level="INFO") as logger:
            self.assertFalse(
                assert_recyclable(
                    {
                        "autorecycle_recycle_on_asg_update": False,
                        "autorecycle_strategy": "meh",
                    },
                    "my_component",
                    "qa",
                )
            )
            self.assertEqual(len(logger.output), 1)
            self.assertEqual(
                logger.output[0],
                "INFO:src.autorecycle_invoke_stepfunctions.get_component_details:The component my_component is not recycleable in qa",
            )

    @parameterized.expand(
        [
            (["autorecycle_recycle_on_asg_update"],),
            (["autorecycle_strategy"],),
            (["autorecycle_recycle_on_asg_update", "autorecycle_strategy"],),
        ]
    )
    def test_assert_recyclable_raises_exception_when_required_asg_tags_missing(self, missing_tags):
        tags = dict(
            autorecycle_recycle_on_asg_update=True,
            autorecycle_strategy="in-out",
            autorecycle_slack_monitoring_channel="alerts",
            autorecycle_notify_pager_duty=False,
        )
        for missing_tag in missing_tags:
            del tags[missing_tag]
        with self.assertLogs("src.autorecycle_invoke_stepfunctions.get_component_details", level="INFO") as logger:
            self.assertFalse(assert_recyclable(tags, "my_component", "qa"))
            self.assertEqual(len(logger.output), 1)
            self.assertEqual(
                logger.output[0],
                f"INFO:src.autorecycle_invoke_stepfunctions.get_component_details:The component my_component is not recycleable in qa - missing required tags {missing_tags}",
            )

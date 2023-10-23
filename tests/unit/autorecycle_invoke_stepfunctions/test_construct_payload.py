import unittest

from src.autorecycle_invoke_stepfunctions.handler import construct_payload


class Construct_payload(unittest.TestCase):
    def test_asgs_config_parsed(self):
        """
        ensure that the Json is parsed and put in the payload
        """
        asg_tags = dict(
            autorecycle_recycle_on_asg_update=True,
            autorecycle_strategy="shake-it-all-about",
            autorecycle_notify_pager_duty=True,
            autorecycle_team="Telemetry",
            autorecycle_slack_monitoring_channel="team-telemetry-alerts",
        )
        result = construct_payload("1234567890", "test-slack", "test-sensu", "test-sensu-12345", asg_tags)
        expected = {
            "component": "test-sensu",
            "auto_scaling_group_name": "test-sensu-12345",
            "emoji": ":robot_face:",
            "strategy": "shake-it-all-about",
            "account_id": "1234567890",
            "success_channel": "test-slack",
            "notify_pager_duty": True,
            "team": "Telemetry",
            "monitoring_slack_channel": "team-telemetry-alerts",
        }
        self.assertEqual(result, expected)

    def test_can_construct_payload_when_optional_config_not_present(self):
        """
        ensure that optional config is handled and won't be in the payload
        """
        asg_tags = dict(
            autorecycle_recycle_on_asg_update=True,
            autorecycle_strategy="shake-it-all-about",
        )
        result = construct_payload("1234567890", "test-slack", "test-sensu", "test-sensu-12345", asg_tags)
        expected = {
            "component": "test-sensu",
            "auto_scaling_group_name": "test-sensu-12345",
            "emoji": ":robot_face:",
            "strategy": "shake-it-all-about",
            "account_id": "1234567890",
            "success_channel": "test-slack",
        }
        self.assertEqual(result, expected)

    def test_all_optional_tags_in_payload(self):
        """
        test that all of the optional payload parameters make it to the payload with correct keys
        """
        asg_tags = dict(
            autorecycle_recycle_on_asg_update=True,
            autorecycle_strategy="strategy",
            autorecycle_slack_monitoring_channel="slack-mon",
            autorecycle_notify_pager_duty=False,
            autorecycle_team="team",
            autorecycle_step_function_name="step-func",
            autorecycle_dry_run=True,
        )

        result = construct_payload("1234567890", "test-slack", "test-sensu", "test-sensu-12345", asg_tags)
        expected = {
            "component": "test-sensu",
            "auto_scaling_group_name": "test-sensu-12345",
            "emoji": ":robot_face:",
            "strategy": "strategy",
            "account_id": "1234567890",
            "success_channel": "test-slack",
            "notify_pager_duty": False,
            "team": "team",
            "monitoring_slack_channel": "slack-mon",
            "step_function_name": "step-func",
            "dry_run": True,
        }
        self.assertEqual(result, expected)

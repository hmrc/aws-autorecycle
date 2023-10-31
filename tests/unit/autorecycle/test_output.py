import unittest

from src.autorecycle.autorecycle_lambda import output


class TestAutoRecycle(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.component = "test"
        self.account_id = "617311445223"
        self.environment = "test"
        self.channel = "foo"

    def create_expected_result(self, channel, text, color, status):
        return {
            "username": "AutoRecycling",
            "status": status,
            "text": "*test*",
            "component": "test",
            "channels": channel,
            "message_content": {
                "color": color,
                "text": text,
                "fields": [
                    {"title": "Component Name", "value": "recycle-test", "short": True},
                    {"title": "Environment", "value": None, "short": True},
                ],
            },
            "emoji": ":robot_face:",
        }

    def test_output_success(self):
        """
        When the function is called with a success of True the correct dictionary is returned
        """
        expected_result = self.create_expected_result(
            channel="foo",
            text="Auto-recycling was successfully initiated",
            color="good",
            status="success",
        )
        message = output(self.component, True, self.channel)
        self.assertEqual(message, expected_result)

    def test_output_failure(self):
        """
        When the function is called with a success of False the correct dictionary is returned
        """
        expected_result = self.create_expected_result(
            channel="team-infra-alerts",
            text="Auto-recycling has failed",
            color="danger",
            status="failure",
        )
        message = output(self.component, False, self.channel)
        self.assertEqual(message, expected_result)

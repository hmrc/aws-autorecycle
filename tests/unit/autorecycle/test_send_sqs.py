import unittest

import boto3
from botocore.exceptions import ClientError
from mock import patch
from moto import mock_sqs

from src.autorecycle.autorecycle_lambda import send_to_sqs


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

    @mock_sqs
    def test_send_sqs_message(self):
        expected_result = self.create_expected_result(
            channel=self.channel,
            text="Auto-recycling was successfully initiated",
            color="good",
            status="success",
        )
        boto3.setup_default_session(region_name="eu-west-2")
        sqs = boto3.resource("sqs")
        self.queue = sqs.create_queue(QueueName="recycle-{}".format(self.component))
        message = send_to_sqs(self.component, self.account_id, self.channel)
        self.assertEqual(message, expected_result)

    @patch("src.autorecycle.autorecycle_lambda.boto3")
    def test_send_sqs_message_sqs_error(self, mock_boto3):
        """
        When the client makes a bad request it should result in a failure message
        """
        expected_result = self.create_expected_result(
            channel="team-infra-alerts",
            text="Auto-recycling has failed",
            color="danger",
            status="failure",
        )
        mock_boto3.client.return_value.send_message.side_effect = ClientError({}, {})
        message = send_to_sqs(self.component, self.account_id, self.channel)
        self.assertEqual(message, expected_result)

    @patch("src.autorecycle.autorecycle_lambda.boto3")
    def test_send_sqs_message_sqs_bad_response(self, mock_boto3):
        """
        When the response from SQS is missing the MessageId it should result in a failure message
        """
        expected_result = self.create_expected_result(
            channel="team-infra-alerts",
            text="Auto-recycling has failed",
            color="danger",
            status="failure",
        )
        mock_boto3.client.return_value.send_message.return_value = {}
        message = send_to_sqs(self.component, self.account_id, self.channel)
        self.assertEqual(message, expected_result)

    @patch("src.autorecycle.autorecycle_lambda.boto3")
    def test_send_sqs_message_sqs_unknown_exception(self, mock_boto3):
        """
        When an unknown exception occurs a failure message should be sent
        """
        expected_result = self.create_expected_result(
            channel="team-infra-alerts",
            text="Auto-recycling has failed",
            color="danger",
            status="failure",
        )
        mock_boto3.client.return_value.send_message.side_effect = Exception("test exception")
        message = send_to_sqs(self.component, self.account_id, self.channel)
        self.assertEqual(message, expected_result)

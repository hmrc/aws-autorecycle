import json
import os
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from src.get_consul_nodes.main import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch.dict(os.environ, {"environment": "integration"})
    @patch("boto3.client")
    @patch("urllib.request.urlopen")
    def test_successful_response(self, mock_urlopen, mock_boto_client):
        # Mock leader response
        mock_leader_response = MagicMock()
        mock_leader_response.read.return_value = b'"10.0.0.1:8300"'
        mock_leader_response.__enter__.return_value = mock_leader_response

        # Mock members response
        mock_members_response = MagicMock()
        mock_members_response.read.return_value = json.dumps(
            [{"Addr": "10.0.0.3"}, {"Addr": "10.0.0.2"}, {"Addr": "10.0.0.1"}]
        ).encode("utf-8")
        mock_members_response.__enter__.return_value = mock_members_response

        mock_urlopen.side_effect = [mock_leader_response, mock_members_response]

        # Mock EC2 describe_instances
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {"InstanceId": "i-consulleader", "NetworkInterfaces": [{"PrivateIpAddress": "10.0.0.1"}]},
                        {"InstanceId": "i-consulfollowerA", "NetworkInterfaces": [{"PrivateIpAddress": "10.0.0.2"}]},
                        {"InstanceId": "i-consulfollowerB", "NetworkInterfaces": [{"PrivateIpAddress": "10.0.0.3"}]},
                    ]
                }
            ]
        }
        mock_boto_client.return_value = mock_ec2

        event = {}
        context = None

        response = lambda_handler(event, context)

        self.assertEqual(len(response["instanceList"]), 3)
        self.assertEqual(
            response["instanceList"],
            [
                {"ip": "10.0.0.3", "instanceId": "i-consulfollowerB"},
                {"ip": "10.0.0.2", "instanceId": "i-consulfollowerA"},
                {"ip": "10.0.0.1", "instanceId": "i-consulleader"},
            ],
        )

    @patch.dict(os.environ, {"environment": "test"})
    @patch("boto3.client")
    @patch("urllib.request.urlopen")
    def test_leader_request_fails(self, mock_urlopen, mock_boto_client):
        # Simulate a 500 error from /v1/status/leader
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://consul-test.test.mdtp:8500/v1/status/leader",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=None,
        )

        with self.assertRaises(Exception) as context:
            lambda_handler({}, None)

        self.assertIn("Get Consul Nodes Failed", str(context.exception))
        self.assertIn("Internal Server Error", str(context.exception))


if __name__ == "__main__":
    unittest.main()

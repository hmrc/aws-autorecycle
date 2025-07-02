import unittest
from unittest.mock import patch, MagicMock
import os

from src.terminate_consul_instance.main import lambda_handler


class TestTerminateInstanceLambda(unittest.TestCase):

    @patch.dict(os.environ, {"AWS_DEFAULT_REGION": "eu-west-2", "environment": "integration"})
    @patch("boto3.client")
    def test_successful_termination(self, mock_boto_client):
        mock_ec2 = MagicMock()
        mock_ec2.terminate_instances.return_value = {"TerminatingInstances": [{"InstanceId": "i-followerA"}]}
        mock_boto_client.return_value = mock_ec2

        event = {"instanceId": "i-followerA"}
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Termination initiated for i-followerA", response["body"])
        self.assertIn("TerminatingInstances", response["response"])

    @patch.dict(os.environ, {"AWS_DEFAULT_REGION": "eu-west-2"}, clear=True)
    @patch("boto3.client")
    def test_missing_instance_id(self, mock_boto_client):
        event = {}
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Missing 'instanceId'", response["body"])

    @patch.dict(os.environ, {"AWS_DEFAULT_REGION": "eu-west-2", "environment": "integration"})
    @patch("boto3.client")
    def test_boto3_raises_exception(self, mock_boto_client):
        mock_ec2 = MagicMock()
        mock_ec2.terminate_instances.side_effect = Exception("Instance not found")
        mock_boto_client.return_value = mock_ec2

        with self.assertRaises(Exception) as context:
            lambda_handler({"instanceId": "i-followerE"}, None)

        self.assertIn("Failed to terminate i-followerE", str(context.exception))
        self.assertIn("Instance not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()

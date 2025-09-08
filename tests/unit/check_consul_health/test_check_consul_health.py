import json
import os
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from src.check_consul_health.main import get_consul_host, lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch.dict(os.environ, {"environment": "integration"})
    @patch("urllib.request.urlopen")
    def test_cluster_healthy(self, mock_urlopen):
        # Mock response for /v1/status/leader
        mock_leader_response = MagicMock()
        mock_leader_response.read.return_value = b'"127.0.0.1:8300"'
        mock_leader_response.__enter__.return_value = mock_leader_response

        # Mock response for /v1/status/peers
        mock_peers_response = MagicMock()
        mock_peers_response.read.return_value = json.dumps(["a", "b", "c"]).encode("utf-8")
        mock_peers_response.__enter__.return_value = mock_peers_response

        mock_urlopen.side_effect = [mock_leader_response, mock_peers_response]

        event = {"expectedPeers": 3}
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Cluster healthy with leader", response["body"])

    @patch.dict(os.environ, {"environment": "production"})
    @patch("urllib.request.urlopen")
    def test_no_leader_found(self, mock_urlopen):
        mock_leader_response = MagicMock()
        mock_leader_response.read.return_value = b'""'
        mock_leader_response.__enter__.return_value = mock_leader_response
        mock_urlopen.side_effect = [mock_leader_response]

        with self.assertRaises(Exception) as context:
            lambda_handler({}, None)

        self.assertIn("No leader found", str(context.exception))

    @patch.dict(os.environ, {"environment": "staging"})
    @patch("urllib.request.urlopen")
    def test_incorrect_peer_count(self, mock_urlopen):
        mock_leader_response = MagicMock()
        mock_leader_response.read.return_value = b'"leader-host:8300"'
        mock_leader_response.__enter__.return_value = mock_leader_response

        mock_peers_response = MagicMock()
        mock_peers_response.read.return_value = json.dumps(["only-one"]).encode("utf-8")
        mock_peers_response.__enter__.return_value = mock_peers_response

        mock_urlopen.side_effect = [mock_leader_response, mock_peers_response]

        with self.assertRaises(Exception) as context:
            lambda_handler({"expectedPeers": 3}, None)

        self.assertIn("1 peers found", str(context.exception))

    @patch.dict(os.environ, {"environment": "test"})
    @patch("urllib.request.urlopen")
    def test_consul_returns_500(self, mock_urlopen):
        # Simulate a 500 Internal Server Error from Consul
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://consul-test.test.mdtp:8500/v1/status/leader",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=None,
        )

        with self.assertRaises(Exception) as context:
            lambda_handler({}, None)

        self.assertIn("Cluster health check failed", str(context.exception))
        self.assertIn("Internal Server Error", str(context.exception))

    @patch.dict(os.environ, {"environment": "integration"})
    def test_get_consul_host_defaults_to_environment(self):
        self.assertEqual(get_consul_host({}), "http://consul-integration.integration.mdtp:8500")

    @patch.dict(os.environ, {"environment": "integration"})
    def test_get_consul_host_includes_cluster(self):
        self.assertEqual(get_consul_host({"cluster": "dev-1"}), "http://consul-dev-1.integration.mdtp:8500")


if __name__ == "__main__":
    unittest.main()

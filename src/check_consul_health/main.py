import json
import logging
import os
import ssl
import tempfile
import urllib.request
from typing import Any, Optional

import boto3

logger = logging.getLogger(__name__)


class CaCertificate:
    """
    Manage CA certificate retrieval and caching.
    """

    def __init__(self, cert_parameter_arn: Optional[str] = None):
        self._cert_path: Optional[str] = None
        self.cert_parameter_arn = cert_parameter_arn

    @property
    def cert_path(self) -> Optional[str]:
        """Get the certificate file path, retrieving it if necessary."""
        if self._cert_path is None and self.cert_parameter_arn:
            self._retrieve_cert()
        return self._cert_path

    def _retrieve_cert(self) -> None:
        """Retrieve certificate from Parameter Store and write to temp file."""
        if not self.cert_parameter_arn:
            logger.info("No TLS certificate ARN configured")
            return

        try:
            logger.info(f"Retrieving CA certificate from parameter: {self.cert_parameter_arn}")
            ssm = boto3.client("ssm", region_name="eu-west-2")
            response = ssm.get_parameter(Name=self.cert_parameter_arn, WithDecryption=True)
            cert_content = response["Parameter"]["Value"]

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
                f.write(cert_content)
                self._cert_path = f.name

            logger.info(f"Successfully retrieved CA certificate and wrote to {self._cert_path}")

        except Exception:
            logger.exception("Failed to retrieve CA certificate")
            raise


ca_certificate = CaCertificate(os.environ.get("CONSUL_TLS_CERT_PARAMETER_ARN"))


# Normally we connect to consul-{environment}.{environment}.mdtp but we also support
# connection to other clusters (e.g. engineer environments)
def get_consul_host(event: Any) -> str:
    environment = os.environ.get("environment")
    if environment == "integration":
        print("Lambda Event Payload:")
        print(event)

    cluster = event.get("cluster", environment)
    return f"https://consul-{cluster}.{environment}.mdtp:8501"


def get_ssl_context() -> ssl.SSLContext:
    """Create SSL context with CA certificate if available."""
    ctx = ssl.create_default_context()
    if ca_certificate.cert_path:
        ctx.load_verify_locations(ca_certificate.cert_path)
    return ctx


def lambda_handler(event: Any, context: Any) -> Any:
    consul_host = get_consul_host(event)

    expected_peers = event.get("expectedPeers", 3)  # Default to 3 if not provided

    ssl_context = get_ssl_context()

    try:
        # Check for leader
        with urllib.request.urlopen(f"{consul_host}/v1/status/leader", context=ssl_context) as res:  # nosec
            leader = res.read().decode().strip().strip('"')
            if not leader:
                raise Exception("No leader found")

        # Check number of nodes in the cluster is as expected.
        with urllib.request.urlopen(f"{consul_host}/v1/status/peers", context=ssl_context) as res:  # nosec
            peers = json.loads(res.read().decode())
            if len(peers) != expected_peers:
                raise Exception(f"{len(peers)} peers found, expected {expected_peers}")

        return {
            "statusCode": 200,
            "body": f"Cluster healthy with leader {leader} and {len(peers)} peers",
        }

    except Exception as e:
        raise Exception(f"Cluster health check failed: {e}")

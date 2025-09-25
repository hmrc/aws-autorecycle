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
            logger.info('No TLS certificate ARN configured')
            return

        try:
            logger.info(f'Retrieving CA certificate from parameter: {self.cert_parameter_arn}')
            ssm = boto3.client('ssm', region_name='eu-west-2')
            response = ssm.get_parameter(Name=self.cert_parameter_arn, WithDecryption=True)
            cert_content = response['Parameter']['Value']

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                f.write(cert_content)
                self._cert_path = f.name

            logger.info(f'Successfully retrieved CA certificate and wrote to {self._cert_path}')

        except Exception:
            logger.exception('Failed to retrieve CA certificate')
            raise


ca_certificate = CaCertificate(os.environ.get('CONSUL_TLS_CERT_PARAMETER_ARN'))


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

    ec2 = boto3.client("ec2")

    ssl_context = get_ssl_context()

    try:
        # Get Consul leader IP
        with urllib.request.urlopen(f"{consul_host}/v1/status/leader", context=ssl_context) as res:  # nosec
            leader = res.read().decode().strip().strip('"').split(":")[0]

        # Get all members of the control plane
        with urllib.request.urlopen(f"{consul_host}/v1/agent/members", context=ssl_context) as res:  # nosec
            members = json.loads(res.read().decode())

        # Sort all the members, putting the leader last in the list
        sorted_members = sorted(members, key=lambda m: m["Addr"] == leader)

        ip_list = [m["Addr"] for m in sorted_members]

        # The consul API returns ip addresses. Onward processing needs instance IDs so look the instance id's up
        instance_map = {}
        if ip_list:
            response = ec2.describe_instances(Filters=[{"Name": "private-ip-address", "Values": ip_list}])

            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    for iface in instance.get("NetworkInterfaces", []):
                        ip = iface.get("PrivateIpAddress")
                        if ip in ip_list:
                            instance_map[ip] = instance["InstanceId"]

        return {"instanceList": [{"ip": ip, "instanceId": instance_map[ip]} for ip in ip_list if ip in instance_map]}

    except Exception as e:
        raise Exception(f"Get Consul Nodes Failed: {e}")

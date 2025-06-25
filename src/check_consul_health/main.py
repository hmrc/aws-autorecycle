import json
import os
import urllib.request
from typing import Any


def lambda_handler(event: Any, context: Any) -> Any:
    environment = os.environ.get("environment")
    if environment == "integration":
        print("🔍 Lambda Event Payload:")
        print(event)
    consul_host = f"http://consul-{environment}.{environment}.mdtp:8500"
    # consul_host = "https://consul-dp-infra-8594.integration.tax.service.gov.uk"
    expected_peers = event.get("expectedPeers", 3)  # Default to 3 if not provided

    try:
        # Check for leader
        with urllib.request.urlopen(f"{consul_host}/v1/status/leader") as res:  # nosec
            leader = res.read().decode().strip().strip('"')
            if not leader:
                raise Exception("No leader found")

        # Check peer count
        with urllib.request.urlopen(f"{consul_host}/v1/status/peers") as res:  # nosec
            peers = json.loads(res.read().decode())
            if len(peers) != expected_peers:
                raise Exception(f"Only {len(peers)} peers found, expected {expected_peers}")

        return {
            "statusCode": 200,
            "body": f"Cluster healthy with leader {leader} and {len(peers)} peers",
        }

    except Exception as e:
        raise Exception(f"Cluster health check failed: {e}")

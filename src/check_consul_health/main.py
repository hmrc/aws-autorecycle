import json
import os
import urllib.request
from typing import Any


# Normally we connect to consul-{environment}.{environment}.mdtp but we also support
# connection to other clusters (e.g. engineer environments)
def get_consul_host(event: Any) -> str:
    environment = os.environ.get("environment")
    if environment == "integration":
        print("Lambda Event Payload:")
        print(event)

    cluster = event.get("cluster", environment)
    return f"http://consul-{cluster}.{environment}.mdtp:8500"


def lambda_handler(event: Any, context: Any) -> Any:
    consul_host = get_consul_host(event)

    expected_peers = event.get("expectedPeers", 3)  # Default to 3 if not provided

    try:
        # Check for leader
        with urllib.request.urlopen(f"{consul_host}/v1/status/leader") as res:  # nosec
            leader = res.read().decode().strip().strip('"')
            if not leader:
                raise Exception("No leader found")

        # Check number of nodes in the cluster is as expected.
        with urllib.request.urlopen(f"{consul_host}/v1/status/peers") as res:  # nosec
            peers = json.loads(res.read().decode())
            if len(peers) != expected_peers:
                raise Exception(f" {len(peers)} peers found, expected {expected_peers}")

        return {
            "statusCode": 200,
            "body": f"Cluster healthy with leader {leader} and {len(peers)} peers",
        }

    except Exception as e:
        raise Exception(f"Cluster health check failed: {e}")

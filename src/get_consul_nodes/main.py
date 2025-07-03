import json
import os
import urllib.request
from typing import Any

import boto3


def lambda_handler(event: Any, context: Any) -> Any:
    environment = os.environ.get("environment")
    if environment == "integration":
        print("Lambda Event Payload:")
        print(event)
    consul_host = f"http://consul-{environment}.{environment}.mdtp:8500"
    ec2 = boto3.client("ec2")

    try:
        # Get Consul leader IP
        with urllib.request.urlopen(f"{consul_host}/v1/status/leader") as res:  # nosec
            leader = res.read().decode().strip().strip('"').split(":")[0]

        # Get all members of the control plane
        with urllib.request.urlopen(f"{consul_host}/v1/agent/members") as res:  # nosec
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

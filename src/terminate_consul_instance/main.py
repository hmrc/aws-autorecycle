import os
from typing import Any

import boto3


def lambda_handler(event: Any, context: Any) -> Any:
    ec2 = boto3.client("ec2")
    environment = os.environ.get("environment")
    if environment == "integration":
        print("Lambda Event Payload:")
        print(event)
    instance_id = event.get("instanceId")

    if not instance_id:
        return {"statusCode": 400, "body": "Missing 'instanceId' in input"}

    try:
        response = ec2.terminate_instances(InstanceIds=[instance_id])
        return {
            "statusCode": 200,
            "body": f"Termination initiated for {instance_id}",
            "response": response,
        }
    except Exception as e:
        raise Exception(f"Failed to terminate {instance_id}: {e}")

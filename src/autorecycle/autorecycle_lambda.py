import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

print("Loading function")

SQS_URL = "https://sqs.eu-west-2.amazonaws.com"


def output(component: str, success: bool, channel: str) -> Any:
    if success:
        outcome = "Auto-recycling was successfully initiated"
        status = "success"
    else:
        outcome = "Auto-recycling has failed"
        status = "failure"
        channel = "team-infra-alerts"

    message_content = {
        "text": outcome,
        "color": "good" if status == "success" else "danger",
        "fields": [
            {
                "title": "Component Name",
                "value": "recycle-{}".format(component),
                "short": True,
            },
            {"title": "Environment", "value": os.getenv("environment"), "short": True},
        ],
    }

    data = {
        "username": "AutoRecycling",
        "channels": channel,
        "emoji": ":robot_face:",
        "text": "*{}*".format(component),
        "status": status,
        "component": component,
        "message_content": message_content,
    }

    return data


def send_to_sqs(component: str, account_id: str, channel: str) -> Any:
    print("LOG: Sending component to be recycled metadata to SQS queue")
    sqs = boto3.client("sqs")

    sqs_queue = SQS_URL + "/{}/recycle-{}".format(account_id, component)

    print(sqs_queue)

    send_message = "Recycle {}".format(component)

    try:
        response = sqs.send_message(
            QueueUrl=sqs_queue,
            MessageAttributes={
                "component": {"DataType": "String", "StringValue": component},
                "account_id": {"DataType": "String", "StringValue": account_id},
            },
            MessageBody=(send_message),
        )
        print("response: {}".format(response))
        if "MessageId" in response:
            print(response["MessageId"])
            success = True
            return output(component, success, channel)
        else:
            print("ERROR: Invalid return code for SQS send, {}".format(response))
            success = False
            return output(component, success, channel)
    except ClientError as err:
        print("Client Error {}".format(err))
        success = False
        return output(component, success, channel)
    except Exception as ex:
        print("General exception {}".format(ex))
        success = False
        return output(component, success, channel)


def lambda_handler(event: Any, context: Any) -> Any:
    component = event["component"]
    account_id = event["account_id"]
    channel = event["success_channel"]

    return send_to_sqs(component, account_id, channel)

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient

boto3_session = boto3.Session(aws_access_key_id="abcd", aws_secret_access_key="defg", region_name="eu-west-2")  # nosec
lambda_client: LambdaClient = boto3_session.client("lambda", endpoint_url=f"http://lambda:8080")


def test_lambda_returns_200():
    result = lambda_client.invoke(FunctionName="function", Payload=json.dumps({}))
    assert result["StatusCode"] == 200

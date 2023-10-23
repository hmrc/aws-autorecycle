import json
import logging
from time import localtime, strftime
from typing import Any

from src.autorecycle_invoke_stepfunctions.aws import get_stepfunctions_client, sf_exceptions

logger = logging.getLogger(__name__)


def sf_start_execution(payload: Any) -> None:
    if "step_function_name" in payload:
        sf_arn: str = "arn:aws:states:eu-west-2:{}:stateMachine:{}".format(
            payload["account_id"], payload["step_function_name"]
        )
    else:
        sf_arn = "arn:aws:states:eu-west-2:{}:stateMachine:autorecycle".format(payload["account_id"])
    execution_name: str = "{}-{}".format(payload["component"], strftime("%Y%m%d%H%M%S", localtime()))

    try:
        response: Any = get_stepfunctions_client().start_execution(
            stateMachineArn=sf_arn, name=execution_name, input=json.dumps(payload)
        )
        logger.info("The step function was invoked and the response was %s", response)
    except sf_exceptions.ClientError as err:
        logger.info(err)

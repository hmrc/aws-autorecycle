from typing import Any

import aws_lambda_logging


def json_logger_config(event: Any, context: Any) -> None:
    aws_lambda_logging.setup(
        level="INFO",
        aws_request_id=context.aws_request_id,
        function=context.function_name,
        component="aws-autorecycle",
    )

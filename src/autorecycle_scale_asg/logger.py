import os

from aws_lambda_powertools.logging import Logger

logger = Logger(
    service="aws-autorecycle-scale-asg-lambda",
    level=os.environ.get("LOG_LEVEL", "DEBUG"),
)

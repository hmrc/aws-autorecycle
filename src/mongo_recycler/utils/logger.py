import aws_lambda_logging


def json_logger_config(event, context):
    aws_lambda_logging.setup(
        level="INFO",
        aws_request_id=context.aws_request_id,
        function=context.function_name,
        component="aws-autorecycle-mongo-lambda",
    )

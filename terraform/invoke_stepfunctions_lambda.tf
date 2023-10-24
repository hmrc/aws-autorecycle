data "aws_caller_identity" "current" {}

module "invoke_stepfunctions_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    "ENVIRONMENT"   = var.environment
    "ACCOUNT_ID"    = data.aws_caller_identity.current.account_id
    "SLACK_CHANNEL" = var.slack_channel
  }
  function_name                           = "autorecycle-invoke-stepfunctions"
  image_command                           = ["autorecycle_invoke_stepfunctions.handler.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
}

resource "aws_lambda_function_event_invoke_config" "invoke_stepfunctions_lambda" {
  function_name                = module.invoke_stepfunctions_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_invoke_stepfunctions_lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "autoscaling:DescribeTags",
      "autoscaling:DescribeAutoScalingGroups",
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "states:StartExecution",
    ]

    resources = [
      var.state_machine_id
    ]
  }
}

resource "aws_iam_role_policy" "aws_autorecycle_invoke_stepfunctions_lambda" {
  role   = module.invoke_stepfunctions_lambda.iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_invoke_stepfunctions_lambda_policy.json
}

# Cloudwatch
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.invoke_stepfunctions_lambda.lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_aws_autorecycle_invoke_stepfunctions_lambda.arn
  qualifier     = module.invoke_stepfunctions_lambda.lambda_alias_name
}

resource "aws_cloudwatch_event_rule" "trigger_aws_autorecycle_invoke_stepfunctions_lambda" {
  name        = "trigger_aws_autorecycle_invoke_stepfunctions_lambda"
  description = "aws_autorecycle_invoke_stepfunctions_lambda"

  event_pattern = <<PATTERN
{
  "source": [
    "aws.autoscaling"
  ],
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventSource": [
      "autoscaling.amazonaws.com"
    ],
    "eventName": [
      "CreateOrUpdateTags",
      "DeleteTags",
      "UpdateAutoScalingGroup"
    ]
  }
}
PATTERN

}

resource "aws_cloudwatch_event_target" "target_aws_autorecycle_invoke_stepfunctions_lambda" {
  target_id = "target_aws_autorecycle_invoke_stepfunctions_lambda"
  rule      = aws_cloudwatch_event_rule.trigger_aws_autorecycle_invoke_stepfunctions_lambda.name
  arn       = module.invoke_stepfunctions_lambda.lambda_alias_arn
}

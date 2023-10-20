data "aws_caller_identity" "current" {}

module "monitor_autorecycle_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
  }
  function_name                           = "monitor-autorecycle"
  image_command                           = ["monitor_autorecycle.main.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = "https://github.com/hmrc/aws-autorecycle"
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
}

resource "aws_lambda_function_event_invoke_config" "lambda_event_invoke_config" {
  function_name                = module.monitor_autorecycle_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "monitor_autorecycle_lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeScalingActivities",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "aws_autorecycle_invoke_stepfunctions_lambda" {
  role   = monitor_autorecycle_lambda.iam_role_id
  policy = data.aws_iam_policy_document.monitor_autorecycle_lambda_policy.json
}

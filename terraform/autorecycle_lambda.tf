module "autorecycle_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    environment = var.environment
  }
  enable_error_alarm                      = false
  error_alarm_runbook                     = local.lambda_error_runbook_url
  function_name                           = "autorecycle"
  image_command                           = ["autorecycle.autorecycle_lambda.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
}

resource "aws_lambda_function_event_invoke_config" "autorecycle_lambda" {
  function_name                = module.autorecycle_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_autorecycle_lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "sqs:SendMessage",
    ]

    resources = ["arn:aws:sqs:eu-west-2:${data.aws_caller_identity.current.account_id}:recycle-*"]
  }

}

resource "aws_iam_role_policy" "aws_autorecycle_autorecycle_lambda" {
  role   = module.autorecycle_lambda.iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_autorecycle_lambda_policy.json
}

module "autorecycle_delayer_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
      payments_sftp = var.payments_delayer_var
  }
  function_name                           = "autorecycle-delayer"
  image_command                           = ["autorecycle_delayer.aws_autorecycle_delayer_lambda.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
}

resource "aws_lambda_function_event_invoke_config" "autorecycle_delayer_lambda" {
  function_name                = module.autorecycle_delayer_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

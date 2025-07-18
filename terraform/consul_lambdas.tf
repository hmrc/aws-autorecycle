#############################     GetConsulNodes_lambda          #############################
module "GetConsulNodes_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    environment = var.environment
  }
  enable_error_alarm                      = true
  error_alarm_runbook                     = local.lambda_error_runbook_url
  error_alarm_actions                     = [data.aws_sns_topic.pagerduty_connector_noncritical.arn]
  function_name                           = "getConsulNodes"
  image_command                           = ["get_consul_nodes.main.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
  vpc_id                                  = var.autorecycle_mongo_lambda_vpc_id
  vpc_subnet_ids                          = var.autorecycle_mongo_lambda_subnet_ids
  security_group_ids                      = var.vpc_endpoint_sg
}

resource "aws_lambda_function_event_invoke_config" "GetConsulNodes_lambda" {
  function_name                = module.GetConsulNodes_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_GetConsulNodes_lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "sqs:SendMessage",
    ]

    resources = ["arn:aws:sqs:eu-west-2:${data.aws_caller_identity.current.account_id}:recycle-*"]
  }

}

resource "aws_iam_role_policy" "aws_autorecycle_GetConsulNodes_lambda" {
  role   = module.GetConsulNodes_lambda.iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_GetConsulNodes_lambda_policy.json
}



#############################     CheckClusterHealth          #############################

module "CheckClusterHealth_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    environment = var.environment
  }
  enable_error_alarm                      = true
  error_alarm_runbook                     = local.lambda_error_runbook_url
  error_alarm_actions                     = [data.aws_sns_topic.pagerduty_connector_noncritical.arn]
  function_name                           = "CheckConsulClusterHealth"
  image_command                           = ["check_consul_health.main.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
  vpc_id                                  = var.autorecycle_mongo_lambda_vpc_id
  vpc_subnet_ids                          = var.autorecycle_mongo_lambda_subnet_ids
}

resource "aws_lambda_function_event_invoke_config" "CheckClusterHealth_lambda" {
  function_name                = module.CheckClusterHealth_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_CheckClusterHealth_lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "sqs:SendMessage",
    ]

    resources = ["arn:aws:sqs:eu-west-2:${data.aws_caller_identity.current.account_id}:recycle-*"]
  }

}

resource "aws_iam_role_policy" "aws_autorecycle_CheckClusterHealth_lambda" {
  role   = module.CheckClusterHealth_lambda.iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_CheckClusterHealth_lambda_policy.json
}





#############################     TerminateConsulInstance          #############################

module "TerminateConsulInstance_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    environment = var.environment
  }
  enable_error_alarm                      = true
  error_alarm_runbook                     = local.lambda_error_runbook_url
  error_alarm_actions                     = [data.aws_sns_topic.pagerduty_connector_noncritical.arn]
  function_name                           = "TerminateConsulInstance"
  image_command                           = ["terminate_consul_instance.main.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
  vpc_id                                  = var.autorecycle_mongo_lambda_vpc_id
  vpc_subnet_ids                          = var.autorecycle_mongo_lambda_subnet_ids
  security_group_ids                      = var.vpc_endpoint_sg
}

resource "aws_lambda_function_event_invoke_config" "TerminateConsulInstance_lambda" {
  function_name                = module.TerminateConsulInstance_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_TerminateConsulInstance_lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "sqs:SendMessage",
    ]

    resources = ["arn:aws:sqs:eu-west-2:${data.aws_caller_identity.current.account_id}:recycle-*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "ec2:TerminateInstances"
    ]
    resources = ["*"]
    condition {
      test     = "StringLike"
      variable = "ec2:ResourceTag/consul-datacenter"
      values   = ["*"]
    }
  }
}

resource "aws_iam_role_policy" "aws_autorecycle_TerminateConsulInstance_lambda" {
  role   = module.TerminateConsulInstance_lambda.iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_TerminateConsulInstance_lambda_policy.json
}

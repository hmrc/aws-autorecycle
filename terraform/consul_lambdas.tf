#############################     GetConsulNodes_lambda          #############################
module "GetConsulNodes_lambda" {
  count  = local.enable_consul_lambdas ? 1 : 0
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    environment                   = var.environment
    CONSUL_TLS_CERT_PARAMETER_ARN = var.consul_ca_cert_arn
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
  count = local.enable_consul_lambdas ? 1 : 0

  function_name                = local.get_consul_nodes_lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_GetConsulNodes_lambda_policy" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = ["arn:aws:sqs:eu-west-2:${data.aws_caller_identity.current.account_id}:recycle-*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [var.consul_ca_cert_arn]
  }

  # Allow decryption of parameters encrypted with default SSM key
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt"
    ]
    resources = ["arn:aws:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:alias/aws/ssm"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.eu-west-2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "aws_autorecycle_GetConsulNodes_lambda" {
  count = local.enable_consul_lambdas ? 1 : 0

  role   = local.get_consul_nodes_iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_GetConsulNodes_lambda_policy.json
}


#############################     CheckClusterHealth          #############################
module "CheckClusterHealth_lambda" {
  count  = local.enable_consul_lambdas ? 1 : 0
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    environment                   = var.environment
    CONSUL_TLS_CERT_PARAMETER_ARN = var.consul_ca_cert_arn
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
  security_group_ids                      = var.vpc_endpoint_sg
}

resource "aws_lambda_function_event_invoke_config" "CheckClusterHealth_lambda" {
  count = local.enable_consul_lambdas ? 1 : 0

  function_name                = local.check_cluster_health_lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_CheckClusterHealth_lambda_policy" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = ["arn:aws:sqs:eu-west-2:${data.aws_caller_identity.current.account_id}:recycle-*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [var.consul_ca_cert_arn]
  }

  # Allow decryption of parameters encrypted with default SSM key
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt"
    ]
    resources = ["arn:aws:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:alias/aws/ssm"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.eu-west-2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "aws_autorecycle_CheckClusterHealth_lambda" {
  count = local.enable_consul_lambdas ? 1 : 0

  role   = local.check_cluster_health_iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_CheckClusterHealth_lambda_policy.json
}


#############################     TerminateConsulInstance          #############################
module "TerminateConsulInstance_lambda" {
  count  = local.enable_consul_lambdas ? 1 : 0
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
  count = local.enable_consul_lambdas ? 1 : 0

  function_name                = local.terminate_consul_lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "aws_autorecycle_TerminateConsulInstance_lambda_policy" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = ["arn:aws:sqs:eu-west-2:${data.aws_caller_identity.current.account_id}:recycle-*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["ec2:TerminateInstances"]
    resources = ["*"]
    condition {
      test     = "StringLike"
      variable = "ec2:ResourceTag/consul-datacenter"
      values   = ["*"]
    }
  }
}

resource "aws_iam_role_policy" "aws_autorecycle_TerminateConsulInstance_lambda" {
  count = local.enable_consul_lambdas ? 1 : 0

  role   = local.terminate_consul_iam_role_id
  policy = data.aws_iam_policy_document.aws_autorecycle_TerminateConsulInstance_lambda_policy.json
}

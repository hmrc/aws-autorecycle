module "autorecycle_mongo_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
    ENVIRONMENT = var.environment
    VAULT_URL   = "https://vault.${var.environment}.mdtp:8200"
    CA_CERT     = "mongo_recycler/mdtp.pem"
  }
  function_name                           = "aws-autorecycle-mongo-lambda"
  image_command                           = ["mongo_recycler.process.step.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 900
  vpc_id                                  = var.autorecycle_mongo_lambda_vpc_id
  vpc_subnet_ids                          = var.autorecycle_mongo_lambda_subnet_ids
}

resource "aws_lambda_function_event_invoke_config" "autorecycle_mongo_lambda" {
  function_name                = module.autorecycle_mongo_lambda.lambda_name
  maximum_event_age_in_seconds = 300
  maximum_retry_attempts       = 0
}

data "aws_iam_policy_document" "autorecycle_mongo_lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "ec2:Describe*",  #tfsec:ignore:aws-iam-no-policy-wildcards
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
    ]

    resources = ["*"]  #tfsec:ignore:aws-iam-no-policy-wildcards
  }
  statement {
    effect = "Allow"

    actions = [
      "autoscaling:Describe*",  #tfsec:ignore:aws-iam-no-policy-wildcards
    ]

    resources = ["*"]  #tfsec:ignore:aws-iam-no-policy-wildcards
  }

  statement {
    effect = "Allow"

    actions = [
      "ec2:TerminateInstances",
    ]

    resources = ["*"]  #tfsec:ignore:aws-iam-no-policy-wildcards

    condition {
      test     = "StringLike"
      variable = "ec2:ResourceTag/Name"

      values = [
        "*_mongo_*",
      ]
    }
  }
}

resource "aws_iam_role_policy" "autorecycle_mongo_lambda" {
  role   = module.autorecycle_mongo_lambda.iam_role_id
  policy = data.aws_iam_policy_document.autorecycle_mongo_lambda_policy.json
}

module "autorecycle_scale_asg_lambda" {
  source = "git::ssh://git@github.com/hmrc/infrastructure-pipeline-lambda-build//terraform/modules/aws-lambda-container?depth=1"

  account_engineering_boundary = var.account_engineering_boundary
  environment                  = var.environment
  environment_variables = {
  }
  function_name                           = "autorecycle-scale-asg"
  image_command                           = ["autorecycle_scale_asg.handler.lambda_handler"]
  image_uri                               = "419929493928.dkr.ecr.eu-west-2.amazonaws.com/aws-autorecycle:${var.image_tag}"
  lambda_git_repo                         = local.lambda_git_repo
  log_subscription_filter_destination_arn = var.log_subscription_filter_destination_arn
  memory_size                             = 128
  timeout                                 = 300
}

data "aws_iam_policy_document" "autorecycle_scale_asg" {
  statement {
    actions = [
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeScalingActivities",
      "autoscaling:ExecutePolicy",
    ]
    effect = "Allow"
    resources = ["*"]
  }
  statement {
    actions = [
      "ec2:DescribeInstanceStatus",
    ]
    effect = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "autorecycle_scale_asg" {
  policy = data.aws_iam_policy_document.autorecycle_scale_asg.json
  role   = module.autorecycle_scale_asg_lambda.iam_role_id
}

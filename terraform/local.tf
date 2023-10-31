locals {
  lambda_git_repo = "https://github.com/hmrc/aws-autorecycle"
}

data "aws_caller_identity" "current" {}

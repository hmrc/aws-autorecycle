locals {
  lambda_git_repo = "https://github.com/hmrc/aws-autorecycle"
  runbook_url     = "https://confluence.tools.tax.service.gov.uk/x/2YwJBg"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
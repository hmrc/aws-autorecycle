locals {
  lambda_git_repo                = "https://github.com/hmrc/aws-autorecycle"
  autorecycle_failed_runbook_url = "https://confluence.tools.tax.service.gov.uk/x/04P0Mg"
  lambda_error_runbook_url       = "https://confluence.tools.tax.service.gov.uk/x/_YD-Mg"
  # https://confluence.tools.tax.service.gov.uk/x/M4P0Mg"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
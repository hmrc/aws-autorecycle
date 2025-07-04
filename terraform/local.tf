locals {
  lambda_git_repo                = "https://github.com/hmrc/aws-autorecycle"
  autorecycle_failed_runbook_url = "https://confluence.tools.tax.service.gov.uk/x/04P0Mg"
  lambda_error_runbook_url       = "https://confluence.tools.tax.service.gov.uk/x/_YD-Mg"
  # https://confluence.tools.tax.service.gov.uk/x/M4P0Mg"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_sns_topic" "pagerduty_connector_noncritical" {
  name = "pagerduty_infrastructure_noncritical-${var.environment}"
}

data "terraform_remote_state" "networks" {
  backend = "s3"

  config = {
    bucket = "tfstate-${var.environment}-${md5(data.aws_caller_identity.current.account_id)}"
    region = data.aws_region.current.name
    key    = "networks.tfstate"
  }
}

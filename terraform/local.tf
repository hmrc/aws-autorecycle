locals {
  lambda_git_repo                       = "https://github.com/hmrc/aws-autorecycle"
  autorecycle_failed_runbook_url        = "https://confluence.tools.tax.service.gov.uk/x/04P0Mg"
  lambda_error_runbook_url              = "https://confluence.tools.tax.service.gov.uk/x/_YD-Mg"
  enable_consul_lambdas                 = var.environment != "management"
  get_consul_nodes_lambda_name          = local.enable_consul_lambdas ? module.GetConsulNodes_lambda[0].lambda_name : null
  get_consul_nodes_iam_role_id          = local.enable_consul_lambdas ? module.GetConsulNodes_lambda[0].iam_role_id : null
  check_cluster_health_lambda_name      = local.enable_consul_lambdas ? module.CheckClusterHealth_lambda[0].lambda_name : null
  check_cluster_health_iam_role_id      = local.enable_consul_lambdas ? module.CheckClusterHealth_lambda[0].iam_role_id : null
  terminate_consul_instance_lambda_name = local.enable_consul_lambdas ? module.TerminateConsulInstance_lambda[0].lambda_name : null
  terminate_consul_instance_iam_role_id = local.enable_consul_lambdas ? module.TerminateConsulInstance_lambda[0].iam_role_id : null
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_sns_topic" "pagerduty_connector_noncritical" {
  name = "pagerduty_infrastructure_noncritical-${var.environment}"
}

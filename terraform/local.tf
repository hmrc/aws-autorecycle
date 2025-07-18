locals {
  lambda_git_repo                = "https://github.com/hmrc/aws-autorecycle"
  autorecycle_failed_runbook_url = "https://confluence.tools.tax.service.gov.uk/x/04P0Mg"
  lambda_error_runbook_url       = "https://confluence.tools.tax.service.gov.uk/x/_YD-Mg"

  enable_consul_lambdas = var.environment != "management"

  # GetConsulNodes Lambda
  get_consul_nodes_lambda_name    = local.enable_consul_lambdas ? module.GetConsulNodes_lambda[0].lambda_name : null
  get_consul_nodes_iam_role_id    = local.enable_consul_lambdas ? module.GetConsulNodes_lambda[0].iam_role_id : null
  get_consul_nodes_lambda_arn     = local.enable_consul_lambdas ? module.GetConsulNodes_lambda[0].lambda_alias_arn : null
  get_consul_nodes_security_group = local.enable_consul_lambdas ? module.GetConsulNodes_lambda[0].security_group_id : null

  # CheckClusterHealth Lambda
  check_cluster_health_lambda_name    = local.enable_consul_lambdas ? module.CheckClusterHealth_lambda[0].lambda_name : null
  check_cluster_health_iam_role_id    = local.enable_consul_lambdas ? module.CheckClusterHealth_lambda[0].iam_role_id : null
  check_cluster_health_lambda_arn     = local.enable_consul_lambdas ? module.CheckClusterHealth_lambda[0].lambda_alias_arn : null
  check_cluster_health_security_group = local.enable_consul_lambdas ? module.CheckClusterHealth_lambda[0].security_group_id : null

  # TerminateConsulInstance Lambda
  terminate_consul_lambda_name    = local.enable_consul_lambdas ? module.TerminateConsulInstance_lambda[0].lambda_name : null
  terminate_consul_iam_role_id    = local.enable_consul_lambdas ? module.TerminateConsulInstance_lambda[0].iam_role_id : null
  terminate_consul_lambda_arn     = local.enable_consul_lambdas ? module.TerminateConsulInstance_lambda[0].lambda_alias_arn : null
  terminate_consul_security_group = local.enable_consul_lambdas ? module.TerminateConsulInstance_lambda[0].security_group_id : null
}




data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_sns_topic" "pagerduty_connector_noncritical" {
  name = "pagerduty_infrastructure_noncritical-${var.environment}"
}

# monitor_autorecycle_lambda
output "monitor_autorecycle_lambda_alias_name" {
  value = module.monitor_autorecycle_lambda.lambda_alias_name
}

output "monitor_autorecycle_lambda_arn" {
  value = module.monitor_autorecycle_lambda.lambda_alias_arn
}

output "monitor_autorecycle_lambda_name" {
  value = module.monitor_autorecycle_lambda.lambda_name
}

output "monitor_autorecycle_lambda_role_arn" {
  value = module.monitor_autorecycle_lambda.iam_role_arn
}

output "monitor_autorecycle_lambda_role" {
  value = module.monitor_autorecycle_lambda.iam_role_id
}

# invoke_stepfunctions_lambda
output "invoke_stepfunctions_lambda_alias_name" {
  value = module.invoke_stepfunctions_lambda.lambda_alias_name
}

output "invoke_stepfunctions_lambda_arn" {
  value = module.invoke_stepfunctions_lambda.lambda_alias_arn
}

output "invoke_stepfunctions_lambda_name" {
  value = module.invoke_stepfunctions_lambda.lambda_name
}

output "invoke_stepfunctions_lambda_role_arn" {
  value = module.invoke_stepfunctions_lambda.iam_role_arn
}

output "invoke_stepfunctions_lambda_role" {
  value = module.invoke_stepfunctions_lambda.iam_role_id
}

# autorecycle_scale_asg_lambda
output "autorecycle_scale_asg_lambda_alias_name" {
  value = module.autorecycle_scale_asg_lambda.lambda_alias_name
}

output "autorecycle_scale_asg_lambda_arn" {
  value = module.autorecycle_scale_asg_lambda.lambda_alias_arn
}

output "autorecycle_scale_asg_lambda_name" {
  value = module.autorecycle_scale_asg_lambda.lambda_name
}

output "autorecycle_scale_asg_lambda_role_arn" {
  value = module.autorecycle_scale_asg_lambda.iam_role_arn
}

output "autorecycle_scale_asg_lambda_role" {
  value = module.autorecycle_scale_asg_lambda.iam_role_id
}

#autorecycle_mongo_lambda
output "autorecycle_mongo_lambda_alias_name" {
  value = var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].lambda_alias_name : null
}

output "autorecycle_mongo_lambda_arn" {
  value = var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].lambda_alias_arn : null
}

output "autorecycle_mongo_lambda_name" {
  value = var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].lambda_name : null
}

output "autorecycle_mongo_lambda_role_arn" {
  value = var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].iam_role_arn : null
}

output "autorecycle_mongo_lambda_role" {
  value = var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].iam_role_id : null
}

output "autorecycle_mongo_lambda_security_group" {
  value = var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].security_group_id : null
}
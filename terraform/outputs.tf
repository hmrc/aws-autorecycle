# monitor_autorecycle
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
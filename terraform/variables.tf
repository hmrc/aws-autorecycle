variable "account_engineering_boundary" {
  type = string
}

variable "environment" {
  description = "Name of the environment the lambda function is deployed to"
  type        = string
}

variable "image_tag" {
  description = "The image tag to deploy"
  type        = string
}

variable "log_subscription_filter_destination_arn" {
  description = "The Kibana log subscription destination ARN"
  type        = string
}

variable "slack_channel" {
  description = "Slack channel to post to"
  type        = string
}

variable "slack_error_channel" {
  description = "Slack channel to post errors to"
  type        = string
}

variable "autorecycle_mongo_lambda_vpc_id" {
  description = "The VPC to run the autorecycle_mongo_lambda in"
  type        = string
  default     = null
}

variable "autorecycle_mongo_lambda_subnet_ids" {
  description = "The subnets to run the autorecycle_mongo_lambda in"
  type        = list(string)
  default     = null
}

variable "slack_notifications_lambda" {
  description = "The ARN of the Slack notifications Lambda"
  type        = string
}

variable "get_instance_refresh_status_lambda_arn" {
  description = "The ARN of the get_instance_refresh_status lambda (We should migrate this lambda into this repo)"
  type        = string
  default     = null
}

variable "get_instance_refresh_status_lambda_name" {
  description = "The name of the get_instance_refresh_status lambda (We should migrate this lambda into this repo)"
  type        = string
  default     = ""
}

variable "cancel_instance_refresh_lambda_arn" {
  description = "The ARN of the cancel_instance_refresh lambda (We should migrate this lambda into this repo)"
  type        = string
  default     = null
}

variable "cancel_instance_refresh_lambda_name" {
  description = "The name of the cancel_instance_refresh lambda (We should migrate this lambda into this repo)"
  type        = string
  default     = ""
}

variable "start_instance_refresh_lambda_arn" {
  description = "The ARN of the start_instance_refresh lambda (We should migrate this lambda into this repo)"
  type        = string
  default     = null
}

variable "start_instance_refresh_lambda_name" {
  description = "The name of the start_instance_refresh lambda (We should migrate this lambda into this repo)"
  type        = string
  default     = ""
}

variable "vpc_endpoint_sg" {
  description = "VPC Endpoint Security Group"
  type        = list(string)
}

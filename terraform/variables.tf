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

variable "state_machine_id" {
  description = "ID of the state machine the lambda will start"
  type        = string
}

variable "slack_channel" {
  description = "Slack channel to post to"
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

variable "payments_delayer_var" {
  default = "09:45:00, 11:15:00, 11:30:00"
}
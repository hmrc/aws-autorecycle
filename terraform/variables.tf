variable "account_engineering_boundary" {
  type = string
}

variable "component" {
  description = "The name of the component"
  type        = string
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

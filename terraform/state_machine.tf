resource "aws_sfn_state_machine" "auto_recycle" {
  name     = "autorecycle"
  role_arn = aws_iam_role.step_machine.arn

  definition = <<EOF
{
  "StartAt": "Choose Recycle Strategy",
  "States": {
    "Standard Recycle": {
      "Comment": "Invokes the basic recycling method (add to SQS queue)",
      "Type": "Task",
      "Resource": "${module.autorecycle_lambda.lambda_alias_arn}",
      "OutputPath": "$",
      "ResultPath": "$",
      "Next": "Slack Message - start",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "ResultPath": "$.error-info",
        "Next": "Lambda Error"
      } ]
    },
    "Recycle single instance ASG": {
      "Comment": "Invokes the complex recycling method to trigger the scale asg lambda",
      "Type": "Task",
      "Resource": "${module.autorecycle_scale_asg_lambda.lambda_alias_arn}",
      "OutputPath": "$",
      "ResultPath": "$",
      "Next": "Is first run?",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "ResultPath": "$.error-info",
        "Next": "Lambda Error"
      } ]
    },
    "Is first run?": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.counter",
          "NumericLessThanEquals": 1,
          "Next": "Slack message - single instance ASG"
        }
      ],
      "Default": "Wait for single instance ASG autorecycle"
    },
    "Slack message - single instance ASG": {
      "Comment": "Send message in slack",
      "Type": "Task",
      "Resource": "${var.slack_notifications_lambda}",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Next": "Wait for single instance ASG autorecycle",
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "Next": "Wait for single instance ASG autorecycle",
        "ResultPath": "$.error-info"
      } ]
    },
    "Wait for single instance ASG autorecycle": {
      "Comment": "Waits for recycle to happen",
      "Type": "Wait",
      "Seconds": 60,
      "Next": "Is Autorecycling single instance ASG Done?"
    },
    "Is Autorecycling single instance ASG Done?": {
      "Comment": "Evaluates if all instances are recycled",
      "Type": "Choice",
      "InputPath": "$",
      "OutputPath": "$",
      "Choices": [
        {
          "Variable": "$.recycle_success",
          "BooleanEquals": true,
          "Next": "Slack Message - end"
        },
        {
          "Variable": "$.counter",
          "NumericGreaterThan": 20,
          "Next": "Slack Message - end"
        }
      ],
      "Default": "Recycle single instance ASG"
    },
    "Choose Recycle Strategy": {
      "Comment": "Chooses the recycle strategy based on the event strategy field",
      "Type": "Choice",
      "InputPath": "$",
      "OutputPath": "$",
      "Choices": [
        {
          "Variable": "$.strategy",
          "StringEquals": "in-out",
          "Next": "Recycle single instance ASG"
        },
        {
          "Variable": "$.strategy",
          "StringEquals": "mongo",
          "Next": "Mongo Recycle"
        },
        {
          "Variable": "$.strategy",
          "StringEquals": "instance-refresh",
          "Next": "Monitor Instance Refresh Status"
        }
      ],
      "Default": "Standard Recycle"
    },
    "Slack Message - start": {
      "Comment": "Send message in slack",
      "Type": "Task",
      "Resource": "${var.slack_notifications_lambda}",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Next": "Wait for commencement",
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "Next": "Wait for commencement",
        "ResultPath": "$.error-info"
      } ]
    },
    "Wait for autorecycle": {
      "Comment": "Waits for recycle to happen",
      "Type": "Wait",
      "Seconds": 360,
      "Next": "Monitor autorecycling"
    },
    "Wait for commencement": {
      "Comment": "Waits for recycle to commence",
      "Type": "Wait",
      "Seconds": 120,
      "Next": "Monitor autorecycling"
    },
    "Wait for instance refresh": {
      "Comment": "Waits for instance refresh to complete",
      "Type": "Wait",
      "Seconds": 180,
      "Next": "Monitor Instance Refresh Progress"
    },
    "Monitor autorecycling": {
      "Comment": "Checks whether the autorecycling had happen",
      "Type": "Task",
      "Resource": "${module.monitor_autorecycle_lambda.lambda_alias_arn}",
      "ResultPath": "$",
      "OutputPath": "$",
      "Next": "Is Autorecycling Done?",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "ResultPath": "$.error-info",
        "Next": "Lambda Error"
      } ]
    },
    "Is Autorecycling Done?": {
      "Comment": "Evaluates if all instances are recycled",
      "Type": "Choice",
      "InputPath": "$",
      "OutputPath": "$",
      "Choices": [
        {
          "Variable": "$.recycle_success",
          "BooleanEquals": true,
          "Next": "Slack Message - end"
        },
        {
          "Variable": "$.counter",
          "NumericGreaterThan": 20,
          "Next": "Slack Message - end"
        }
      ],
      "Default": "Wait for autorecycle"
    },
    "Mongo Recycle": {
      "Comment": "Set up arguments for Mongo recycle slack message",
      "Type": "Pass",
      "Next": "Slack message - Mongo",
      "Parameters": {
        "username": "AutoRecycling",
        "status": "success",
        "text.$": "$.component",
        "component.$": "$.component",
        "channels": [
          "${var.slack_channel}"
        ],
        "message_content": {
          "color": "good",
          "text": "Auto-recycling was successfully initiated",
          "fields": [
            {
              "short": true,
              "value.$": "$.component",
              "title": "Component Name"
            },
            {
                "title": "Environment",
                "value": "${var.environment}",
                "short": true
            }
          ]
        },
        "emoji": ":robot_face:"
       }
    },
    "Slack message - Mongo": {
      "Comment": "Send message in slack",
      "Type": "Task",
      "Resource": "${var.slack_notifications_lambda}",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Next": "Recycle Mongo Cluster",
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "Next": "Recycle Mongo Cluster",
        "ResultPath": "$.error-info"
      } ]
    },
    "Wait for Mongo autorecycle": {
      "Comment": "Waits for Mongo recycle to happen",
      "Type": "Wait",
      "Seconds": 60,
      "Next": "Recycle Mongo Cluster"
    },
    "Mongo autorecycle decision": {
      "Comment": "Decide which step to execute next",
      "Type": "Choice",
      "InputPath": "$",
      "OutputPath": "$",
      "Choices": [
        {
          "Variable": "$.decision.action",
          "StringEquals": "STEP_DOWN_AND_RECYCLE_PRIMARY",
          "Next": "Wait for Mongo autorecycle"
        },
        {
          "Variable": "$.decision.action",
          "StringEquals": "RECYCLE_SECONDARY",
          "Next": "Wait for Mongo autorecycle"
        },
        {
          "Variable": "$.decision.action",
          "StringEquals": "DONE",
          "Next": "Slack Message - end"
        }
      ],
      "Default": "Recycle Mongo Cluster"
    },
    "Recycle Mongo Cluster": {
      "Comment": "Recycles the given Mongo Cluster",
      "Type": "Task",
      "Resource": "${var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].lambda_alias_arn : aws_lambda_function.dummy_lambda.arn}",
      "OutputPath": "$",
      "ResultPath": "$",
      "TimeoutSeconds": 900,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Next": "Mongo autorecycle decision",
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "ResultPath": "$.error-info",
        "Next": "Lambda Error"
      } ]
    },
    "Instance Refresh": {
      "Comment": "Set up arguments for instance refresh slack message",
      "Type": "Pass",
      "Next": "Slack message - Instance Refresh",
      "Parameters": {
        "username": "AutoRecycling",
        "status": "success",
        "text.$": "$.component",
        "component.$": "$.component",
        "channels": [
          "${var.slack_channel}"
        ],
        "message_content": {
          "color": "good",
          "text": "Instance refresh was successfully initiated",
          "fields": [
            {
              "short": true,
              "value.$": "$.component",
              "title": "Component Name"
            },
            {
                "title": "Environment",
                "value": "${var.environment}",
                "short": true
            }
          ]
        },
        "emoji": ":robot_face:"
       }
    },
    "Slack message - Instance Refresh": {
      "Comment": "Send message in slack",
      "Type": "Task",
      "Resource": "${var.slack_notifications_lambda}",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Next": "Instance Refresh Start",
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "Next": "Instance Refresh Start",
        "ResultPath": "$.error-info"
      } ]
    },
    "Instance Refresh Start": {
      "Comment": "Invokes the start instance refresh method to trigger asg update",
      "Type": "Task",
      "Resource": "${var.start_instance_refresh_lambda_arn != null ? var.start_instance_refresh_lambda_arn : aws_lambda_function.dummy_lambda.arn}",
      "OutputPath": "$",
      "ResultPath": "$.${var.start_instance_refresh_lambda_name}-output",
      "Next": "Was a refresh started?",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "ResultPath": "$.error-info",
        "Next": "Lambda Error"
      } ]
    },
    "Was a refresh started?": {
      "Comment": "Evaluates if the asg refresh was started",
      "Type": "Choice",
      "InputPath": "$",
      "OutputPath": "$",
      "Choices": [
        {
          "Variable": "$.${var.start_instance_refresh_lambda_name}-output.instance_refresh_id",
          "IsPresent": false,
          "Next": "Success"
        }
      ],
      "Default": "Monitor Instance Refresh Progress"
    },
    "Instance Refresh Cancel": {
      "Comment": "Invokes the cancel instance refresh method to trigger asg update",
      "Type": "Task",
      "Resource": "${var.cancel_instance_refresh_lambda_arn != null ? var.cancel_instance_refresh_lambda_arn : aws_lambda_function.dummy_lambda.arn}",
      "InputPath": "$.${var.get_instance_refresh_status_lambda_name}-output",
      "OutputPath": "$",
      "ResultPath": "$.${var.cancel_instance_refresh_lambda_name}-output",
      "Next": "Wait for instance refresh status",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "ResultPath": "$.error-info",
        "Next": "Lambda Error"
      } ]
    },
    "Monitor Instance Refresh Progress": {
      "Comment": "Checks whether the instance refresh has completed",
      "Type": "Task",
      "Resource": "${var.get_instance_refresh_status_lambda_arn != null ? var.get_instance_refresh_status_lambda_arn : aws_lambda_function.dummy_lambda.arn}",
      "InputPath": "$.${var.start_instance_refresh_lambda_name}-output",
      "OutputPath": "$",
      "ResultPath": "$.${var.get_instance_refresh_status_lambda_name}-output",
      "Next": "Is Instance Refresh Complete?",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "Next": "Lambda Error"
      } ]
    },
    "Monitor Instance Refresh Status": {
      "Comment": "Checks whether the instance refresh running",
      "Type": "Task",
      "Resource": "${var.get_instance_refresh_status_lambda_arn != null ? var.get_instance_refresh_status_lambda_arn : aws_lambda_function.dummy_lambda.arn}",
      "InputPath": "$",
      "OutputPath": "$",
      "ResultPath": "$.${var.get_instance_refresh_status_lambda_name}-output",
      "Next": "Instance Refresh Status?",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Retry": [ {
         "ErrorEquals": [ "Lambda.ServiceException", "Lambda.SdkClientException" ],
         "IntervalSeconds": 1,
         "MaxAttempts": 8,
         "BackoffRate": 2
      } ],
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "ResultPath": "$.error-info",
        "Next": "Lambda Error"
      } ]
    },
    "Instance Refresh Status?": {
      "Comment": "Evaluates if the asg has completed its instance refresh",
      "Type": "Choice",
      "InputPath": "$",
      "OutputPath": "$",
      "Choices": [
        {
          "And": [
            {
              "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
              "IsPresent": false
            },
            {
              "Variable": "$.instance_refresh_status_state.instance_refresh_checked",
              "IsPresent": false
            }
          ],
          "Next": "Instance Refresh"
        },
        {
          "And": [
            {
              "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
              "IsPresent": false
            },
            {
              "Variable": "$.instance_refresh_status_state.instance_refresh_checked",
              "IsPresent": true
            }
          ],
          "Next": "Instance Refresh Start"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "Pending",
          "Next": "Instance Refresh Cancel"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "InProgress",
          "Next": "Instance Refresh Cancel"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "Cancelling",
          "Next": "Wait for instance refresh status"
        }
      ],
      "Default": "Instance Refresh"
    },
    "Wait for instance refresh status": {
      "Comment": "Waits for instance refresh to complete",
      "Type": "Wait",
      "Seconds": 180,
      "Next": "Record Instance Refresh Status State"
    },
    "Record Instance Refresh Status State": {
      "Comment": "Records when an instance refresh status check found a running refresh",
      "Type": "Pass",
      "Result": {
        "instance_refresh_checked": true
      },
      "ResultPath": "$.instance_refresh_status_state",
      "OutputPath": "$",
      "Next": "Monitor Instance Refresh Status"
    },
    "Is Instance Refresh Complete?": {
      "Comment": "Evaluates if the asg has completed its instance refresh",
      "Type": "Choice",
      "InputPath": "$",
      "OutputPath": "$",
      "Choices": [
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "Pending",
          "Next": "Wait for instance refresh"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "In Progress",
          "Next": "Wait for instance refresh"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "Successful",
          "Next": "Successful Instance Refresh"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "Failed",
          "Next": "Failed Instance Refresh"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "Cancelling",
          "Next": "Wait for instance refresh"
        },
        {
          "Variable": "$.${var.get_instance_refresh_status_lambda_name}-output.Status",
          "StringEquals": "Cancelled",
          "Next": "Success"
        }
      ],
      "Default": "Wait for instance refresh"
    },
    "Successful Instance Refresh": {
      "Comment": "Set up arguments for instance refresh end slack message",
      "Type": "Pass",
      "Next": "Slack Message - end",
      "Parameters": {
        "username": "AutoRecycling",
        "status": "success",
        "text.$": "$.component",
        "component.$": "$.component",
        "channels": [
          "${var.slack_channel}"
        ],
        "message_content": {
          "color": "good",
          "text": "Instance refresh was successfully completed",
          "fields": [
            {
              "short": true,
              "value.$": "$.component",
              "title": "Component Name"
            },
            {
                "title": "Environment",
                "value": "${var.environment}",
                "short": true
            }
          ]
        },
        "emoji": ":robot_face:"
       }
    },
    "Failed Instance Refresh": {
      "Comment": "Set up arguments for instance refresh end slack message",
      "Type": "Pass",
      "Next": "Slack Message - end",
      "Parameters": {
        "username": "AutoRecycling",
        "status": "failed",
        "text.$": "$.component",
        "component.$": "$.component",
        "channels": [
          "${var.slack_channel}",
          "${var.slack_error_channel}"
        ],
        "message_content": {
          "color": "danger",
          "text": "Instance refresh FAILED to completed",
          "fields": [
            {
              "short": true,
              "value.$": "$.component",
              "title": "Component Name"
            },
            {
                "title": "Environment",
                "value": "${var.environment}",
                "short": true
            }
          ]
        },
        "emoji": ":robot_face:"
       }
    },
    "Slack Message - end": {
      "Comment": "Send message in slack",
      "Type": "Task",
      "Resource": "${var.slack_notifications_lambda}",
      "TimeoutSeconds": 300,
      "HeartbeatSeconds": 60,
      "Next": "Status",
      "Catch": [ {
        "ErrorEquals": [ "States.ALL" ],
        "Next": "Status",
        "ResultPath": "$.error-info"
      } ]
    },
    "Lambda Error": {
      "Comment": "Catches unhandled messages and sends a Slack message",
      "Type": "Pass",
      "Parameters": {
        "username": "AutoRecycling",
        "channels": "team-infra-alerts",
        "component.$": "$.component",
        "status": "fail",
        "message_content": {
          "text": "Failed to recycle a component: ${local.runbook_url}",
          "color": "danger",
          "fields": [
            {
              "short": true,
              "value.$": "$.component",
              "title": "Component Name"
            },
            {
                "title": "Environment",
                "value": "${var.environment}",
                "short": true
            }
          ]
        },
        "text": "State execution has failed in ${var.environment} because of a lambda exception! Please investigate.",
        "emoji": ":robot_face:"
      },
      "ResultPath": "$",
      "OutputPath": "$",
      "Next": "Slack Message - end"
    },
    "Status": {
      "Comment": "Determines whether the execution has completed successfully",
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.status",
          "StringEquals": "fail",
          "Next": "Fail"
        }
      ],
      "Default": "Success"
    },
    "Fail": {
      "Type": "Fail",
      "Cause": "Execution failed",
      "Error": "Fail"
    },
    "Success": {
      "Type": "Succeed"
    }
  }
}

EOF

}

resource "aws_iam_role" "step_machine" {
  name_prefix = "autorecycle-step-"

  permissions_boundary = var.account_engineering_boundary

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "states.${data.aws_region.current.name}.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "allow_step_function_to_invoke_lambdas" {
  statement {
    actions = [
      "lambda:InvokeFunction"
    ]
    effect = "Allow"
    resources = compact([
      var.start_instance_refresh_lambda_arn,
      var.cancel_instance_refresh_lambda_arn,
      var.get_instance_refresh_status_lambda_arn,
      var.slack_notifications_lambda,
      module.autorecycle_lambda.lambda_alias_arn,
      var.autorecycle_mongo_lambda_vpc_id != null ? module.autorecycle_mongo_lambda[0].lambda_alias_arn : null,
      module.monitor_autorecycle_lambda.lambda_alias_arn,
      module.autorecycle_scale_asg_lambda.lambda_alias_arn
    ])
  }
}

resource "aws_iam_role_policy" "allow_step_function_to_invoke_lambdas" {
  policy = data.aws_iam_policy_document.allow_step_function_to_invoke_lambdas.json
  role   = aws_iam_role.step_machine.name
}

resource "aws_cloudwatch_metric_alarm" "autorecyle_cloudwatch_alarm" {
  alarm_name        = "monitor-${aws_sfn_state_machine.auto_recycle.name}"
  alarm_description = "Step function failure. ${aws_sfn_state_machine.auto_recycle.name} in environment ${var.environment}"

  namespace           = "AWS/States"
  metric_name         = "ExecutionsFailed"
  comparison_operator = "GreaterThanThreshold"
  threshold           = "0"
  evaluation_periods  = "1"
  datapoints_to_alarm = "1"
  period              = "60"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.auto_recycle.id
  }

  treat_missing_data = "ignore"
  statistic          = "Maximum"
}


# Dummy lambda to cover for the missing lambdas in management
data "archive_file" "dummy_lambda" {
  type        = "zip"
  output_path = "lambda_function_payload.zip"

  source {
    content  = "dummy"
    filename = "dummy.py"
  }
}

resource "aws_lambda_function" "dummy_lambda" {
  filename      = "lambda_function_payload.zip"
  function_name = "autorecycle_dummy_lambda"
  role          = module.autorecycle_lambda.iam_role_arn
  handler       = "dummy"
  runtime       = "python3.10"

  source_code_hash = data.archive_file.dummy_lambda.output_base64sha256
}
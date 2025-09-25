resource "aws_sfn_state_machine" "recycle_consul_agents" {
  count    = local.enable_consul_lambdas ? 1 : 0
  name     = "recycle_consul_agents"
  role_arn = aws_iam_role.consul_step_machine.arn

  definition = <<-EOF
{
  "StartAt": "MainFlow",
  "States": {
    "MainFlow": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "StartNotification",
          "States": {
            "StartNotification": {
              "Type": "Task",
              "Comment": "Send Slack notification that auto-recycling of the Consul Control plane has started",
              "Resource": "${var.slack_notifications_lambda}",
              "Parameters": {
                "text": "Auto-recycling was successfully initiated",
                "channels": ["${var.slack_channel}"],
                "color": "good",
                "message_content": {
                  "color": "good",
                  "text.$": "States.Format('Auto-recycling of the Consul Control Plane {} was successfully initiated', $$.Execution.Input.cluster)"
                },
                "username": "AutoRecycling"
              },
              "Next": "CheckClusterHealthInitial"
            },
            "CheckClusterHealthInitial": {
              "Type": "Task",
              "Comment": "Check that consul is healthy before we start. 1 leader and 2 followers totalling 3 members",
              "Resource": "${local.check_cluster_health_lambda_arn}",
              "Parameters": {
                "cluster.$": "$$.Execution.Input.cluster"
              },
              "ResultPath": "$.initialHealth",
              "Retry": [{
                "ErrorEquals": ["States.ALL"],
                "IntervalSeconds": 120,
                "MaxAttempts": 4,
                "BackoffRate": 2.0
              }],
              "Next": "GetConsulNodes"
            },
            "GetConsulNodes": {
              "Type": "Task",
              "Comment": "Gets the IP and instance ID for each consul agent. Returns a sorted array with the leader last",
              "Resource": "${local.get_consul_nodes_lambda_arn}",
              "Parameters": {
                "cluster.$": "$$.Execution.Input.cluster"
              },
              "ResultPath": "$.nodes",
              "Next": "ForEachInstance"
            },
            "ForEachInstance": {
              "Type": "Map",
              "Comment": "Process each node one at a time in the order determined by GetConsulNodes. So leader last",
              "ItemsPath": "$.nodes.instanceList",
              "MaxConcurrency": 1,
              "Parameters": {
                "ip.$": "$$.Map.Item.Value.ip",
                "instanceId.$": "$$.Map.Item.Value.instanceId"
              },
              "Iterator": {
                "StartAt": "GracefulLeave",
                "States": {
                  "GracefulLeave": {
                    "Type": "Task",
                    "Comment": "Connect to each instance via SSM and issue the consul leave command",
                    "Resource": "arn:aws:states:::aws-sdk:ssm:sendCommand",
                    "Parameters": {
                      "DocumentName": "AWS-RunShellScript",
                      "InstanceIds.$": "States.Array($.instanceId)",
                      "Parameters": {
                        "commands": [
                          "echo 'Checking Consul leader status...'",
                          "curl -s https://localhost:8501/v1/status/leader || echo 'Consul not responding, not running or leaderless'",
                          "echo 'Attempting graceful leave...'",
                          "curl -X PUT https://localhost:8501/v1/agent/leave || echo 'Leave command failed'"
                        ]
                      }
                    },
                    "ResultPath": "$.gracefulLeaveResult",
                    "Next": "WaitBeforeHealthCheck"
                  },
                  "WaitBeforeHealthCheck": {
                    "Type": "Wait",
                    "Seconds": 120,
                    "Next": "CheckClusterHealthPostLeave"
                  },
                  "CheckClusterHealthPostLeave": {
                    "Type": "Task",
                    "Resource": "${local.check_cluster_health_lambda_arn}",
                    "ResultPath": "$.healthCheck",
                    "Parameters": {
                      "cluster.$": "$$.Execution.Input.cluster",
                      "expectedPeers": 2
                    },
                    "Retry": [{
                      "ErrorEquals": ["States.ALL"],
                      "IntervalSeconds": 120,
                      "MaxAttempts": 4,
                      "BackoffRate": 2.0
                    }],
                    "Next": "TerminateNode"
                  },
                  "TerminateNode": {
                    "Type": "Task",
                    "Resource": "${local.terminate_consul_lambda_arn}",
                    "Parameters": {
                      "instanceId.$": "$.instanceId"
                    },
                    "ResultPath": "$.terminateResult",
                    "Next": "WaitBeforeFinalHealthCheck"
                  },
                  "WaitBeforeFinalHealthCheck": {
                    "Type": "Wait",
                    "Seconds": 300,
                    "Next": "CheckClusterHealthFinal"
                  },
                  "CheckClusterHealthFinal": {
                    "Type": "Task",
                    "Resource": "${local.check_cluster_health_lambda_arn}",
                    "Parameters": {
                      "cluster.$": "$$.Execution.Input.cluster"
                    },
                    "ResultPath": "$.postTerminationHealth",
                    "Retry": [{
                      "ErrorEquals": ["States.ALL"],
                      "IntervalSeconds": 180,
                      "MaxAttempts": 6,
                      "BackoffRate": 2.0
                    }],
                    "End": true
                  }
                }
              },
              "Next": "EndNotification"
            },
            "EndNotification": {
              "Type": "Task",
              "Resource": "${var.slack_notifications_lambda}",
              "Parameters": {
                "text": "Auto-recycling the consul cluster has completed",
                "channels": ["${var.slack_channel}"],
                "color": "good",
                "message_content": {
                  "color": "good",
                  "text.$": "States.Format('Auto-recycling of the Consul Control Plane {} was successfully completed', $$.Execution.Input.cluster)"
                },
                "username": "AutoRecycling"
              },
              "End": true
            }
          }
        }
      ],
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "FailureNotification"
      }],
      "End": true
    },
    "FailureNotification": {
      "Type": "Task",
      "Resource": "${var.slack_notifications_lambda}",
      "Parameters": {
        "text.$": "States.Format('Auto-recycling of the Consul Control Plane {} failed', $$.Execution.Input.cluster)",
        "channels": [
          "${var.slack_error_channel}"
        ],
        "color": "danger",
        "message_content": {
          "color": "danger",
          "text": "Auto-recycling of the Consul Control Plane encountered an error and was aborted"
        },
        "username": "AutoRecycling"
      },
      "Next": "FailState"
    },
    "FailState": {
      "Type": "Fail",
      "Error": "AutoRecyclingFailed",
      "Cause": "Error encountered during Consul Recycle"
    }
  }
}
EOF
}


resource "aws_iam_role" "consul_step_machine" {
  name_prefix = "autorecycle-consul-step-"

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

data "aws_iam_policy_document" "allow_consul_step_function_to_invoke_lambdas" {
  statement {
    actions = ["lambda:InvokeFunction"]
    effect  = "Allow"
    resources = compact([
      var.slack_notifications_lambda,
      local.get_consul_nodes_lambda_arn,
      local.check_cluster_health_lambda_arn,
      local.terminate_consul_lambda_arn
    ])
  }

  statement {
    actions = ["ssm:SendCommand"]
    effect  = "Allow"
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}::document/AWS-RunShellScript",
      "arn:aws:ec2:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:instance/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:managed-instance/*"
    ]
  }
}

resource "aws_iam_role_policy" "allow_consul_step_function_to_invoke_lambdas" {
  policy = data.aws_iam_policy_document.allow_consul_step_function_to_invoke_lambdas.json
  role   = aws_iam_role.consul_step_machine.name
}


resource "aws_cloudwatch_metric_alarm" "autorecyle_consul_cloudwatch_alarm" {
  count             = local.enable_consul_lambdas ? 1 : 0
  alarm_name        = "monitor-${aws_sfn_state_machine.recycle_consul_agents[0].name}"
  alarm_description = "Step function failure. ${aws_sfn_state_machine.recycle_consul_agents[0].name} in environment ${var.environment}"

  namespace           = "AWS/States"
  metric_name         = "ExecutionsFailed"
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  period              = 60

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.recycle_consul_agents[0].id
  }

  treat_missing_data = "ignore"
  statistic          = "Maximum"
}

# Dummy lambda to cover for the missing lambdas in management
data "archive_file" "dummy_consul_lambda" {
  type        = "zip"
  output_path = "lambda_function_payload.zip"

  source {
    content  = "dummy"
    filename = "dummy.py"
  }
}

resource "aws_lambda_function" "dummy_consul_lambda" {
  filename      = "lambda_function_payload.zip"
  function_name = "autorecycle_consul_dummy_lambda"
  role          = module.autorecycle_lambda.iam_role_arn
  handler       = "dummy"
  runtime       = "python3.10"

  source_code_hash = data.archive_file.dummy_lambda.output_base64sha256
}

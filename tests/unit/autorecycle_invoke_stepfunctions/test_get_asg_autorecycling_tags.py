import unittest
from unittest.mock import Mock, call, patch

from src.autorecycle_invoke_stepfunctions.aws import get_autorecycling_tags


class TestGetAutorecyclingTags(unittest.TestCase):
    @patch("boto3.client")
    def test_get_autorecycling_tags_requests_tags_using_correct_filters(self, mock_client):
        asg_name = "my-super-duper-asg"
        expected_filters = {
            "Filters": [
                dict(Name="auto-scaling-group", Values=[asg_name]),
                dict(
                    Name="key",
                    Values=[
                        "autorecycle_override_component_name",
                        "autorecycle_recycle_on_asg_update",
                        "autorecycle_strategy",
                        "autorecycle_slack_monitoring_channel",
                        "autorecycle_notify_pager_duty",
                        "autorecycle_team",
                        "autorecycle_step_function_name",
                        "autorecycle_dry_run",
                    ],
                ),
            ]
        }
        mock_client.return_value.describe_tags.return_value = {"Tags": []}
        mock_client.return_value.get_paginator.return_value.paginate.return_value.search.return_value = iter(
            [{"AutoScalingGroupName": asg_name}]
        )

        get_autorecycling_tags(asg_name)

        mock_client.assert_called_with("autoscaling", "eu-west-2")
        self.assertEqual(len(mock_client.mock_calls), 2)
        self.assertEqual(mock_client.mock_calls[1][0], "().describe_tags")
        self.assertEqual(mock_client.mock_calls[1][2], expected_filters)

    @patch("boto3.client")
    def test_get_autorecycling_tags_returns_the_tags(self, mock_client):
        mock_client.return_value.describe_tags.return_value = {
            "Tags": [
                dict(
                    ResourceId="my-asg-name",
                    ResourceType="auto-scaling-group",
                    Key="autorecycle_recycle_on_asg_update",
                    Value="true",
                    PropagateAtLaunch=True,
                ),
                dict(
                    ResourceId="my-asg-name",
                    ResourceType="auto-scaling-group",
                    Key="autorecycle_strategy",
                    Value="in-out",
                    PropagateAtLaunch=False,
                ),
            ]
        }

        tags = get_autorecycling_tags("my-asg-name")
        self.assertEqual(
            tags,
            dict(autorecycle_recycle_on_asg_update=True, autorecycle_strategy="in-out"),
        )

    def create_tag(self, key, value):
        return dict(
            ResourceId="my-asg-name",
            ResourceType="auto-scaling-group",
            Key=key,
            Value=value,
            PropagateAtLaunch=True,
        )

    @patch("boto3.client")
    def test_get_autorecycling_tags_returns_all_optional_tags(self, mock_client):
        mock_client.return_value.describe_tags.return_value = {
            "Tags": [
                self.create_tag("autorecycle_recycle_on_asg_update", "true"),
                self.create_tag("autorecycle_strategy", "in-out"),
                self.create_tag("autorecycle_slack_monitoring_channel", "slack-monitoring"),
                self.create_tag("autorecycle_notify_pager_duty", "false"),
                self.create_tag("autorecycle_team", "telemetry"),
                self.create_tag("autorecycle_step_function_name", "my-funky-step-function"),
                self.create_tag("autorecycle_dry_run", "false"),
            ]
        }

        tags = get_autorecycling_tags("my-asg-name")
        self.assertEqual(
            tags,
            dict(
                autorecycle_recycle_on_asg_update=True,
                autorecycle_strategy="in-out",
                autorecycle_slack_monitoring_channel="slack-monitoring",
                autorecycle_notify_pager_duty=False,
                autorecycle_team="telemetry",
                autorecycle_step_function_name="my-funky-step-function",
                autorecycle_dry_run=False,
            ),
        )

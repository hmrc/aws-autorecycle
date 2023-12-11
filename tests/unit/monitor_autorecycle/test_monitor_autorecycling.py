import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

from src.monitor_autorecycle.main import (
    _compare_start_times,
    _describe_asg,
    _describe_scaling_activities,
    _get_launching_activities,
    _last_instance_activity_time,
    check,
    check_instances,
    config,
    lambda_handler,
    ScaledDownASGException
)
from tests.test_data.monitor_autorecycle.describe_asg_lc import launch_configuration_asgs
from tests.test_data.monitor_autorecycle.describe_asg_lt import launch_template_asgs

CONTEXT = MagicMock(aws_request_id="test-request-id", function_name="test-function")


def get_test_event():
    return {
        "message_content": {"text": "This is a test"},
        "counter": 0,
        "component": "asg-test-example-not-up-to-date",
        "channels": "team-tiger-alerts",
    }


@patch("boto3.client")
class TestMain(unittest.TestCase):
    def test_lambda_handler_runs_with_lc_healthy(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]
        mock_boto_client().describe_scaling_activities.return_value = {
            "Activities": [
                {
                    "Description": "Launching a new EC2 instance: i-1",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 29),
                },
                {
                    "Description": "Launching a new EC2 instance: i-2",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 32),
                },
                {
                    "Description": "Terminating a new EC2 instance: i-1",
                    "StartTime": datetime(2022, 4, 19, 14, 24),
                    "EndTime": datetime(2022, 4, 19, 14, 33),
                },
            ]
        }

        test_event = get_test_event()
        test_event["component"] = "public_routing_proxy_healthy"

        result = lambda_handler(test_event, CONTEXT)
        self.assertTrue(result["recycle_success"])

        with self.assertLogs("monitor_autorecycle", level="INFO") as log:
            lambda_handler(test_event, CONTEXT)
            self.assertEqual(
                log.output[0],
                "INFO:monitor_autorecycle:Finding a matching ASG for: public_routing_proxy_healthy",
            )
            self.assertEqual(
                log.output[1],
                "INFO:monitor_autorecycle:Found an ASG called: public_routing_proxy_healthy-asg-123",
            )
            self.assertEqual(
                log.output[2],
                "INFO:monitor_autorecycle:We have found 2 instances in the ASG",
            )
            self.assertEqual(log.output[3], "INFO:monitor_autorecycle:Found an instance: i-1")
            self.assertEqual(
                log.output[4],
                "INFO:monitor_autorecycle:i-1 has a HealthStatus of Healthy",
            )
            self.assertEqual(
                log.output[5],
                "INFO:monitor_autorecycle:i-1 has a LifecycleState of InService",
            )
            self.assertEqual(log.output[6], "INFO:monitor_autorecycle:Found an instance: i-2")
            self.assertEqual(
                log.output[7],
                "INFO:monitor_autorecycle:i-2 has a HealthStatus of Healthy",
            )
            self.assertEqual(
                log.output[8],
                "INFO:monitor_autorecycle:i-2 has a LifecycleState of InService",
            )
            self.assertEqual(len(log.output), 10)

    def test_lambda_handler_runs_with_lc_unhealthy(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]
        mock_boto_client().describe_scaling_activities.return_value = {
            "Activities": [
                {
                    "Description": "Launching a new EC2 instance: i-3",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 29),
                },
                {
                    "Description": "Launching a new EC2 instance: i-4",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 32),
                },
                {
                    "Description": "Terminating a new EC2 instance: i-3",
                    "StartTime": datetime(2022, 4, 19, 14, 24),
                    "EndTime": datetime(2022, 4, 19, 14, 33),
                },
            ]
        }

        test_event = get_test_event()
        test_event["component"] = "public_routing_proxy_unhealthy"

        result = lambda_handler(test_event, CONTEXT)
        self.assertFalse(result["recycle_success"])

        with self.assertLogs("monitor_autorecycle", level="INFO") as log:
            lambda_handler(test_event, CONTEXT)
            self.assertEqual(
                log.output[0],
                "INFO:monitor_autorecycle:Finding a matching ASG for: public_routing_proxy_unhealthy",
            )
            self.assertEqual(
                log.output[1],
                "INFO:monitor_autorecycle:Found an ASG called: public_routing_proxy_unhealthy-asg-123",
            )
            self.assertEqual(
                log.output[2],
                "INFO:monitor_autorecycle:We have found 2 instances in the ASG",
            )
            self.assertEqual(log.output[3], "INFO:monitor_autorecycle:Found an instance: i-3")
            self.assertEqual(
                log.output[4],
                "INFO:monitor_autorecycle:i-3 has a HealthStatus of NotHealthy",
            )
            self.assertEqual(
                log.output[5],
                "INFO:monitor_autorecycle:i-3 has a LifecycleState of Pending",
            )
            self.assertEqual(
                log.output[6],
                "INFO:monitor_autorecycle:auto-recycling is not complete because i-3 is not in a healthy state",
            )
            self.assertEqual(len(log.output), 7)

    def test_lambda_handler_runs_with_lc_terminating(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]

        mock_boto_client().describe_scaling_activities.return_value = {
            "Activities": [
                {
                    "Description": "Launching a new EC2 instance: i-5",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 29),
                },
                {
                    "Description": "Launching a new EC2 instance: i-6",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 32),
                },
                {
                    "Description": "Terminating a new EC2 instance: i-6",
                    "StartTime": datetime(2022, 4, 19, 14, 24),
                    "EndTime": datetime(2022, 4, 19, 14, 33),
                },
            ]
        }

        test_event = get_test_event()
        test_event["component"] = "public_routing_proxy_terminating"

        result = lambda_handler(test_event, CONTEXT)
        self.assertFalse(result["recycle_success"])

        with self.assertLogs("monitor_autorecycle", level="INFO") as log:
            lambda_handler(test_event, CONTEXT)
            self.assertEqual(
                log.output[0],
                "INFO:monitor_autorecycle:Finding a matching ASG for: public_routing_proxy_terminating",
            )
            self.assertEqual(
                log.output[1],
                "INFO:monitor_autorecycle:Found an ASG called: public_routing_proxy_terminating-asg-123",
            )
            self.assertEqual(
                log.output[2],
                "INFO:monitor_autorecycle:We have found 2 instances in the ASG",
            )
            self.assertEqual(log.output[3], "INFO:monitor_autorecycle:Found an instance: i-5")
            self.assertEqual(
                log.output[4],
                "INFO:monitor_autorecycle:i-5 has a HealthStatus of NotHealthy",
            )
            self.assertEqual(
                log.output[5],
                "INFO:monitor_autorecycle:i-5 has a LifecycleState of Terminating",
            )
            self.assertEqual(
                log.output[6],
                "INFO:monitor_autorecycle:auto-recycling is not complete because i-5 is not in a healthy state",
            )
            self.assertEqual(len(log.output), 7)

    def test_lambda_handler_runs_with_no_lc(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]
        mock_boto_client().describe_scaling_activities.return_value = {
            "Activities": [
                {
                    "Description": "Launching a new EC2 instance: i-7",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 29),
                },
                {
                    "Description": "Launching a new EC2 instance: i-8",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 32),
                },
                {
                    "Description": "Terminating a new EC2 instance: i-7",
                    "StartTime": datetime(2022, 4, 19, 14, 24),
                    "EndTime": datetime(2022, 4, 19, 14, 33),
                },
            ]
        }

        test_event = get_test_event()
        test_event["component"] = "public_routing_proxy_no_lc"

        result = lambda_handler(test_event, CONTEXT)
        self.assertTrue(result["recycle_success"])

        with self.assertLogs("monitor_autorecycle", level="INFO") as log:
            lambda_handler(test_event, CONTEXT)
            self.assertEqual(
                log.output[0],
                "INFO:monitor_autorecycle:Finding a matching ASG for: public_routing_proxy_no_lc",
            )
            self.assertEqual(
                log.output[1],
                "INFO:monitor_autorecycle:Found an ASG called: public_routing_proxy_no_lc-asg-123",
            )
            self.assertEqual(
                log.output[2],
                "INFO:monitor_autorecycle:We have found 2 instances in the ASG",
            )
            self.assertEqual(log.output[3], "INFO:monitor_autorecycle:Found an instance: i-7")
            self.assertEqual(
                log.output[4],
                "INFO:monitor_autorecycle:i-7 has a HealthStatus of Healthy",
            )
            self.assertEqual(
                log.output[5],
                "INFO:monitor_autorecycle:i-7 has a LifecycleState of InService",
            )
            self.assertEqual(log.output[6], "INFO:monitor_autorecycle:Found an instance: i-8")
            self.assertEqual(
                log.output[7],
                "INFO:monitor_autorecycle:i-8 has a HealthStatus of Healthy",
            )
            self.assertEqual(
                log.output[8],
                "INFO:monitor_autorecycle:i-8 has a LifecycleState of InService",
            )

            self.assertEqual(len(log.output), 10)

    def test_lambda_handler_runs_with_lt_healthy(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]
        mock_boto_client().describe_scaling_activities.return_value = {
            "Activities": [
                {
                    "Description": "Launching a new EC2 instance: i-9",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 29),
                },
                {
                    "Description": "Launching a new EC2 instance: i-10",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 32),
                },
                {
                    "Description": "Terminating a new EC2 instance: i-9",
                    "StartTime": datetime(2022, 4, 19, 14, 24),
                    "EndTime": datetime(2022, 4, 19, 14, 33),
                },
            ]
        }
        test_event = get_test_event()
        test_event["component"] = "public-mdtp-uptodate"

        result = lambda_handler(test_event, CONTEXT)
        self.assertTrue(result["recycle_success"])

        with self.assertLogs("monitor_autorecycle", level="INFO") as log:
            lambda_handler(test_event, CONTEXT)
            self.assertEqual(
                log.output[0],
                "INFO:monitor_autorecycle:Finding a matching ASG for: public-mdtp-uptodate",
            )
            self.assertEqual(
                log.output[1],
                "INFO:monitor_autorecycle:Found an ASG called: public-mdtp-uptodate-asg-123",
            )
            self.assertEqual(
                log.output[2],
                "INFO:monitor_autorecycle:We have found 2 instances in the ASG",
            )
            self.assertEqual(log.output[3], "INFO:monitor_autorecycle:Found an instance: i-9")
            self.assertEqual(
                log.output[4],
                "INFO:monitor_autorecycle:i-9 has a HealthStatus of Healthy",
            )
            self.assertEqual(
                log.output[5],
                "INFO:monitor_autorecycle:i-9 has a LifecycleState of InService",
            )
            self.assertEqual(log.output[6], "INFO:monitor_autorecycle:Found an instance: i-10")
            self.assertEqual(
                log.output[7],
                "INFO:monitor_autorecycle:i-10 has a HealthStatus of Healthy",
            )
            self.assertEqual(
                log.output[8],
                "INFO:monitor_autorecycle:i-10 has a LifecycleState of InService",
            )

            self.assertEqual(len(log.output), 10)

    def test_lambda_handler_runs_with_lt_unhealthy(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]
        mock_boto_client().describe_scaling_activities.return_value = {
            "Activities": [
                {
                    "Description": "Launching a new EC2 instance: i-11",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 29),
                },
                {
                    "Description": "Launching a new EC2 instance: i-12",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 32),
                },
                {
                    "Description": "Terminating a new EC2 instance: i-11",
                    "StartTime": datetime(2022, 4, 19, 14, 24),
                    "EndTime": datetime(2022, 4, 19, 14, 33),
                },
            ]
        }

        test_event = get_test_event()
        test_event["component"] = "public-mdtp-unhealthy"
        test_event["counter"] = 20

        result = lambda_handler(test_event, CONTEXT)
        self.assertFalse(result["recycle_success"])
        self.assertEqual(
            {
                "component": "public-mdtp-unhealthy",
                "status": "fail",
                "counter": 21,
                "message_content": {
                    "text": "Autorecycling appears to be taking too long :scream: please investigate.",
                    "color": "danger",
                },
                "recycle_success": False,
                "status": "fail",
                "channels": "team-tiger-alerts",
            },
            result,
        )

    def test_lambda_handler_runs_with_lt_terminating(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]
        mock_boto_client().describe_scaling_activities.return_value = {
            "Activities": [
                {
                    "Description": "Launching a new EC2 instance: i-13",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 29),
                },
                {
                    "Description": "Launching a new EC2 instance: i-14",
                    "StartTime": datetime(2022, 4, 19, 15, 19),
                    "EndTime": datetime(2022, 4, 19, 15, 32),
                },
                {
                    "Description": "Terminating a new EC2 instance: i-13",
                    "StartTime": datetime(2022, 4, 19, 14, 24),
                    "EndTime": datetime(2022, 4, 19, 14, 33),
                },
            ]
        }

        test_event = get_test_event()
        test_event["component"] = "public-mdtp-terminating"
        test_event["channels"] = "team-tiger-alerts"

        with self.assertLogs("monitor_autorecycle", level="INFO") as log:
            lambda_handler(test_event, CONTEXT)
            self.assertEqual(
                log.output[0],
                "INFO:monitor_autorecycle:Finding a matching ASG for: public-mdtp-terminating",
            )
            self.assertEqual(
                log.output[1],
                "INFO:monitor_autorecycle:Found an ASG called: public-mdtp-terminating-asg-123",
            )
            self.assertEqual(
                log.output[2],
                "INFO:monitor_autorecycle:We have found 2 instances in the ASG",
            )
            self.assertEqual(log.output[3], "INFO:monitor_autorecycle:Found an instance: i-13")
            self.assertEqual(
                log.output[4],
                "INFO:monitor_autorecycle:i-13 has a HealthStatus of Healthy",
            )
            self.assertEqual(
                log.output[5],
                "INFO:monitor_autorecycle:i-13 has a LifecycleState of InService",
            )
            self.assertEqual(log.output[6], "INFO:monitor_autorecycle:Found an instance: i-14")
            self.assertEqual(
                log.output[7],
                "INFO:monitor_autorecycle:i-14 has a HealthStatus of NotHealthy",
            )
            self.assertEqual(
                log.output[8],
                "INFO:monitor_autorecycle:i-14 has a LifecycleState of Terminating",
            )
            self.assertEqual(
                log.output[9],
                "INFO:monitor_autorecycle:auto-recycling is not complete because i-14 is not in a healthy state",
            )

            self.assertEqual(len(log.output), 10)

            result = lambda_handler(test_event, CONTEXT)
            self.assertFalse(result["recycle_success"])

    def test_lambda_handler_raises_exception_with_unknown_component(self, mock_boto_client):
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            launch_configuration_asgs(),
            launch_template_asgs(),
        ]

        test_event = get_test_event()
        del test_event["component"]

        with self.assertRaises(Exception):
            lambda_handler(test_event, CONTEXT)


@patch("src.monitor_autorecycle.main.check_instances")
@patch("src.monitor_autorecycle.main._get_launching_activities")
@patch("src.monitor_autorecycle.main._describe_scaling_activities")
@patch("src.monitor_autorecycle.main._describe_asg")
class Check(unittest.TestCase):
    def test_check_returns_false_when_no_scaling_activities(
        self,
        mock_describe_asg,
        mock_scaling_activities,
        mock_launching_activities,
        mock_check_instances,
    ):
        mock_describe_asg.return_value = launch_configuration_asgs()["AutoScalingGroups"][0]
        mock_launching_activities.return_value = []
        component = "doesnt_matter"
        check(component)
        mock_describe_asg.assert_called_with(component)
        mock_scaling_activities.assert_called_with("public_routing_proxy_healthy-asg-123")
        mock_check_instances.assert_not_called()

    def test_check_returns_check_instances_when_scaling_activities(
        self,
        mock_describe_asg,
        mock_scaling_activities,
        mock_launching_activities,
        mock_check_instances,
    ):
        component = "public_routing_proxy_healthy"
        mock_describe_asg.return_value = {"AutoScalingGroupName": "test_asg_name"}
        mock_launching_activities.return_value = [
            {
                "Description": "test_id launch_activity",
            }
        ]
        self.assertEqual(check(component), mock_check_instances.return_value)
        mock_describe_asg.assert_called_with(component)
        mock_scaling_activities.assert_called_with("test_asg_name")
        mock_launching_activities.assert_called_with(mock_scaling_activities.return_value)


class CheckInstances(unittest.TestCase):
    @patch("src.monitor_autorecycle.main._compare_start_times")
    @patch("src.monitor_autorecycle.main._last_instance_activity_time")
    def test_check_instances_with_healthy_instances(self, mock_last_instance_activity_time, mock_compare_start_times):
        asg = launch_configuration_asgs()["AutoScalingGroups"][0]
        launching_activities = "doesnt_matter"
        mock_last_instance_activity_time.side_effect = [1, 2]
        last_activity_calls = [
            call(launching_activities, "i-1"),
            call(launching_activities, "i-2"),
        ]

        check_instances(asg, launching_activities)

        mock_last_instance_activity_time.assert_has_calls(last_activity_calls)
        self.assertEqual(len(mock_last_instance_activity_time.mock_calls), 2)
        mock_compare_start_times.assert_called_with([1, 2], 2)

    def test_check_instances_with_unhealthy_instances(self):
        asg = launch_template_asgs()["AutoScalingGroups"][2]
        launching_activities = "doesnt_matter"
        self.assertFalse(check_instances(asg, launching_activities))

    def test_check_instances_with_instances_not_in_service(self):
        asg = launch_template_asgs()["AutoScalingGroups"][4]
        launching_activities = "doesnt_matter"
        self.assertFalse(check_instances(asg, launching_activities))

    def test_check_instances_with_no_activities(self):
        asg = launch_configuration_asgs()["AutoScalingGroups"][0]
        launching_activities = []

        self.assertEqual(
            check_instances(asg, launching_activities),
            False,
        )


class CompareStartTimes(unittest.TestCase):
    def test_compare_start_times_within_delta(self):
        time = datetime(2022, 4, 19, 15, 28)
        time_minus_one = time - timedelta(minutes=1)
        start_times_list = [time, time_minus_one, time, time_minus_one]
        self.assertTrue(_compare_start_times(start_times_list, 2))

    def test_compare_start_times_not_within_delta(self):
        time = datetime(2022, 4, 19, 15, 28)
        time_minus_one = time - timedelta(minutes=1)
        time_minus_three = time - timedelta(minutes=3)
        start_times_list = [time_minus_three, time, time, time_minus_one]
        self.assertFalse(_compare_start_times(start_times_list, 2))
        self.assertFalse(_compare_start_times(start_times_list[::-1], 2))


class DescribeAsg(unittest.TestCase):
    @patch("boto3.client")
    def test_describe_asg_response_lc(self, mock_boto_client):
        response = launch_configuration_asgs()
        component = "public_routing_proxy"
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            response,
            response,
        ]
        test_response = _describe_asg(component)
        print(test_response)
        self.assertEqual(
            test_response["Instances"][0]["LaunchConfigurationName"],
            "public_routing_proxy-lc-123",
        )

    @patch("boto3.client")
    def test_describe_asg_response_lt(self, mock_boto_client):
        response = launch_template_asgs()
        component = "public-mdtp-uptodate"
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            response,
            response,
        ]
        test_response = _describe_asg(component)
        self.assertEqual(test_response["Instances"][0]["LaunchTemplate"]["Version"], "10")

    @patch("boto3.client")
    def test_describe_scaled_down(self, mock_boto_client):
        response = {
            "AutoScalingGroups": [
                {
                    "AutoScalingGroupName": "public-mdtp-noinstances-asg-123",
                    "LaunchTemplate": {"Version": "10"},
                    "MaxSize": 0,
                    "Instances": [],
                },
            ]
        }

        component = "public-mdtp-noinstances"
        mock_boto_client().get_paginator.return_value.paginate.return_value = [
            response,
            response,
        ]

        with self.assertRaises(ScaledDownASGException):
            _describe_asg(component)

@patch("boto3.client")
class DescribeScalingActivities(unittest.TestCase):
    def test_describe_scaling_activities_returns_activities(self, mock_boto_client):
        response = {
            "Activities": [
                {
                    "Description": "string",
                    "StartTime": datetime(2015, 1, 1),
                    "EndTime": datetime(2015, 1, 1),
                }
            ]
        }

        mock_boto_client().describe_scaling_activities.return_value = response
        self.assertEqual(_describe_scaling_activities("test_asg"), response["Activities"])
        mock_boto_client.assert_called_with("autoscaling", "eu-west-2", config=config)
        mock_boto_client().describe_scaling_activities.assert_called_with(
            AutoScalingGroupName="test_asg",
            MaxRecords=20,
        )


class GetLaunchingActivities(unittest.TestCase):
    def test_get_launching_activities(self):
        # Return all activities with 'launching', in the description
        scaling_activities = [
            {
                "Description": "Launching a new EC2 instance: test_id_1",
            },
            {
                "Description": "Terminating a new EC2 instance: test_id_2",
            },
            {
                "Description": "Launching a new EC2 instance: test_id_3",
            },
        ]
        expected_result = [
            {
                "Description": "Launching a new EC2 instance: test_id_1",
            },
            {
                "Description": "Launching a new EC2 instance: test_id_3",
            },
        ]
        self.assertEqual(_get_launching_activities(scaling_activities), expected_result)


class LastScalingActivityTime(unittest.TestCase):
    def test_last_instance_activity_time_returns_last_activity_start_time(self):
        scaling_activities = [
            {
                "Description": "test_id last_activity",
                "StartTime": datetime(2022, 4, 19, 15, 28),
                "EndTime": datetime(2022, 4, 19, 15, 29),
            },
            {
                "Description": "test_id first_activity",
                "StartTime": datetime(2022, 4, 19, 15, 19),
                "EndTime": datetime(2022, 4, 19, 15, 32),
            },
            {
                "Description": "test_id middle_activity",
                "StartTime": datetime(2022, 4, 19, 15, 24),
                "EndTime": datetime(2022, 4, 19, 15, 33),
            },
        ]
        self.assertEqual(
            _last_instance_activity_time(scaling_activities, "test_id"),
            datetime(2022, 4, 19, 15, 28),
        )

    def test_last_instance_activity_time_returns_last_activity_start_time_excluding_other_instance_ids(
        self,
    ):
        scaling_activities = [
            {
                "Description": "wrong_id last_activity",
                "StartTime": datetime(2022, 4, 19, 15, 28),
                "EndTime": datetime(2022, 4, 19, 15, 29),
            },
            {
                "Description": "test_id first_activity",
                "StartTime": datetime(2022, 4, 19, 15, 19),
                "EndTime": datetime(2022, 4, 19, 15, 32),
            },
            {
                "Description": "test_id middle_activity",
                "StartTime": datetime(2022, 4, 19, 15, 24),
                "EndTime": datetime(2022, 4, 19, 15, 33),
            },
        ]
        self.assertEqual(
            _last_instance_activity_time(scaling_activities, "test_id"),
            datetime(2022, 4, 19, 15, 24),
        )

    def test_no_instance_activities(
        self,
    ):
        scaling_activities = []

        self.assertEqual(_last_instance_activity_time(scaling_activities, "test_id"), None)


@patch("src.monitor_autorecycle.main._monitor_autorecycle")
class TestLambdaHandler(unittest.TestCase):
    def test_lambda_handler_runs(self, mock_monitor_autorecycle):
        event = {"component": "test_component"}
        with patch("src.monitor_autorecycle.main.aws_lambda_logging"):
            self.assertEqual(
                lambda_handler(event, CONTEXT),
                mock_monitor_autorecycle.return_value,
            )
        mock_monitor_autorecycle.assert_called_with(event)

    def test_lambda_handler_raises_on_missing_component(self, mock_monitor_autorecycle):
        event = {"missing_component": "none"}
        with patch("src.monitor_autorecycle.main.aws_lambda_logging"):
            with self.assertRaises(Exception):
                lambda_handler(event, CONTEXT),

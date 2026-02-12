import json
import os
import unittest

from unittest.mock import patch
from src.autorecycle_scale_asg import autoscaling
from src.autorecycle_scale_asg.autoscaling import describe_asg, describe_scaling_activities


def load_json(name):
    with open(f"tests/test_data/autorecycle_scale_asg/{name}.json", "r") as event:
        return json.load(event)


class Test_AutoScaling(unittest.TestCase):
    @patch("boto3.client")
    def test_describe_asg(self, mock_asg_client):
        response = load_json("describe-asg")
        component = "sensu"
        mock_asg_client().get_paginator.return_value.paginate.return_value = [
            response,
            response,
        ]
        test_response = describe_asg(component)
        self.assertEqual(
            test_response[0]["AutoScalingGroupName"],
            "sensu-asg-00340a9d51ccc10d09cc6a6197",
        )

    @patch("boto3.client")
    def test_describe_asg_similar_name(self, mock_asg_client):
        response = load_json("describe-asg-similar-name")
        component = "sensu"
        mock_asg_client().get_paginator.return_value.paginate.return_value = [
            response,
            response,
        ]
        test_response = describe_asg(component)
        self.assertEqual(
            test_response[0]["AutoScalingGroupName"],
            "sensu-asg-00340a9d51ccc10d09cc6a6197",
        )
        self.assertNotEqual(test_response[0]["AutoScalingGroupName"], "tel-sensu-proxy")
        self.assertNotEqual(test_response[0]["AutoScalingGroupName"], "sensu_proxy")

    @patch("boto3.client")
    def test_describe_asg_underscore_2_az(self, mock_asg_client):
        response = load_json("describe-asg-underscore-az")
        component = "protected_oracle_proxy_a"
        mock_asg_client().get_paginator.return_value.paginate.return_value = [
            response,
            response,
        ]
        test_response = describe_asg(component)

        self.assertEqual(
            test_response[0]["AutoScalingGroupName"],
            component + "-asg-2018121414012939380000000e",
        )
        self.assertEqual(
            test_response[1]["AutoScalingGroupName"],
            "protected_oracle_proxy_b-asg-2018121414012930210000000d",
        )

    @patch("boto3.client")
    def test_describe_asg_underscore_3_az(self, mock_asg_client):
        response = load_json("describe-asg-underscore-az")
        component = "kubernetes-etcd_a"
        mock_asg_client().get_paginator.return_value.paginate.return_value = [
            response,
            response,
        ]
        test_response = describe_asg(component)

        self.assertEqual(
            test_response[0]["AutoScalingGroupName"],
            component + "-asg-2018121414012939380000000d",
        )
        self.assertEqual(
            test_response[1]["AutoScalingGroupName"],
            "kubernetes-etcd_b-asg-2018121414012930210000000d",
        )
        self.assertEqual(
            test_response[2]["AutoScalingGroupName"],
            "kubernetes-etcd_c-asg-2018121414012930210000000d",
        )

    @patch("boto3.client")
    def test_execute_scaling_policy_not_success(self, mock_asg_client):
        failure_response = load_json("execute-scaling-policy-failure")

        component = "sensu"
        mock_asg_client().execute_policy.return_value = failure_response

        # with self.assertLogs('autorecycle_scale_asg', level='INFO') as failure_log_message:
        test_not_success_response = autoscaling.execute_scaling_policy(component, "sensu-scale-in")
        self.assertEqual(test_not_success_response["ResponseMetadata"]["HTTPStatusCode"], 418)
        self.assertNotEqual(test_not_success_response["ResponseMetadata"]["HTTPStatusCode"], 200)
        # self.assertEqual(failure_log_message.output, ['INFO:autorecycle_scale_asg:Executing scaling policy: sensu-scale-in on this ASG: sensu'])

    @patch("boto3.client")
    def test_describe_asg_underscore_abc(self, mock_asg_client):
        response = load_json("describe-asg-underscore-abc")
        component = "test_component_a"
        mock_asg_client().get_paginator.return_value.paginate.return_value = [response]
        test_response = describe_asg(component)

        print(test_response)
        self.assertEqual(len(test_response), 2)
        self.assertEqual(
            test_response[0]["AutoScalingGroupName"],
            "test_component_a-asg-20181112132421997300000010",
        )
        self.assertEqual(
            test_response[1]["AutoScalingGroupName"],
            "test_component_b-asg-20181112132421997300000010",
        )

    @patch("boto3.client")
    def test_describe_asg_underscore_abc_no_extension(self, mock_asg_client):
        response = load_json("describe-asg-underscore-abc")
        component = "test_component"
        mock_asg_client().get_paginator.return_value.paginate.return_value = [response]
        test_response = describe_asg(component)

        print(test_response)
        self.assertEqual(len(test_response), 1)
        self.assertEqual(
            test_response[0]["AutoScalingGroupName"],
            "test_component-asg-20181112132421997300000010",
        )

    @patch("boto3.client")
    def test_execute_scaling_policy_success(self, mock_asg_client):
        success_response = load_json("execute-scaling-policy")
        component = "sensu"
        mock_asg_client().execute_policy.return_value = success_response

        # with self.assertLogs('autorecycle_scale_asg', level='INFO') as failure_log_message:
        test_success_response = autoscaling.execute_scaling_policy(component, "sensu-scale-in")
        self.assertEqual(test_success_response["ResponseMetadata"]["HTTPStatusCode"], 200)
        # self.assertEqual(failure_log_message.output, ['INFO:autorecycle_scale_asg:Executing scaling policy: sensu-scale-in on this ASG: sensu'])

    @patch("boto3.client")
    def test_describe_scaling_activities(self, mock_asg_client):
        response = load_json("describe-scaling-activities")
        asg_name = "public_monolith_activemq_a-asg-0123456789"
        policy = "recycle-scale-in"
        mock_asg_client().describe_scaling_activities.return_value = response
        test_response = describe_scaling_activities(asg_name)
        self.assertEqual(test_response["Description"], "Terminating EC2 instance: i-0123456789")

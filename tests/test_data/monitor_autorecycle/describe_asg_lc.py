from datetime import datetime


def launch_configuration_asgs():
    return {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "public_routing_proxy_healthy-asg-123",
                "Instances": [
                    {
                        "InstanceId": "i-1",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-2",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public_routing_proxy_unhealthy-asg-123",
                "Instances": [
                    {
                        "InstanceId": "i-3",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "Pending",
                        "HealthStatus": "NotHealthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-4",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public_routing_proxy_terminating-asg-123",
                "Instances": [
                    {
                        "InstanceId": "i-5",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "Terminating",
                        "HealthStatus": "NotHealthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-6",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public_routing_proxy_no_lc-asg-123",
                "Instances": [
                    {
                        "InstanceId": "i-7",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-8",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public_routing_proxy-asg-123",
                "Instances": [
                    {
                        "InstanceId": "i-9",
                        "AvailabilityZone": "eu-west-2a",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchConfigurationName": "public_routing_proxy-lc-123",
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    }
                ],
            },
        ]
    }

from datetime import datetime


def launch_template_asgs():
    return {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "public-mdtp-uptodate-asg-123",
                "LaunchTemplate": {"Version": "10"},
                "MaxSize": 2,
                "Instances": [
                    {
                        "InstanceId": "i-9",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-10",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public-mdtp-not-uptodate-asg-123",
                "LaunchTemplate": {"Version": "10"},
                "MaxSize": 2,
                "Instances": [
                    {
                        "InstanceId": "i-9",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-10",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchTemplate": {"Version": "9"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public-mdtp-unhealthy-asg-123",
                "LaunchTemplate": {"Version": "10"},
                "MaxSize": 2,
                "Instances": [
                    {
                        "InstanceId": "i-11",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "NotHealthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-12",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "NotHealthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public-mdtp-terminating-asg-123",
                "LaunchTemplate": {"Version": "10"},
                "MaxSize": 2,
                "Instances": [
                    {
                        "InstanceId": "i-13",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-14",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "Terminating",
                        "HealthStatus": "NotHealthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
            {
                "AutoScalingGroupName": "public-mdtp-NotInService-asg-123",
                "LaunchTemplate": {"Version": "10"},
                "MaxSize": 2,
                "Instances": [
                    {
                        "InstanceId": "i-11",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "NotInService",
                        "HealthStatus": "Healthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                    {
                        "InstanceId": "i-12",
                        "AvailabilityZone": "eu-west-2b",
                        "LifecycleState": "InService",
                        "HealthStatus": "Healthy",
                        "LaunchTemplate": {"Version": "10"},
                        "StartTime": datetime(2022, 4, 19, 15, 19),
                    },
                ],
            },
        ]
    }

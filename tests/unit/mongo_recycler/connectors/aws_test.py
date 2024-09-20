from unittest.mock import MagicMock, Mock, call, patch

import pytest
import src.mongo_recycler.connectors.aws as aws
from botocore.exceptions import ClientError
from tests.unit.mongo_recycler.test_utils import create_primary_1

reservations = {
    "Reservations": [
        {
            "Instances": [
                {
                    "ImageId": "ami-e6618481",
                    "InstanceId": "i-084d2313533e254c0",
                    "State": {"Name": "running"},
                    "NetworkInterfaces": [
                        {
                            "Attachment": {"DeleteOnTermination": False},
                            "PrivateIpAddress": "172.26.24.21",
                        },
                        {
                            "Attachment": {"DeleteOnTermination": True},
                            "PrivateIpAddress": "172.26.24.22",
                        },
                    ],
                },
                {
                    "ImageId": "ami-e6618482",
                    "InstanceId": "i-084d2313533e254c1",
                    "State": {"Name": "running"},
                    "NetworkInterfaces": [
                        {
                            "Attachment": {"DeleteOnTermination": False},
                            "PrivateIpAddress": "172.26.24.31",
                        },
                        {
                            "Attachment": {"DeleteOnTermination": True},
                            "PrivateIpAddress": "172.26.24.32",
                        },
                    ],
                },
            ]
        }
    ]
}

reservations_no_eni = {
    "Reservations": [
        {
            "Instances": [
                {
                    "ImageId": "ami-e6618481",
                    "InstanceId": "i-084d2313533e254c0",
                    "State": {"Name": "running"},
                    "NetworkInterfaces": [
                        {
                            "Attachment": {"DeleteOnTermination": True},
                            "PrivateIpAddress": "172.26.24.21",
                        },
                        {
                            "Attachment": {"DeleteOnTermination": True},
                            "PrivateIpAddress": "172.26.24.22",
                        },
                    ],
                },
                {
                    "ImageId": "ami-e6618482",
                    "InstanceId": "i-084d2313533e254c1",
                    "State": {"Name": "running"},
                    "NetworkInterfaces": [],
                },
            ]
        }
    ]
}

reservations_with_terminated_instance = {
    "Reservations": [
        {
            "Instances": [
                {
                    "ImageId": "ami-e6618481",
                    "InstanceId": "i-084d2313533e254c0",
                    "State": {"Name": "running"},
                    "NetworkInterfaces": [
                        {
                            "Attachment": {"DeleteOnTermination": False},
                            "PrivateIpAddress": "172.26.24.21",
                        },
                        {
                            "Attachment": {"DeleteOnTermination": True},
                            "PrivateIpAddress": "172.26.24.22",
                        },
                    ],
                },
                {
                    "ImageId": "ami-e6618482",
                    "InstanceId": "i-084d2313533e254c1",
                    "State": {"Name": "terminated"},
                    "NetworkInterfaces": [
                        {
                            "Attachment": {"DeleteOnTermination": False},
                            "PrivateIpAddress": "172.26.24.31",
                        },
                        {
                            "Attachment": {"DeleteOnTermination": True},
                            "PrivateIpAddress": "172.26.24.32",
                        },
                    ],
                },
            ]
        }
    ]
}

non_paginated_launch_configurations = {"LaunchConfigurations": [{"a": "b"}, {"c": "d"}, {"a1": "b1"}, {"c1": "d1"}]}
paginated_launch_configurations = [
    {"LaunchConfigurations": [{"a": "b"}, {"c": "d"}]},
    {"LaunchConfigurations": [{"a1": "b1"}, {"c1": "d1"}]},
]


def test_describe_mongodb_instances():
    expected_result = [
        {
            "InstanceId": "i-084d2313533e254c0",
            "ImageId": "ami-e6618481",
            "IpAddress": "172.26.24.21",
        },
        {
            "InstanceId": "i-084d2313533e254c1",
            "ImageId": "ami-e6618482",
            "IpAddress": "172.26.24.31",
        },
    ]

    result = list(aws.describe_mongodb_instances(reservations))

    assert result == expected_result


def test_describe_mongodb_instances_no_eni_found():
    with pytest.raises(aws.NoENIFound) as e_info:
        list(aws.describe_mongodb_instances(reservations_no_eni))

    assert str(e_info.value) == "No ENI found for instance : i-084d2313533e254c0"


def test_describe_mongodb_instances_filters_out_non_running_instances():
    expected_result = [
        {
            "InstanceId": "i-084d2313533e254c0",
            "ImageId": "ami-e6618481",
            "IpAddress": "172.26.24.21",
        }
    ]

    result = list(aws.describe_mongodb_instances(reservations_with_terminated_instance))

    assert result == expected_result


def test_create_instance_name_filters():
    expected_result = [
        {
            "Name": "tag:Name",
            "Values": [
                "protected_rate_mongo_a",
                "protected_rate_mongo_b",
                "protected_rate_mongo_c",
            ],
        }
    ]

    assert aws.create_instance_name_filters("protected_rate_mongo_a") == expected_result
    assert aws.create_instance_name_filters("protected_rate_mongo") == expected_result


def test_instance_state_assuming_single_return_value():
    reservations = {"Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]}

    result = aws.instance_state(reservations)
    assert result == "running"


def test_instance_state_raises_if_instance_list_is_empty():
    reservations = {"Reservations": [{"Instances": []}]}

    with pytest.raises(aws.NoInstancesFound):
        aws.instance_state(reservations)


def test_instance_state_raises_if_reservation_list_is_empty():
    reservations = {"Reservations": []}

    with pytest.raises(aws.NoInstancesFound):
        aws.instance_state(reservations)


def test_instance_state_raises_if_more_than_one_instance():
    reservations = {
        "Reservations": [
            {
                "Instances": [
                    {"State": {"Name": "running"}},
                    {"State": {"Name": "running"}},
                ]
            }
        ]
    }

    with pytest.raises(aws.TooManyInstancesFound):
        aws.instance_state(reservations)


def test_instance_state_raises_if_more_than_one_reservations():
    reservations = {
        "Reservations": [
            {"Instances": [{"State": {"Name": "running"}}]},
            {"Instances": [{"State": {"Name": "running"}}]},
        ]
    }

    with pytest.raises(aws.TooManyReservationsFound):
        aws.instance_state(reservations)


def test_assert_terminated_throws_if_running():
    with pytest.raises(AssertionError) as e_info:
        aws.assert_terminated("running")

    assert str(e_info.value) == "instance is in state running"


def test_assert_terminated_doesnt_throw_if_not_running():
    aws.assert_terminated("terminated")


@patch("boto3.client")
def test_get_instance_state(mock_client):
    reservations = {"Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]}

    mock_client().describe_instances.return_value = reservations

    expected_result = "running"

    client = aws.AWS("protected")
    result = client.get_instance_state("i-123")
    assert result == expected_result
    mock_client().describe_instances.assert_called_with(InstanceIds=["i-123"])


@patch("boto3.client")
def test_get_mongodb_instances_returns_a_filtered_summary_of_mongodb_instances_zone_appended(
    mock_client,
):
    mock_client().describe_instances.return_value = reservations

    client = aws.AWS("protected_rate_mongo_a")
    result = client.get_mongo_db_instances()
    expected_result = aws.describe_mongodb_instances(reservations)
    expected_filters = [
        {
            "Name": "tag:Name",
            "Values": [
                "protected_rate_mongo_a",
                "protected_rate_mongo_b",
                "protected_rate_mongo_c",
            ],
        }
    ]

    assert list(result) == list(expected_result)

    mock_client.assert_called_with("ec2", region_name="eu-west-2")
    mock_client().describe_instances.assert_called_with(Filters=expected_filters)


@patch("boto3.client")
def test_get_mongodb_instances_returns_a_filtered_summary_of_mongodb_instances_zone_not_appended(
    mock_client,
):
    mock_client().describe_instances.return_value = reservations

    client = aws.AWS("protected_rate_mongo")
    result = client.get_mongo_db_instances()
    expected_result = aws.describe_mongodb_instances(reservations)
    expected_filters = [
        {
            "Name": "tag:Name",
            "Values": [
                "protected_rate_mongo_a",
                "protected_rate_mongo_b",
                "protected_rate_mongo_c",
            ],
        }
    ]

    assert list(result) == list(expected_result)

    mock_client.assert_called_with("ec2", region_name="eu-west-2")
    mock_client().describe_instances.assert_called_with(Filters=expected_filters)


@patch("boto3.client")
def test_get_launch_template_image_ids_with_found_templates_returns_list_of_image_ids(
    mock_client,
):
    mock_describe_launch_templates = MagicMock()
    mock_describe_launch_templates.return_value = {
        "LaunchTemplates": [
            {
                "LaunchTemplateId": "lt-0cf12daa1c8798ef7",
                "LaunchTemplateName": "public_mongo_b-lt-20230213152441319800000005",
                "CreateTime": "2023-02-13T15:24:41+00:00",
                "CreatedBy": "arn:aws:sts::150648916438:assumed-role/RoleJenkinsTerraformProvisioner/1676301874",
                "DefaultVersionNumber": 1,
                "LatestVersionNumber": 5,
                "Tags": [{"Key": "Component", "Value": "public_mongo_b"}],
            },
            {
                "LaunchTemplateId": "lt-03c416e9d886757f9",
                "LaunchTemplateName": "public_mongo_a-lt-20230213152441312500000003",
                "CreateTime": "2023-02-13T15:24:41+00:00",
                "CreatedBy": "arn:aws:sts::150648916438:assumed-role/RoleJenkinsTerraformProvisioner/1676301874",
                "DefaultVersionNumber": 1,
                "LatestVersionNumber": 5,
                "Tags": [{"Key": "Component", "Value": "public_mongo_a"}],
            },
            {
                "LaunchTemplateId": "lt-0176365d6f06cc351",
                "LaunchTemplateName": "public_mongo_c-lt-20230213152441308100000001",
                "CreateTime": "2023-02-13T15:24:41+00:00",
                "CreatedBy": "arn:aws:sts::150648916438:assumed-role/RoleJenkinsTerraformProvisioner/1676301874",
                "DefaultVersionNumber": 1,
                "LatestVersionNumber": 5,
                "Tags": [{"Key": "Component", "Value": "public_mongo_c"}],
            },
        ]
    }

    mock_describe_launch_template_versions = MagicMock()
    mock_describe_launch_template_versions.return_value = {
        "LaunchTemplateVersions": [{"LaunchTemplateData": {"ImageId": "ami-006b1a02425203dfe"}}]
    }

    mock_client().describe_launch_templates = mock_describe_launch_templates
    mock_client().describe_launch_template_versions = mock_describe_launch_template_versions

    client = aws.AWS("public_mongo")
    result = client.get_launch_template_image_ids()

    assert result == [
        "ami-006b1a02425203dfe",
        "ami-006b1a02425203dfe",
        "ami-006b1a02425203dfe",
    ]

    mock_client.assert_called_with("ec2", region_name="eu-west-2")
    mock_describe_launch_templates.assert_called_with(
        Filters=[{"Name": "launch-template-name", "Values": ["public_mongo*"]}]
    )

    mock_describe_launch_template_versions.assert_has_calls(
        [
            call(LaunchTemplateId="lt-0cf12daa1c8798ef7", Versions=["5"]),
            call(LaunchTemplateId="lt-03c416e9d886757f9", Versions=["5"]),
            call(LaunchTemplateId="lt-0176365d6f06cc351", Versions=["5"]),
        ]
    )


@patch("boto3.client")
def test_get_launch_template_image_ids_with_no_found_templates_returns_empty_list(
    mock_client,
):
    mock_describe_launch_templates = MagicMock()
    mock_describe_launch_templates.return_value = {"LaunchTemplates": []}

    mock_describe_launch_template_versions = MagicMock()

    mock_client().describe_launch_templates = mock_describe_launch_templates
    mock_client().describe_launch_template_versions = mock_describe_launch_template_versions

    client = aws.AWS("public_mongo")
    result = client.get_launch_template_image_ids()

    assert result == []
    mock_describe_launch_template_versions.assert_not_called()


class BotoError(ClientError):
    def __init__(self):
        pass


@patch("boto3.resource")
def test_recycle_instance_throws_if_instance_cant_be_found(mock_resource):
    client = aws.AWS("protected")
    mock_resource().instances.filter.side_effect = BotoError()

    with pytest.raises(aws.NoInstancesFound):
        client.recycle_instance(create_primary_1("ami-123"))


@patch("boto3.resource")
def test_recycle_instance_throws_if_more_than_one_instance_found(mock_resource):
    client = aws.AWS("protected")
    mock_resource().instances.filter().all.return_value = iter(["instance-1", "instance-2"])

    with pytest.raises(aws.TooManyInstancesFound):
        client.recycle_instance(create_primary_1("ami-123"))


@patch("boto3.resource")
def test_recycle_instance_throws_if_instance_cant_be_terminated_for_any_reason(
    mock_resource,
):
    client = aws.AWS("protected")

    mock_instance = Mock()
    mock_resource().instances.filter().all.return_value = iter([mock_instance])
    mock_instance.terminate.side_effect = Exception

    with pytest.raises(Exception):
        client.recycle_instance(create_primary_1("ami-123"))


@patch("src.mongo_recycler.connectors.aws.poll")
@patch("boto3.resource")
def test_recycle_instance_terminates_instance_if_it_can_be_found_and_polls_until_dead(mock_resource, mock_poll):
    client = aws.AWS("protected")

    mock_instance = Mock()
    mock_resource().instances.filter().all.return_value = iter([mock_instance])
    mock_instance.terminate.return_value = {}

    client.recycle_instance(create_primary_1("ami-123"))

    mock_resource.assert_called_with("ec2", region_name="eu-west-2")
    mock_resource().instances.filter.assert_called_with(InstanceIds=["i-084d2313533e254c0"])
    assert mock_poll.call_count == 1

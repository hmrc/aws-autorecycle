import logging
import re
from typing import Any, Generator

import boto3
from botocore.exceptions import ClientError
from src.mongo_recycler.utils.poll import poll


class NoENIFound(Exception):
    pass


class NoInstancesFound(Exception):
    pass


class TooManyInstancesFound(Exception):
    pass


class TooManyReservationsFound(Exception):
    pass


def create_instance_name_filters(component: str) -> Any:
    instances = [re.sub(r"_[abc]$", "", component) + az for az in ["_a", "_b", "_c"]]
    return [{"Name": "tag:Name", "Values": instances}]


def describe_mongodb_instances(reservations: Any) -> Generator:
    def describe_ip_address_from_instance(instance: Any) -> Any:
        try:
            return [
                interface["PrivateIpAddress"]
                for interface in instance["NetworkInterfaces"]
                if not interface["Attachment"]["DeleteOnTermination"]
            ][0]
        except IndexError:
            raise (NoENIFound("No ENI found for instance : {}".format(instance["InstanceId"])))

    for reservation in reservations["Reservations"]:
        for instance in reservation["Instances"]:
            if instance["State"]["Name"] == "running":
                yield {
                    "InstanceId": instance["InstanceId"],
                    "ImageId": instance["ImageId"],
                    "IpAddress": describe_ip_address_from_instance(instance),
                }


def instance_state(instance_descriptions: Any) -> Any:
    reservations = instance_descriptions["Reservations"]
    if len(reservations) == 0:
        raise NoInstancesFound
    if len(reservations) > 1:
        raise TooManyReservationsFound
    instances = instance_descriptions["Reservations"][0]["Instances"]
    if len(instances) == 0:
        raise NoInstancesFound
    if len(instances) > 1:
        raise TooManyInstancesFound
    return instances[0]["State"]["Name"]


def assert_terminated(state: str) -> bool:
    if state == "terminated":
        return True
    else:
        raise AssertionError("instance is in state {}".format(state))


class AWS:
    def __init__(self, component: str) -> None:
        self.component = component
        self.region_name = "eu-west-2"

    def get_launch_template_image_ids(self) -> list[str]:
        client = boto3.client("ec2", region_name="eu-west-2")

        launch_templates = client.describe_launch_templates(
            Filters=[{"Name": "launch-template-name", "Values": [f"{self.component}*"]}]
        )

        launch_templates_versions = [
            client.describe_launch_template_versions(
                LaunchTemplateId=launch_template["LaunchTemplateId"],
                Versions=[str(launch_template["LatestVersionNumber"])],
            )["LaunchTemplateVersions"][0]
            for launch_template in launch_templates["LaunchTemplates"]
        ]

        return [
            launch_template_version["LaunchTemplateData"]["ImageId"]
            for launch_template_version in launch_templates_versions
        ]

    def get_instance_state(self, instance_id: str) -> Any:
        client = boto3.client("ec2", region_name=self.region_name)
        return instance_state(client.describe_instances(InstanceIds=[instance_id]))

    def get_mongo_db_instances(self) -> Generator:
        client = boto3.client("ec2", region_name=self.region_name)
        reservations = client.describe_instances(Filters=create_instance_name_filters(self.component))
        return describe_mongodb_instances(reservations)

    def recycle_instance(self, instance: Any) -> None:
        resource = boto3.resource("ec2", region_name=self.region_name)

        try:
            instances = list(resource.instances.filter(InstanceIds=[instance.instance_id]).all())
        except ClientError:
            raise NoInstancesFound

        if len(instances) > 1:
            raise TooManyInstancesFound

        instance = instances[0]

        instance.terminate()

        def is_terminated() -> None:
            assert_terminated(self.get_instance_state(instance.instance_id))

        logging.info("waiting for instance {} to terminate".format(instance.instance_id))
        poll(is_terminated, sleep_for_seconds=10)

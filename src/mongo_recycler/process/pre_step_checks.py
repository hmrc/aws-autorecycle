from src.mongo_recycler.connectors.aws import AWS
from src.mongo_recycler.models.instances import Instance


class NoLaunchTemplatesFound(Exception):
    pass


class LaunchTemplateAmiMismatch(Exception):
    pass


class MongoReplicaSetMismatch(Exception):
    pass


def get_ami_and_check_all_amis_match(component: str, aws: AWS) -> str:
    return assert_amis_match_and_get_ami(component, aws.get_launch_template_image_ids())


def assert_amis_match_and_get_ami(component: str, launch_template_image_ids: list[str]) -> str:
    if len(launch_template_image_ids) == 0:
        raise NoLaunchTemplatesFound(f"No launch templates start with `{component}`")

    image_ids = {launch_template_image_id for launch_template_image_id in launch_template_image_ids}

    if len(image_ids) != 1:
        raise LaunchTemplateAmiMismatch(f"AMI IDs do not match in {component} launch templates")

    return image_ids.pop()


def assert_all_nodes_in_same_replica_set(instances: list[Instance]) -> None:
    result_set = {instance.replica_set_name for instance in instances}
    if len(result_set) != 1:
        raise MongoReplicaSetMismatch

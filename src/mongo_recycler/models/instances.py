from collections import namedtuple

Instance = namedtuple(
    "Instance",
    ["instance_id", "image_id", "ip_address", "mongo_state", "replica_set_name"],
)


def find_instances(instances: list[Instance], mongo_state: str) -> list[Instance]:
    return [i for i in instances if i.mongo_state == mongo_state]

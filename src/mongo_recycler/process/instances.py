from typing import Generator

from src.mongo_recycler.connectors.aws import AWS
from src.mongo_recycler.connectors.mongo import Mongo
from src.mongo_recycler.models.instances import Instance


def fetch_replica_set_status(aws: AWS, mongo: Mongo) -> Generator:
    for instance in aws.get_mongo_db_instances():
        node_details = mongo.get_node_details(instance["IpAddress"])
        yield Instance(
            instance_id=instance["InstanceId"],
            image_id=instance["ImageId"],
            ip_address=instance["IpAddress"],
            mongo_state=node_details.node_state,
            replica_set_name=node_details.replica_set_name,
        )

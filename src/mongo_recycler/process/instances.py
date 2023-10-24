from src.mongo_recycler.models.instances import Instance


def fetch_replica_set_status(aws, mongo):
    for instance in aws.get_mongo_db_instances():
        node_details = mongo.get_node_details(instance["IpAddress"])
        yield Instance(
            instance_id=instance["InstanceId"],
            image_id=instance["ImageId"],
            ip_address=instance["IpAddress"],
            mongo_state=node_details.node_state,
            replica_set_name=node_details.replica_set_name,
        )

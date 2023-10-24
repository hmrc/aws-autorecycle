from unittest.mock import Mock

from src.mongo_recycler.connectors import mongo
from src.mongo_recycler.models.instances import Instance
from src.mongo_recycler.process.instances import fetch_replica_set_status


def preprogrammed_get_node_details(ip_address):
    state = {
        "172.26.24.22": "PRIMARY",
        "172.26.24.21": "SECONDARY",
        "172.26.88.21": "SECONDARY",
        "172.26.88.22": "ARBITER",
    }[ip_address]
    return mongo.NodeDetails(state, "int-protected-1")


def test_fetch_replica_set_status():
    mock_mongo = Mock()
    mock_aws = Mock()

    mock_mongo.get_node_details = preprogrammed_get_node_details

    mock_aws.get_mongo_db_instances.return_value = [
        {
            "ImageId": "ami-e6618481",
            "InstanceId": "i-084d2313533e254c0",
            "IpAddress": "172.26.24.22",
        },
        {
            "ImageId": "ami-e6618481",
            "InstanceId": "i-07ac15b12a9cfdbd8",
            "IpAddress": "172.26.24.21",
        },
        {
            "ImageId": "ami-e6618481",
            "InstanceId": "i-074ac0b714dee2968",
            "IpAddress": "172.26.88.21",
        },
        {
            "ImageId": "ami-e6618481",
            "InstanceId": "i-096c79792758d031f",
            "IpAddress": "172.26.88.22",
        },
    ]

    replica_set_status = fetch_replica_set_status(mock_aws, mock_mongo)

    expected_status = [
        Instance(
            image_id="ami-e6618481",
            instance_id="i-084d2313533e254c0",
            ip_address="172.26.24.22",
            mongo_state="PRIMARY",
            replica_set_name="int-protected-1",
        ),
        Instance(
            image_id="ami-e6618481",
            instance_id="i-07ac15b12a9cfdbd8",
            ip_address="172.26.24.21",
            mongo_state="SECONDARY",
            replica_set_name="int-protected-1",
        ),
        Instance(
            image_id="ami-e6618481",
            instance_id="i-074ac0b714dee2968",
            ip_address="172.26.88.21",
            mongo_state="SECONDARY",
            replica_set_name="int-protected-1",
        ),
        Instance(
            image_id="ami-e6618481",
            instance_id="i-096c79792758d031f",
            ip_address="172.26.88.22",
            mongo_state="ARBITER",
            replica_set_name="int-protected-1",
        ),
    ]

    assert list(replica_set_status) == expected_status

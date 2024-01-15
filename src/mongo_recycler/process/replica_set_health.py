from typing import Any

from src.mongo_recycler.connectors.aws import AWS
from src.mongo_recycler.connectors.mongo import Mongo
from src.mongo_recycler.utils.poll import poll


class NodeNotHealthy(Exception):
    pass


class PrimaryError(Exception):
    pass


class SecondaryNotHealthy(Exception):
    pass


healthy_states = {"PRIMARY", "SECONDARY", "ARBITER"}


def assert_one_primary_node(replica_set_members: list[Any]) -> None:
    primary_nodes = [member for member in replica_set_members if member["stateStr"] == "PRIMARY"]
    if len(primary_nodes) != 1:
        raise PrimaryError("primary error, {} primaries found".format(len(primary_nodes)))


def assert_all_nodes_healthy(replica_set_members: list[Any]) -> None:
    for member in replica_set_members:
        state = member["stateStr"]
        if state not in healthy_states:
            raise NodeNotHealthy("{name} is in unhealthy state {state}".format(name=member["name"], state=state))
        if state == "SECONDARY":
            if "syncSourceHost" in member:
                if member["syncSourceHost"] == "":
                    raise SecondaryNotHealthy(
                        "{name} is secondary but has no syncSourceHost".format(name=member["name"])
                    )


def assert_replica_set_healthy(replica_set_status: Any) -> None:
    replica_set_members = replica_set_status["members"]
    assert_all_nodes_healthy(replica_set_members)
    assert_one_primary_node(replica_set_members)


class ReplicaSetHealth:
    def __init__(self, aws: AWS, mongo: Mongo) -> None:
        self.aws = aws
        self.mongo = mongo

    def assert_healthy(self) -> None:
        instances = self.aws.get_mongo_db_instances()
        host = ",".join(i["IpAddress"] for i in instances)
        replica_set_status = self.mongo.replica_set_status(host)
        print(replica_set_status)
        replication_status = self.mongo.replication_status(host)
        print(replication_status)
        assert_replica_set_healthy(replica_set_status)

    def wait_until_cluster_healthy(self) -> None:
        poll(self.assert_healthy, sleep_for_seconds=10, max_iters=60)

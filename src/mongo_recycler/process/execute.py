import logging

from src.mongo_recycler.connectors.aws import AWS
from src.mongo_recycler.connectors.mongo import Mongo
from src.mongo_recycler.models.decision import DONE, STEP_DOWN_AND_RECYCLE_PRIMARY, Decision
from src.mongo_recycler.process.replica_set_health import ReplicaSetHealth

logger = logging.getLogger(__name__)


def execute_action(decision: Decision, aws: AWS, mongo: Mongo, cluster_health: ReplicaSetHealth) -> None:
    instances = aws.get_mongo_db_instances()
    connection_string = ",".join(i["IpAddress"] for i in instances)
    if decision.action == DONE:
        mongo.set_chaining(connection_string, True)
        return
    # We need to disable chaining to ensure that when we terminate a secondary, we can be confident
    # that the other secondary is not syncing from it, as that would lead to replication timeouts
    mongo.set_chaining(connection_string, False)
    if decision.action == STEP_DOWN_AND_RECYCLE_PRIMARY:
        logger.info("STEPPING DOWN MONGO PRIMARY")
        mongo.step_down(decision.instance.ip_address)

        logger.info("WAITING FOR STEP DOWN")
        cluster_health.wait_until_cluster_healthy()

    logger.info("RECYCLING INSTANCE")
    aws.recycle_instance(decision.instance)

    logger.info("WAIT FOR CLUSTER TO BECOME HEALTHY AGAIN")
    cluster_health.wait_until_cluster_healthy()

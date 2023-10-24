import logging

from src.mongo_recycler.models.decision import DONE, STEP_DOWN_AND_RECYCLE_PRIMARY

logger = logging.getLogger(__name__)


def execute_action(decision, aws, mongo, cluster_health):
    if decision.action == DONE:
        return

    if decision.action == STEP_DOWN_AND_RECYCLE_PRIMARY:
        logger.info("STEPPING DOWN MONGO PRIMARY")
        mongo.step_down(decision.instance.ip_address)

        logger.info("WAITING FOR STEP DOWN")
        cluster_health.wait_until_cluster_healthy()

    logger.info("RECYCLING INSTANCE")
    aws.recycle_instance(decision.instance)

    logger.info("WAIT FOR CLUSTER TO BECOME HEALTHY AGAIN")
    cluster_health.wait_until_cluster_healthy()

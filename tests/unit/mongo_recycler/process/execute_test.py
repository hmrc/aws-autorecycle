from unittest.mock import patch

import src.mongo_recycler.process.execute as execute
from src.mongo_recycler.models.decision import done, recycle_secondary, step_down_and_recycle_primary
from tests.unit.mongo_recycler.test_utils import create_primary_1, create_secondary_1


@patch("src.mongo_recycler.connectors.aws.AWS")
@patch("src.mongo_recycler.connectors.mongo.Mongo")
@patch("src.mongo_recycler.process.replica_set_health.ReplicaSetHealth")
def test_execute_action_should_step_down_secondary(mock_replica_set_health, mock_mongo, mock_aws):
    secondary_1 = create_secondary_1("ami-1")
    action = recycle_secondary(secondary_1)

    execute.execute_action(action, mock_aws(), mock_mongo(), mock_replica_set_health())

    mock_aws().recycle_instance.assert_called_with(secondary_1)
    mock_replica_set_health().wait_until_cluster_healthy.assert_called_once()


@patch("src.mongo_recycler.connectors.aws.AWS")
@patch("src.mongo_recycler.connectors.mongo.Mongo")
@patch("src.mongo_recycler.process.replica_set_health.ReplicaSetHealth")
def test_execute_action_should_step_down_primary_then_recycle(mock_replica_set_health, mock_mongo, mock_aws):
    primary_1 = create_primary_1("ami-1")
    action = step_down_and_recycle_primary(primary_1)

    execute.execute_action(action, mock_aws(), mock_mongo(), mock_replica_set_health())

    mock_mongo().step_down.assert_called_with(primary_1.ip_address)
    mock_replica_set_health().wait_until_cluster_healthy.assert_called()
    assert mock_replica_set_health().wait_until_cluster_healthy.call_count == 2
    mock_aws().recycle_instance.assert_called_with(primary_1)


@patch("src.mongo_recycler.connectors.aws.AWS")
@patch("src.mongo_recycler.connectors.mongo.Mongo")
@patch("src.mongo_recycler.process.replica_set_health.ReplicaSetHealth")
def test_execute_action_should_exit_immediately_if_done(mock_replica_set_health, mock_mongo, mock_aws):
    action = done()

    execute.execute_action(action, mock_aws(), mock_mongo(), mock_replica_set_health())

    mock_mongo().step_down.assert_not_called()
    mock_replica_set_health().wait_until_cluster_healthy.assert_not_called()
    mock_aws().recycle_instance.assert_not_called()

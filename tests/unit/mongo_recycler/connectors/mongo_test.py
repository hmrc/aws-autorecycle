import ssl
from unittest.mock import Mock, patch

import pytest
from pymongo.errors import AutoReconnect
from tenacity.wait import wait_none

import src.mongo_recycler.connectors.mongo as mongo


def test_state_string_from_status():
    assert mongo.state_string_from_status({"myState": 0}) == "STARTUP"
    assert mongo.state_string_from_status({"myState": 1}) == "PRIMARY"
    assert mongo.state_string_from_status({"myState": 2}) == "SECONDARY"
    assert mongo.state_string_from_status({"myState": 3}) == "RECOVERING"
    assert mongo.state_string_from_status({"myState": 4}) == "STARTUP2"
    assert mongo.state_string_from_status({"myState": 5}) == "UNKNOWN"
    assert mongo.state_string_from_status({"myState": 6}) == "ARBITER"
    assert mongo.state_string_from_status({"myState": 7}) == "DOWN"
    assert mongo.state_string_from_status({"myState": 8}) == "ROLLBACK"
    assert mongo.state_string_from_status({"myState": 9}) == "REMOVED"


def test_state_string_from_status_fails_if_myState_cannot_be_found():
    with pytest.raises(mongo.InstanceStateNotFound):
        mongo.state_string_from_status({})


def test_node_details():
    instance_status = {"myState": 2, "ok": 1.0, "set": "int-protected-1"}

    expected_result = mongo.NodeDetails("SECONDARY", "int-protected-1")

    result = mongo.node_details(instance_status)
    assert result == expected_result


def test_node_details_unsuccessful():
    instance_status = {"ok": 0}

    with pytest.raises(mongo.MongoRequestFailed):
        mongo.node_details(instance_status)


@patch("aws_get_vault_object.__init__")
@patch("src.mongo_recycler.connectors.mongo.get_credentials")
@patch("pymongo.MongoClient")
def test_get_node_details(mock_mongo_client, mock_get_credentials_object, mock_get_frozen_credentials):
    instance_status = {"myState": 2, "ok": 1.0, "set": "int-protected-1"}

    mock_get_credentials_object.return_value = {"data": {"username": "user", "password": "pass"}}

    mock_get_frozen_credentials.return_value = {"data": {"username": "user", "password": "pass"}}

    mock_mongo_client().admin.command.return_value = instance_status

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    expected_result = mongo.NodeDetails("SECONDARY", "int-protected-1")
    result = mongo_instance.get_node_details("1.1.1.1")

    assert result == expected_result


@patch("aws_get_vault_object.__init__")
@patch("src.mongo_recycler.connectors.mongo.get_credentials")
@patch("pymongo.MongoClient")
def test_replica_set_status(mock_mongo_client, mock_get_credentials_object, mock_get_frozen_credentials):
    instance_status = {"myState": 2, "ok": 1.0, "set": "int-protected-1"}

    mock_get_credentials_object.return_value = {"data": {"username": "user", "password": "pass"}}

    mock_get_frozen_credentials.return_value = {"data": {"username": "user", "password": "pass"}}

    mock_mongo_client().admin.command.return_value = instance_status

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    assert mongo_instance.replica_set_status("1.1.1.1") == instance_status

    mock_mongo_client.assert_called_with(
        "1.1.1.1",
        authMechanism="SCRAM-SHA-1",
        password="pass",
        serverSelectionTimeoutMS=5000,
        ssl=True,
        ssl_cert_reqs=ssl.CERT_NONE,
        username="user",
    )


@patch("src.mongo_recycler.connectors.mongo.Mongo._connect")
def test_step_down_requests_primary_step_down_then_catches_connection_error(
    mock_mongo_client,
):
    ip_address = "1.2.3.4"

    mock_mongo_client().admin.command.side_effect = AutoReconnect

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    mongo_instance.step_down(ip_address)

    mock_mongo_client().admin.command.assert_called_with("replSetStepDown", 100)


@patch("pymongo.MongoClient")
def test_step_down_throws_on_any_other_error_but_connection(mock_mongo_client):
    ip_address = "1.2.3.4"

    mock_mongo_client().admin.command.side_effect = Exception

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")

    with pytest.raises(Exception):
        mongo_instance.step_down(ip_address)


@patch("aws_get_vault_object.__init__")
@patch("src.mongo_recycler.connectors.mongo.get_credentials")
@patch("pymongo.MongoClient")
def test_connect_with_auth(mock_mongo_client, mock_get_credentials_object, mock_get_frozen_credentials):
    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    mock_get_credentials_object.return_value = {"data": {"username": "user", "password": "pass"}}

    mock_get_frozen_credentials.return_value = {"data": {"username": "user", "password": "pass"}}

    mongo_instance._connect("")
    mock_mongo_client.assert_called_with(
        "",
        serverSelectionTimeoutMS=5000,
        ssl=True,
        ssl_cert_reqs=ssl.CERT_NONE,
        username="user",
        password="pass",
        authMechanism="SCRAM-SHA-1",
    )


@patch.dict("os.environ", {"VAULT_URL": "test-url"})
@patch("aws_get_vault_object.__init__")
@patch("src.mongo_recycler.connectors.mongo.get_credentials")
@patch("pymongo.MongoClient")
def test_connect_with_auth_again(mock_mongo_client, mock_get_credentials_object, mock_get_frozen_credentials):
    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    mongo_instance._connect("")
    assert mongo_instance.cluster_name == "test_cluster"
    mock_get_credentials_object.assert_called_with(
        "test-url",
        "database/creds/autorecycle_test_cluster",
        "/tmp/.creds_file",
        refresh=True,
        ca_cert=None,
    )


@patch("aws_get_vault_object.__init__")
@patch("src.mongo_recycler.connectors.mongo.get_credentials")
@patch("pymongo.MongoClient")
def test_connect_retries(mock_mongo_client, mock_get_credentials_object, mock_get_frozen_credentials):
    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    mock_get_credentials_object.return_value = {"data": {"username": "user", "password": "pass"}}

    mock_get_frozen_credentials.return_value = {"data": {"username": "user", "password": "pass"}}

    class TemporaryException(Exception):
        pass

    mock_mongo_client.side_effect = [
        TemporaryException,
        TemporaryException,
        TemporaryException,
        Mock(),
    ]

    try:
        mongo_instance._connect("")
    except TemporaryException:
        assert False, "_connect wasn't retried enough times"

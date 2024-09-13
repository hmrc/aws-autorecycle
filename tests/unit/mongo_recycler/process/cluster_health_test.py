from unittest.mock import Mock

import pytest
from src.mongo_recycler.process.replica_set_health import (
    NodeNotHealthy,
    PrimaryError,
    ReplicaSetHealth,
    SecondaryNotHealthy,
    assert_replica_set_healthy,
)


def create_replica_set_status(names_and_statuses):
    return {
        "members": [
            {"name": name, "stateStr": status, "syncSourceHost": syncSourceHost}
            for name, status, syncSourceHost in names_and_statuses
        ],
        "ok": 1.0,
    }


names_and_statuses = [
    ("protected-mongo-a", "PRIMARY", ""),
    ("protected-mongo-b", "SECONDARY", "foo"),
    ("protected-mongo-c", "ARBITER", ""),
]


def test_assert_replica_set_healthy_pass_if_all_nodes_in_primary_secondary_or_arbiter():
    assert_replica_set_healthy(create_replica_set_status(names_and_statuses))


def test_assert_replica_set_healthy_fails_if_not_all_nodes_in_primary_secondary_or_arbiter():
    for status in [
        "STARTUP",
        "RECOVERING",
        "STARTUP2",
        "UNKNOWN",
        "DOWN",
        "ROLLBACK",
        "REMOVED",
    ]:
        invalid_names_and_statuses = names_and_statuses + [("protected-mongo-d", status, "foo")]

        with pytest.raises(NodeNotHealthy) as e_info:
            assert_replica_set_healthy(create_replica_set_status(invalid_names_and_statuses))

        assert str(e_info.value) == "protected-mongo-d is in unhealthy state {}".format(status)


def test_assert_replica_set_healthy_fails_with_no_primary():
    names_and_statuses = [
        ("protected-mongo-a", "SECONDARY", "foo"),
        ("protected-mongo-b", "SECONDARY", "foo"),
        ("protected-mongo-c", "ARBITER", ""),
    ]

    with pytest.raises(PrimaryError) as e_info:
        assert_replica_set_healthy(create_replica_set_status(names_and_statuses))

    assert str(e_info.value) == "primary error, 0 primaries found"


def test_assert_replica_set_healthy_fails_with_too_many_primaries():
    names_and_statuses = [
        ("protected-mongo-a", "PRIMARY", ""),
        ("protected-mongo-b", "SECONDARY", "foo"),
        ("protected-mongo-c", "PRIMARY", ""),
    ]

    with pytest.raises(PrimaryError) as e_info:
        assert_replica_set_healthy(create_replica_set_status(names_and_statuses))

    assert str(e_info.value) == "primary error, 2 primaries found"


def test_assert_replica_set_healthy_fails_with_secondary_having_no_sync_source():
    names_and_statuses = [
        ("protected-mongo-a", "PRIMARY", ""),
        ("protected-mongo-b", "SECONDARY", ""),
        ("protected-mongo-c", "PRIMARY", ""),
    ]

    with pytest.raises(SecondaryNotHealthy) as e_info:
        assert_replica_set_healthy(create_replica_set_status(names_and_statuses))

    assert str(e_info.value) == "protected-mongo-b is secondary but has no syncSourceHost"


def test_assert_healthy():
    mock_aws = Mock()
    mock_mongo = Mock()

    mock_aws().get_mongo_db_instances.return_value = [
        {
            "InstanceId": "i-084d2313533e254c0",
            "ImageId": "ami-e6618481",
            "IpAddress": "172.26.24.21",
        },
        {
            "InstanceId": "i-084d2313533e254c3",
            "ImageId": "ami-e6618481",
            "IpAddress": "172.26.24.22",
        },
    ]

    mock_mongo().replica_set_status.return_value = create_replica_set_status(
        [
            ("protected-mongo-a", "PRIMARY", ""),
            ("protected-mongo-b", "SECONDARY", "foo"),
            ("protected-mongo-c", "PRIMARY", ""),
        ]
    )

    cluster_health = ReplicaSetHealth(mock_aws(), mock_mongo())

    with pytest.raises(PrimaryError):
        cluster_health.assert_healthy()

    mock_mongo().replica_set_status.assert_called_with("172.26.24.21,172.26.24.22")

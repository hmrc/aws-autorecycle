import pytest

import src.mongo_recycler.process.pre_step_checks as recycler
from tests.unit.mongo_recycler.test_utils import create_primary_1, create_secondary_1


def test_reports_all_amis_match_and_returns_ami_id():
    result = recycler.assert_amis_match_and_get_ami("protected_mongo", ["ami-1", "ami-1", "ami-1"])

    assert result == "ami-1"


def test_reports_amis_do_not_match():
    with pytest.raises(recycler.LaunchTemplateAmiMismatch) as e_info:
        recycler.assert_amis_match_and_get_ami("protected_rate_mongo", ["ami-1", "ami-1", "ami-2"])

    assert str(e_info.value) == "AMI IDs do not match in protected_rate_mongo launch templates"


def test_reports_if_no_launch_templates_match():
    with pytest.raises(recycler.NoLaunchTemplatesFound) as e_info:
        recycler.assert_amis_match_and_get_ami("duff_replica_set", [])

    assert str(e_info.value) == "No launch templates start with `duff_replica_set`"


def test_assert_all_nodes_in_same_replica_set_with_healthy_instances():
    healthy_instances = [create_secondary_1("ami_1"), create_primary_1("ami_1")]

    recycler.assert_all_nodes_in_same_replica_set(healthy_instances)


def test_assert_all_nodes_in_same_replica_set_with_unhealthy_instances():
    unhealthy_instance = [
        create_secondary_1("ami_1"),
        create_primary_1("ami_1")._replace(replica_set_name="definitely-not-a-set-name"),
    ]

    with pytest.raises(recycler.MongoReplicaSetMismatch):
        recycler.assert_all_nodes_in_same_replica_set(unhealthy_instance)

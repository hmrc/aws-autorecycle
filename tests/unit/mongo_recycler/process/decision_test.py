import src.mongo_recycler.process.decision as decision
from colors import bold, faint, green, red, yellow
from src.mongo_recycler.models.decision import done, recycle_secondary, step_down_and_recycle_primary
from tests.unit.mongo_recycler.test_utils import (
    create_arbiter_1,
    create_primary_1,
    create_recovering_1,
    create_secondary_1,
    create_secondary_2,
)


def test_decision_if_there_are_no_out_of_date_nodes():
    target_ami_id = "ami-1"

    primary_1 = create_primary_1(target_ami_id)
    secondary_1 = create_secondary_1(target_ami_id)
    secondary_2 = create_secondary_2(target_ami_id)
    arbiter_1 = create_arbiter_1(target_ami_id)

    replica_set_status = [primary_1, secondary_1, secondary_2, arbiter_1]

    action = decision.decide_on_action(replica_set_status, target_ami_id)

    assert action == done()


def test_decision_only_arbiter_is_out_of_date():
    target_ami_id = "ami-1"
    old_ami_id = "ami-2"

    primary_1 = create_primary_1(target_ami_id)
    secondary_1 = create_secondary_1(target_ami_id)
    secondary_2 = create_secondary_2(target_ami_id)
    arbiter_1 = create_arbiter_1(old_ami_id)

    replica_set_status = [primary_1, secondary_1, secondary_2, arbiter_1]

    action = decision.decide_on_action(replica_set_status, target_ami_id)

    assert action == done()


def test_decide_on_action_if_there_are_out_of_date_secondaries():
    target_ami_id = "ami-1"
    old_ami_id = "ami-2"

    primary_1 = create_primary_1(old_ami_id)
    secondary_1 = create_secondary_1(target_ami_id)
    secondary_2 = create_secondary_2(old_ami_id)
    arbiter_1 = create_arbiter_1(old_ami_id)

    replica_set_status = [primary_1, secondary_1, secondary_2, arbiter_1]

    action = decision.decide_on_action(replica_set_status, target_ami_id)

    assert action == recycle_secondary(secondary_2)


def test_decide_on_action_if_there_is_only_a_primary_left():
    target_ami_id = "ami-1"
    old_ami_id = "ami-2"

    primary_1 = create_primary_1(old_ami_id)
    secondary_1 = create_secondary_1(target_ami_id)
    secondary_2 = create_secondary_2(target_ami_id)
    arbiter_1 = create_arbiter_1(old_ami_id)

    replica_set_status = [primary_1, secondary_1, secondary_2, arbiter_1]

    action = decision.decide_on_action(replica_set_status, target_ami_id)

    assert action == step_down_and_recycle_primary(primary_1)


def test_find_candidates():
    target_ami = "ami-1"
    old_ami = "ami-2"

    instances = [
        create_primary_1(old_ami),
        create_secondary_1(target_ami),
        create_secondary_2(old_ami),
    ]

    result = decision.find_candidates(instances, target_ami)

    assert result == [create_primary_1(old_ami), create_secondary_2(old_ami)]


def test_find_candidates_ignores_nodes_in_awkward_states():
    target_ami = "ami-1"
    old_ami = "ami-2"

    instances = [
        create_primary_1(old_ami),
        create_secondary_1(target_ami),
        create_secondary_2(old_ami),
        create_arbiter_1(old_ami),
        create_recovering_1(old_ami),
    ]

    result = decision.find_candidates(instances, target_ami)

    assert result == [create_primary_1(old_ami), create_secondary_2(old_ami)]


target_ami = "ami-1"
old_ami = "ami-2"


def test_report_cluster_status_shows_red_if_on_old_ami_primary_and_secondary():
    primary_1 = create_primary_1(old_ami)
    secondary_1 = create_secondary_1(old_ami)

    instances = [primary_1, secondary_1]

    assert decision.report_cluster_status(instances, target_ami) == "\n".join(
        [
            red("i-084d2313533e254c0 | PRIMARY | 172.26.24.22 | ami-2"),
            red("i-07ac15b12a9cfdbd8 | SECONDARY | 172.26.24.21 | ami-2"),
        ]
    )


def test_report_cluster_status_shows_yellow_for_non_candidates_no_matter_the_state():
    arbiter_1 = create_arbiter_1(old_ami)
    recovering_1 = create_recovering_1(target_ami)

    instances = [arbiter_1, recovering_1]

    assert decision.report_cluster_status(instances, target_ami) == "\n".join(
        [
            faint("i-096c79792758d031f | ARBITER | 172.26.88.22 | ami-2"),
            faint("i-096c79792758d0345f | RECOVERING | 172.26.88.25 | ami-1"),
        ]
    )


def test_report_cluster_status_shows_green_if_target_ami_matches_on_primary_secondary():
    primary_1 = create_primary_1(target_ami)
    secondary_1 = create_secondary_1(target_ami)

    instances = [primary_1, secondary_1]

    assert decision.report_cluster_status(instances, target_ami) == "\n".join(
        [
            green("i-084d2313533e254c0 | PRIMARY | 172.26.24.22 | ami-1"),
            green("i-07ac15b12a9cfdbd8 | SECONDARY | 172.26.24.21 | ami-1"),
        ]
    )


def test_report_decision_secondary():
    expected_result = yellow("RECYCLE_SECONDARY : i-07ac15b12a9cfdbd8")
    result = decision.report_outcome(recycle_secondary(create_secondary_1("ami-123")))
    assert expected_result == result


def test_report_decision_primary():
    expected_result = bold(yellow("STEP_DOWN_AND_RECYCLE_PRIMARY : i-084d2313533e254c0"))
    result = decision.report_outcome(step_down_and_recycle_primary(create_primary_1("ami-123")))
    assert expected_result == result


def test_report_decision_done():
    expected_result = bold(green("DONE"))
    result = decision.report_outcome(done())
    assert expected_result == result

from colors import bold, faint, green, red, yellow

from src.mongo_recycler.models.decision import (
    DONE,
    RECYCLE_SECONDARY,
    STEP_DOWN_AND_RECYCLE_PRIMARY,
    done,
    recycle_secondary,
    step_down_and_recycle_primary,
)
from src.mongo_recycler.models.instances import find_instances


def choose_color(instance, target_ami):
    if instance.mongo_state not in candidate_states:
        return faint
    if instance.image_id == target_ami:
        return green
    else:
        return red


def report_cluster_status(instances, target_ami):
    return "\n".join(choose_color(instance, target_ami)(instance_to_string(instance)) for instance in instances)


def report_outcome(decision):
    def outcome_string(decision):
        return "{} : {}".format(decision.action, decision.instance.instance_id)

    if decision.action == STEP_DOWN_AND_RECYCLE_PRIMARY:
        return bold(yellow(outcome_string(decision)))
    elif decision.action == RECYCLE_SECONDARY:
        return yellow(outcome_string(decision))
    elif decision.action == DONE:
        return bold(green("{}".format(decision.action)))


def instance_to_string(instance):
    return "{instance_id} | {mongo_state} | {ip_address} | {image_id}".format(**instance._asdict())


candidate_states = {"PRIMARY", "SECONDARY"}


def find_candidates(instances, target_ami):
    return [
        instance
        for instance in instances
        if instance.image_id != target_ami and instance.mongo_state in candidate_states
    ]


def decide_on_action(replica_set_status, target_ami):
    candidates = find_candidates(replica_set_status, target_ami)
    secondaries = find_instances(candidates, mongo_state="SECONDARY")
    primaries = find_instances(candidates, mongo_state="PRIMARY")

    if len(secondaries) != 0:
        return recycle_secondary(secondaries[0])
    elif len(primaries) != 0:
        return step_down_and_recycle_primary(primaries[0])
    else:
        return done()

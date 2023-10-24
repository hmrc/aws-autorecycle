from collections import namedtuple

from src.mongo_recycler.models.instances import Instance

Decision = namedtuple("Decision", ["action", "instance"])

STEP_DOWN_AND_RECYCLE_PRIMARY = "STEP_DOWN_AND_RECYCLE_PRIMARY"
RECYCLE_SECONDARY = "RECYCLE_SECONDARY"
DONE = "DONE"


def done() -> Decision:
    return Decision(DONE, None)


def recycle_secondary(instance: Instance) -> Decision:
    return Decision(RECYCLE_SECONDARY, instance)


def step_down_and_recycle_primary(instance: Instance) -> Decision:
    return Decision(STEP_DOWN_AND_RECYCLE_PRIMARY, instance)

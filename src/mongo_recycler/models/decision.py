from collections import namedtuple

Decision = namedtuple("Decision", ["action", "instance"])

STEP_DOWN_AND_RECYCLE_PRIMARY = "STEP_DOWN_AND_RECYCLE_PRIMARY"
RECYCLE_SECONDARY = "RECYCLE_SECONDARY"
DONE = "DONE"


def done():
    return Decision(DONE, None)


def recycle_secondary(instance):
    return Decision(RECYCLE_SECONDARY, instance)


def step_down_and_recycle_primary(instance):
    return Decision(STEP_DOWN_AND_RECYCLE_PRIMARY, instance)

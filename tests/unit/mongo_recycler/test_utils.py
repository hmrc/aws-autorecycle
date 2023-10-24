from src.mongo_recycler.models.instances import Instance


def create_primary_1(ami):
    return Instance(
        image_id=ami,
        instance_id="i-084d2313533e254c0",
        ip_address="172.26.24.22",
        mongo_state="PRIMARY",
        replica_set_name="int-protected-1",
    )


def create_secondary_1(ami):
    return Instance(
        image_id=ami,
        instance_id="i-07ac15b12a9cfdbd8",
        ip_address="172.26.24.21",
        mongo_state="SECONDARY",
        replica_set_name="int-protected-1",
    )


def create_secondary_2(ami):
    return Instance(
        image_id=ami,
        instance_id="i-074ac0b714dee2968",
        ip_address="172.26.88.21",
        mongo_state="SECONDARY",
        replica_set_name="int-protected-1",
    )


def create_arbiter_1(ami):
    return Instance(
        image_id=ami,
        instance_id="i-096c79792758d031f",
        ip_address="172.26.88.22",
        mongo_state="ARBITER",
        replica_set_name="int-protected-1",
    )


def create_recovering_1(ami):
    return Instance(
        image_id=ami,
        instance_id="i-096c79792758d0345f",
        ip_address="172.26.88.25",
        mongo_state="RECOVERING",
        replica_set_name="int-protected-1",
    )

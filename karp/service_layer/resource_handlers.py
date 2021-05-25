from karp.domain.models.resource import Resource
from karp.domain.ports import UnitOfWorkManager


class CreateResourceHandler:
    def __init__(self, uowm: UnitOfWorkManager):
        self.uowm = uowm

    def handle(self, cmd):
        resource = Resource(
            resource_id=cmd.resource_id,
            name=cmd.name,
            machine_name=cmd.machine_name,
            config=cmd.config,
            message=cmd.message,
            last_modified_by=cmd.created_by,
        )

        with self.uowm.start() as tx:
            tx.resources.put(resource)
            tx.commit()

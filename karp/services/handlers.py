from karp.domain import commands, model, errors

# from karp.domain.model import Issue, IssueReporter
from karp.infrastructure.unit_of_work import UnitOfWork


def create_resource(cmd: commands.CreateResource, uow: UnitOfWork):
    resource = model.Resource(
        entity_id=cmd.id,
        resource_id=cmd.resource_id,
        name=cmd.name,
        config=cmd.config,
        message=cmd.message,
        last_modified=cmd.timestamp,
        last_modified_by=cmd.created_by,
    )

    with uow:
        existing_resource = uow.repo.by_resource_id(cmd.resource_id)
        if existing_resource and existing_resource.id != cmd.id:
            raise errors.IntegrityError(
                f"Resource with '{cmd.resource_id}' already exists."
            )
        uow.repo.put(resource)
        uow.commit()


def update_resource(cmd: commands.UpdateResource, uow: UnitOfWork):
    with uow:
        resource = uow.repo.by_resource_id(cmd.resource_id)
        found_changes = False
        if resource.name != cmd.name:
            resource.name = cmd.name
            found_changes = True
        if resource.config != cmd.config:
            resource.config = cmd.config
            found_changes = True
        if found_changes:
            resource.stamp(
                user=cmd.user,
                message=cmd.message,
                timestamp=cmd.timestamp,
            )
            uow.repo.update(resource)
        uow.commit()

from karp.domain import commands, events, model
from . import unit_of_work


def create_resource(cmd: commands.CreateResource, uow: unit_of_work.UnitOfWork):
    with uow:
        resource = model.Resource(
            resource_id=cmd.resource_id,
            name=cmd.name,
            machine_name=cmd.machine_name,
            config=cmd.config,
            message=cmd.message,
            last_modified_by=cmd.created_by,
            entries=cmd.entries,
        )
        uow.resources.add(resource)
        uow.commit()


def create_entry_in_resource(cmd: commands.CreateEntry, uow: unit_of_work.UnitOfWork):
    with uow:

        resource = uow.resources.get(cmd.resource_id)
        entry = model.Entry(
            entry_id=cmd.entry_id,
            name=cmd.name,
            body=cmd.body,
            message=cmd.message,
            last_modified_by=cmd.created_by,
        )
        resource.entries.add(entry)
        uow.commit()


EVENT_HANDLERS = {events.ResourceCreated: []}

COMMAND_HANDLERS = {
    commands.CreateEntry: create_entry_in_resource,
    commands.CreateResource: create_resource,
}

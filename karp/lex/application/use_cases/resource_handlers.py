import json
import logging
import typing
from pathlib import Path
from typing import IO, Dict, Generic, List, Optional, Tuple

import logging

from karp import errors as karp_errors
from karp.lex.domain import errors, events, entities
from karp.lex.domain.entities import Resource
from karp.foundation import events as foundation_events
from karp.foundation.commands import CommandHandler
from karp.foundation import messagebus
from karp.lex.application.queries import ResourceDto
from karp.lex.application import repositories as lex_repositories
from karp.lex.domain import commands
from karp.lex.application import repositories


logger = logging.getLogger(__name__)

resource_models = {}  # Dict
history_models = {}  # Dict
resource_configs = {}  # Dict
resource_versions = {}  # Dict[str, int]
field_translations = {}  # Dict[str, Dict[str, List[str]]]


class BasingResource:
    def __init__(
        self,
        resource_uow: repositories.ResourceUnitOfWork
    ) -> None:
        self.resource_uow = resource_uow

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


def check_resource_published(resource_ids: List[str]) -> None:
    published_resources = [
        resource.resource_id for resource in get_published_resources()
    ]
    for resource_id in resource_ids:
        if resource_id not in published_resources:
            raise errors.KarpError(
                'Resource is not searchable: "{resource_id}"'.format(
                    resource_id=resource_id
                ),
                errors.ClientErrorCodes.RESOURCE_NOT_PUBLISHED,
            )


class CreatingResource(CommandHandler[commands.CreateResource], BasingResource):
    def __init__(
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        entry_repo_uow: lex_repositories.EntryUowRepositoryUnitOfWork
    ) -> None:
        super().__init__(resource_uow=resource_uow)
        self.entry_repo_uow = entry_repo_uow

    def execute(self, cmd: commands.CreateResource) -> ResourceDto:
        with self.entry_repo_uow as uow:
            entry_repo_exists = uow.repo.get_by_id_optional(cmd.entry_repo_id)
            if not entry_repo_exists:
                raise errors.NoSuchEntryRepository(
                    f"Entry repository '{cmd.entry_repo_id}' not found")

        with self.resource_uow as uow:
            existing_resource = uow.repo.get_by_resource_id_optional(
                cmd.resource_id)
            if (
                existing_resource
                and not existing_resource.discarded
                and existing_resource.entity_id != cmd.entity_id
            ):
                raise errors.IntegrityError(
                    f"Resource with resource_id='{cmd.resource_id}' already exists."
                )

            resource = entities.create_resource(
                entity_id=cmd.entity_id,
                resource_id=cmd.resource_id,
                config=cmd.config,
                message=cmd.message,
                entry_repo_id=cmd.entry_repo_id,
                created_at=cmd.timestamp,
                created_by=cmd.user,
                name=cmd.name,
            )

            uow.repo.save(resource)
            uow.commit()
        return ResourceDto(**resource.dict())

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


class UpdatingResource(CommandHandler[commands.UpdateResource], BasingResource):
    def __init__(self, resource_uow: repositories.ResourceUnitOfWork) -> None:
        super().__init__(resource_uow=resource_uow)

    def execute(self, cmd: commands.UpdateResource):
        with self.resource_uow as uow:
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
                uow.repo.save(resource)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


class PublishingResource(CommandHandler[commands.PublishResource], BasingResource):
    def __init__(
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        **kwargs,
    ) -> None:
        super().__init__(resource_uow=resource_uow)

    def execute(self, cmd: commands.PublishResource):
        logger.info('publishing resource', extra={
                    'resource_id': cmd.resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(cmd.resource_id)
            if not resource:
                raise errors.ResourceNotFound(cmd.resource_id)
            resource.publish(user=cmd.user, message=cmd.message,
                             timestamp=cmd.timestamp)
            uow.repo.save(resource)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


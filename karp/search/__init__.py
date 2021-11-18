from typing import List

import injector

from karp.foundation.commands import CommandHandler
from karp.foundation.events import EventHandler
from karp.lex.domain import events as lex_events
from karp.search.domain import commands
from karp.search.application import handlers
from karp.search.application.queries import ResourceViews
from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.search.application.transformers import (
    EntryTransformer,
    PreProcessor,
)


class Search(injector.Module):
    @injector.provider
    def reindex_resource(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        pre_processor: PreProcessor,
        resource_views: ResourceViews,
    ) -> CommandHandler[commands.ReindexResource]:
        return handlers.ReindexResourceHandler(
            search_service_uow=search_service_uow,
            pre_processor=pre_processor,
            resource_views=resource_views,
        )

    @injector.multiprovider
    def create_index(
        self,
        search_service_uow: SearchServiceUnitOfWork
    ) -> List[EventHandler[lex_events.ResourceCreated]]:
        return [
            handlers.CreateSearchServiceHandler(
                search_service_uow
            )
        ]

    @injector.multiprovider
    def publish_index(
        self,
        search_service_uow: SearchServiceUnitOfWork
    ) -> List[EventHandler[lex_events.ResourcePublished]]:
        return [
            handlers.ResourcePublishedHandler(
                search_service_uow
            )
        ]

    @injector.multiprovider
    def add_entry(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
    ) -> List[EventHandler[lex_events.EntryAdded]]:
        return [
            handlers.EntryAddedHandler(
                search_service_uow=search_service_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]

    @injector.multiprovider
    def update_entry(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
    ) -> List[EventHandler[lex_events.EntryUpdated]]:
        return [
            handlers.EntryUpdatedHandler(
                search_service_uow=search_service_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]

    @injector.multiprovider
    def delete_entry(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
    ) -> List[EventHandler[lex_events.EntryDeleted]]:
        return [
            handlers.EntryDeletedHandler(
                search_service_uow=search_service_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]

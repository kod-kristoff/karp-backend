from collections import defaultdict
from datetime import date
from typing import Dict, List
from unittest import mock

import pytest
from karp import bootstrap
from karp.domain import commands, events

# from karp.service_layer import handlers
from karp.domain import repository  # , notifications
from karp.service_layer import unit_of_work
from karp.utility.unique_id import make_unique_id
from .adapters import (
    bootstrap_test_app,
    FakeEntryRepository,
    FakeResourceRepository,
    FakeUnitOfWork,
)


class TestAddResource:
    def test_create_new_resource(self):
        bus = bootstrap_test_app()
        resource_id = make_unique_id()
        with mock.patch("karp.utility.time.utc_now", return_value=12345):

            bus.handle(
                commands.CreateResource(
                    resource_id=resource_id,
                    machine_name="lex",
                    name="Lex",
                    config={"fields": {}, "sort": "bf"},
                    message="add Lex",
                    created_by="kristoff@example.com",
                )
            )
        resource = bus.uow.resources.get(resource_id)
        assert resource is not None
        assert resource.id == resource_id
        assert resource.machine_name == "lex"
        assert resource.last_modified_by == "kristoff@example.com"
        assert int(resource.last_modified) == 12345
        assert bus.uow.was_committed

    # def test_for_existing_resource(self):
    #     bus = bootstrap_test_app()
    #     bus.handle(commands.CreateResource("b1", "GARISH-RUG", 100, None))
    #     bus.handle(commands.CreateResource("b2", "GARISH-RUG", 99, None))
    #     assert "b2" in [
    #         b.reference for b in bus.uow.resources.get("GARISH-RUG").batches
    #     ]


class TestAddEntryToResource:
    def test_create_new_entry(self):
        bus = bootstrap_test_app()
        resource_id = make_unique_id()
        entry_id = make_unique_id()
        bus.handle(
            commands.CreateResource(
                resource_id=resource_id,
                machine_name="lex",
                name="Lex",
                config={"fields": {}, "sort": "bf"},
                message="add Lex",
                created_by="kristoff@example.com",
                entries=FakeEntryRepository([]),
            )
        )
        bus.handle(
            commands.CreateEntry(
                resource_id=resource_id,
                entry_id=entry_id,
                name="test..1",
                body={"test": "test"},
                # machine_name="lex",
                # name="Lex",
                # config={"fields": {}, "sort": "bf"},
                message="add test..1",
                created_by="kristoff@example.com",
            )
        )
        resource = bus.uow.resources.get(resource_id)
        entry = resource.entries.get(entry_id)
        assert entry is not None
        assert entry.id == entry_id
        assert entry.name == "test..1"
        assert entry.last_modified_by == "kristoff@example.com"
        assert bus.uow.was_committed


# class TestAllocate:
#     def test_allocates(self):
#         bus = bootstrap_test_app()
#         bus.handle(commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None))
#         bus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10))
#         [batch] = bus.uow.resources.get("COMPLICATED-LAMP").batches
#         assert batch.available_quantity == 90

#     def test_errors_for_invalid_sku(self):
#         bus = bootstrap_test_app()
#         bus.handle(commands.CreateBatch("b1", "AREALSKU", 100, None))

#         with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
#             bus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10))

#     def test_commits(self):
#         bus = bootstrap_test_app()
#         bus.handle(commands.CreateBatch("b1", "OMINOUS-MIRROR", 100, None))
#         bus.handle(commands.Allocate("o1", "OMINOUS-MIRROR", 10))
#         assert bus.uow.committed

#     def test_sends_email_on_out_of_stock_error(self):
#         fake_notifs = FakeNotifications()
#         bus = bootstrap.bootstrap(
#             start_orm=False,
#             uow=FakeUnitOfWork(),
#             notifications=fake_notifs,
#             publish=lambda *args: None,
#         )
#         bus.handle(commands.CreateBatch("b1", "POPULAR-CURTAINS", 9, None))
#         bus.handle(commands.Allocate("o1", "POPULAR-CURTAINS", 10))
#         assert fake_notifs.sent["stock@made.com"] == [
#             f"Out of stock for POPULAR-CURTAINS",
#         ]


# class TestChangeBatchQuantity:
#     def test_changes_available_quantity(self):
#         bus = bootstrap_test_app()
#         bus.handle(commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None))
#         [batch] = bus.uow.resources.get(sku="ADORABLE-SETTEE").batches
#         assert batch.available_quantity == 100

#         bus.handle(commands.ChangeBatchQuantity("batch1", 50))
#         assert batch.available_quantity == 50

#     def test_reallocates_if_necessary(self):
#         bus = bootstrap_test_app()
#         history = [
#             commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
#             commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
#             commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
#             commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
#         ]
#         for msg in history:
#             bus.handle(msg)
#         [batch1, batch2] = bus.uow.resources.get(sku="INDIFFERENT-TABLE").batches
#         assert batch1.available_quantity == 10
#         assert batch2.available_quantity == 50

#         bus.handle(commands.ChangeBatchQuantity("batch1", 25))

#         # order1 or order2 will be deallocated, so we'll have 25 - 20
#         assert batch1.available_quantity == 5
#         # and 20 will be reallocated to the next batch
#         assert batch2.available_quantity == 30

from collections import defaultdict
from datetime import date
from typing import Dict, List
import pytest
from karp import bootstrap
from karp.domain import commands, events

# from karp.service_layer import handlers
from karp.domain import repository  # , notifications
from karp.service_layer import unit_of_work
from karp.utility.unique_id import make_unique_id


class FakeEntryRepository(repository.EntryRepository):
    def __init__(self, entrys):
        super().__init__()
        self._entrys = set(entrys)

    def _add(self, entry):
        self._entrys.add(entry)

    def _get(self, id):
        return next((r for r in self._entrys if r.id == id), None)

    # def _get_by_batchref(self, batchref):
    #     return next(
    #         (p for p in self._entrys for b in p.batches if b.reference == batchref),
    #         None,
    #     )


class FakeUnitOfWork(unit_of_work.UnitOfWork):
    def __init__(self):
        self.entries = FakeEntryRepository([])
        self.was_committed = False

    def _commit(self):
        self.was_committed = True

    def rollback(self):
        pass


# class FakeNotifications(notifications.AbstractNotifications):
#     def __init__(self):
#         self.sent = defaultdict(list)  # type: Dict[str, List[str]]

#     def send(self, destination, message):
#         self.sent[destination].append(message)


def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        # notifications=FakeNotifications(),
        # publish=lambda *args: None,
    )

    # def test_for_existing_entry(self):
    #     bus = bootstrap_test_app()
    #     bus.handle(commands.CreateResource("b1", "GARISH-RUG", 100, None))
    #     bus.handle(commands.CreateResource("b2", "GARISH-RUG", 99, None))
    #     assert "b2" in [
    #         b.reference for b in bus.uow.entrys.get("GARISH-RUG").batches
    #     ]


# class TestAllocate:
#     def test_allocates(self):
#         bus = bootstrap_test_app()
#         bus.handle(commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None))
#         bus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10))
#         [batch] = bus.uow.entrys.get("COMPLICATED-LAMP").batches
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
#         [batch] = bus.uow.entrys.get(sku="ADORABLE-SETTEE").batches
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
#         [batch1, batch2] = bus.uow.entrys.get(sku="INDIFFERENT-TABLE").batches
#         assert batch1.available_quantity == 10
#         assert batch2.available_quantity == 50

#         bus.handle(commands.ChangeBatchQuantity("batch1", 25))

#         # order1 or order2 will be deallocated, so we'll have 25 - 20
#         assert batch1.available_quantity == 5
#         # and 20 will be reallocated to the next batch
#         assert batch2.available_quantity == 30

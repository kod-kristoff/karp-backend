from karp import bootstrap
from karp.domain import commands, events

# from karp.service_layer import handlers
from karp.domain import repository  # , notifications
from karp.service_layer import unit_of_work


class FakeEntryRepository(repository.EntryRepository):
    def __init__(self, entries):
        super().__init__()
        self._entries = set(entries)

    def _add(self, entry):
        self._entries.add(entry)

    def _get(self, id):
        print(f"FakeEntryRepository: self._entries = {self._entries}")
        return next((e for e in self._entries if e.id == id), None)


class FakeResourceRepository(repository.ResourceRepository):
    def __init__(self, resources):
        super().__init__()
        self._resources = set(resources)

    def _add(self, resource):
        self._resources.add(resource)

    def _get(self, id):
        return next((r for r in self._resources if r.id == id), None)

    # def _get_by_batchref(self, batchref):
    #     return next(
    #         (p for p in self._resources for b in p.batches if b.reference == batchref),
    #         None,
    #     )


class FakeUnitOfWork(unit_of_work.UnitOfWork):
    def __init__(self):
        self.resources = FakeResourceRepository([])
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

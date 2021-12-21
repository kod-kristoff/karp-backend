import pytest
from karp.foundation.events import EventBus, Event

from karp.lex_infrastructure import SqlResourceUnitOfWork
from karp.lex_infrastructure.repositories.sql_entries import SqlEntryUnitOfWork

from karp.tests.unit.lex import adapters, factories


class FakeEventBus(EventBus):
    def __init__(self) -> None:
        super().__init__()
        self.events = []

    def post(self, event: Event) -> None:
        self.events.append(event)


class TestSqlResourceUnitOfWork:
    def test_rolls_back_uncommitted_work_by_default(self, sqlite_session_factory):
        uow = SqlResourceUnitOfWork(
            sqlite_session_factory, event_bus=FakeEventBus())
        with uow:
            resource = factories.ResourceFactory()
            uow.resources.save(resource)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []

    def test_rolls_back_on_error(self, sqlite_session_factory):

        def do_something_that_fails(resource):
            print(resource.to_string())

        uow = SqlResourceUnitOfWork(
            sqlite_session_factory, event_bus=FakeEventBus())
        with pytest.raises(AttributeError):
            with uow:
                resource = factories.ResourceFactory()
                uow.resources.save(resource)
                do_something_that_fails(resource)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []


class TestSqlEntryUnitOfWork:
    def test_rolls_back_uncommitted_work_by_default(self, sqlite_session_factory):
        uow = SqlEntryUnitOfWork(
            # {"resource_id": "abc", "table_name": "abc"},
            # resource_config={"resource_id": "abc", "config": {}},
            session_factory=sqlite_session_factory,
            event_bus=FakeEventBus()
        )
        with uow:
            entry = factories.EntryFactory(resource_id="abc")
            uow.entries.save(entry)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []

    def test_rolls_back_on_error(self, sqlite_session_factory):
        class MyException(Exception):
            pass

        uow = SqlEntryUnitOfWork(
            {"resource_id": "abc", "table_name": "abc"},
            resource_config={"resource_id": "abc", "config": {}},
            session_factory=sqlite_session_factory,
        )
        with pytest.raises(MyException):
            with uow:
                entry = random_entry(resource_id="abc")
                uow.entries.put(entry)
                raise MyException()

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []

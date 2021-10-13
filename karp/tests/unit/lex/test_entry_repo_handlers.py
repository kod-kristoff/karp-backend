
from karp.lex.application.handlers import (
    CreateEntryRepositoryHandler,
)
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
)
from karp.lex.domain.commands import CreateEntryRepository

from . import adapters, factories


class TestCreateEntryRepository:
    def test_create_entry_repository(
        self,
        lex_test_context: adapters.UnitTestContext,
    ):
        cmd = factories.CreateEntryRepositoryFactory()
        lex_test_context.command_bus.dispatch(cmd)

        entry_uow_repo_uow = lex_test_context.container.get(EntryUowRepositoryUnitOfWork)
        assert entry_uow_repo_uow.was_committed
        assert len(entry_uow_repo_uow.repo) == 1


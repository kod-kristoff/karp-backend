from typing import Any

from karp.foundation.events import EventHandler
from karp.lex import events
from karp.lex_infrastructure.queries.sql_entry_views import SqlEntryViews


class CreatingReadModel(EventHandler[events.ResourceCreated]):
    def __init__(self, entry_views: SqlEntryViews) -> None:
        self._entry_views = entry_views

    def __call__(self, event: events.ResourceCreated, *args: Any, **kwds: Any) -> Any:
        assert False

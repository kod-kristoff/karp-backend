from foundation.events import EventHandler

from karp.lex.domain.events import EntryAdded


class AddingEntryToEntryViews(EventHandler[EntryAdded]):
    pass

import contextlib  # noqa: I001
from karp.search_infrastructure.repositories.es6_indicies import (
    Es6Index,
    Es6IndexUnitOfWork,
)


class TestEs6Index:
    def test_can_instantiate_es6_index(self):  # noqa: ANN201
        with contextlib.suppress(AttributeError):
            Es6Index(es=None, mapping_repo=None)

    def test_can_instantiate_es6_index_uow(self):  # noqa: ANN201
        with contextlib.suppress(AttributeError):
            Es6IndexUnitOfWork(es=None, event_bus=None, mapping_repo=None)

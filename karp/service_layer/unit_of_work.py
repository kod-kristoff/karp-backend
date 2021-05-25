import abc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session


from karp import config
from karp.domain import repository


class UnitOfWork(abc.ABC):
    resources: repository.ResourceRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self):
        for resource in self.resources.seen:
            while resource.events:
                yield resource.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


# DEFAULT_SESSION_FACTORY = sessionmaker(
#     bind=create_engine(
#         config.get_mariadb_uri(),
#         # isolation_level="REPEATABLE READ",
#     )
# )


# class SqlUnitOfWork(UnitOfWork):
#     def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
#         self.session_factory = session_factory

#     def __enter__(self):
#         self.session = self.session_factory()  # type: Session
#         self.resources = repository.SqlResourceRepository(self.session)
#         return super().__enter__()

#     def __exit__(self, *args):
#         super().__exit__(*args)
#         self.session.close()

#     def _commit(self):
#         self.session.commit()

#     def rollback(self):
#         self.session.rollback()

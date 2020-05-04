"""SQL Lexicon Repository"""
from typing import Optional, List, Tuple, Dict
from uuid import UUID

from karp.domain.model.lexicon import Lexicon, Repository as LexiconRepository

from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_repository import SqlRepository


class SqlLexiconRepository(LexiconRepository, SqlRepository):
    def __init__(self, db_uri: str):
        super().__init__(db_uri=db_uri)
        self._table = None
        if self._table is None:
            table_name = "lexicons"
            table = db.get_table(table_name)
            if table is None:
                table = create_table(table_name, self.db_uri)
            self._table = table

    def put(self, lexicon: Lexicon):
        self._check_has_session()
        if lexicon.version is None:
            lexicon._version = self.get_latest_version(lexicon.lexicon_id) + 1
        self._session.execute(
            db.insert(self._table, values=self._lexicon_to_row(lexicon))
        )

    def lexicon_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self._table)
        return [
            row.lexicon_id for row in query.group_by(self._table.c.lexicon_id).all()
        ]

    def lexicons_with_id(self, lexicon_id: str):
        pass

    def lexicon_with_id_and_version(self, lexicon_id: str, version: int):
        self._check_has_session()
        query = self._session.query(Lexicon)
        return query.filter_by(_lexicon_id=lexicon_id, _version=version).first()

    def get_active_lexicon(self, lexicon_id: str) -> Optional[Lexicon]:
        self._check_has_session()
        query = self._session.query(self._table)
        return self._row_to_lexicon(
            query.filter_by(_lexicon_id=lexicon_id, is_active=True).one_or_none()
        )

    def get_latest_version(self, lexicon_id: str) -> int:
        self._check_has_session()
        row = (
            self._session.query(Lexicon)
            .order_by(Lexicon._version.desc())
            .filter_by(_lexicon_id=lexicon_id)
            .first()
        )
        if row is None:
            return 0
        return row.version

    def history_by_lexicon_id(self, lexicon_id: str) -> List:
        return []

    def _lexicon_to_row(
        self, lexicon: Lexicon
    ) -> Tuple[None, UUID, str, int, str, Dict, bool]:
        return (
            None,
            lexicon.id,
            lexicon.lexicon_id,
            lexicon.version,
            lexicon.name,
            lexicon.config,
            lexicon.is_active,
        )

    def _row_to_lexicon(self, row: Optional[Tuple]) -> Optional[Lexicon]:
        if row is None:
            return None

        return Lexicon(
            row.id,
            row.lexicon_id,
            row.version,
            row.name,
            row.config,
            is_active=row.is_active,
        )


def create_table(table_name: str, db_uri: str) -> db.Table:
    table = db.Table(
        table_name,
        db.metadata(db_uri),
        db.Column(
            "history_id",
            db.Integer,
            primary_key=True,
            # autoincrement=True
        ),
        db.Column("id", db.UUIDType, nullable=False),
        db.Column(
            "lexicon_id",
            db.String(64),
            # primary_key=True,
            nullable=False,
        ),
        db.Column(
            "version",
            db.Integer,
            # primary_key=True,
            # autoincrement=True,
            nullable=False,
        ),
        db.Column("name", db.String(64), nullable=False,),
        db.Column("config", db.NestedMutableJson, nullable=False),
        db.Column("is_active", db.Boolean, index=True, nullable=True, default=None),
        db.UniqueConstraint(
            "lexicon_id", "version", name="lexicon_version_unique_constraint"
        ),
        db.UniqueConstraint(
            "lexicon_id", "is_active", name="lexicon_is_active_unique_constraint"
        ),
        mysql_character_set="utf8mb4"
        # extend_existing=True
    )
    db.mapper(
        Lexicon,
        table,
        properties={
            "_id": table.c.id,
            "_version": table.c.version,
            "_name": table.c.name,
            "_lexicon_id": table.c.lexicon_id,
            # "_is_active": table.c.is_active,
        },
    )

    @db.event.listens_for(Lexicon.is_active, "set", retval=True)
    def update_is_active(target, value, oldvalue, initiator):
        if value:
            value = True
        else:
            value = None
        return value

    table.create(db.get_engine(db_uri))
    return table

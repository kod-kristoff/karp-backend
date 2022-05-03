import sqlalchemy


from karp.db_infrastructure import base, db
from karp.db_infrastructure.base_repository import BaseRepository

from karp.lex.domain.entities import Resource, ResourceOp

# from karp.lex_infrastructure.sql.sql_models import ResourceModel

resources = sqlalchemy.Table(
    "resources",
    base.metadata,
    db.Column('history_id', db.Integer, primary_key=True),
    db.Column('entity_id', db.UUIDType, nullable=False),
    db.Column('resource_id', db.String(32), nullable=False),
    db.Column('resource_type', db.String(32), nullable=False),
    db.Column('version', db.Integer, nullable=False),
    db.Column('name', db.String(64), nullable=False),
    db.Column('entry_repo_id', db.UUIDType, nullable=False),
    db.Column('config', db.NestedMutableJson, nullable=False),
    db.Column('is_published', db.Boolean, index=True,
              nullable=True, default=None),
    db.Column('last_modified', db.Float, nullable=False),
    db.Column('last_modified_by', db.String(100), nullable=False),
    db.Column('message', db.String(100), nullable=False),
    db.Column('op', db.Enum(ResourceOp), nullable=False),
    db.Column('discarded', db.Boolean, default=False),
    db.UniqueConstraint(
        "resource_id", "version", name="resource_version_unique_constraint"
        ),
)

class AsyncSqlResourceRepository(BaseRepository):
    async def save(self, resource: Resource):
        query = resources.insert()
        await self.db.execute(query=query, values=resource.dict())

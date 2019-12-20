"""Standard contexts."""
from datetime import datetime, timezone
import json
import logging
from typing import Dict
from typing import List
from typing import Optional

import fastjsonschema  # pyre-ignore

from sqlalchemy import exc as sql_exception

from karp import elasticsearch as es
from karp.database import db
from karp.database import ResourceDefinition
from karp.indexmgr.index import IndexInterface
from karp.errors import KarpError, ClientErrorCodes, EntryNotFoundError, UpdateConflict

# from karp.database import db
from karp.elasticsearch import search as es_search
from karp import search
from karp import resourcemgr
from karp.resourcemgr import entrymetadata

_logger = logging.getLogger("karp")


def _compile_schema(json_schema):
    try:
        validate_entry = fastjsonschema.compile(json_schema)
        return validate_entry
    except fastjsonschema.JsonSchemaDefinitionException as e:
        raise RuntimeError(e)


def _validate_entry(schema, json_obj):
    try:
        schema(json_obj)
    except fastjsonschema.JsonSchemaException as e:
        _logger.warning(
            "Entry not valid:\n%s\nMessage: %s",
            json.dumps(json_obj, indent=2),
            e.message,
        )
        raise KarpError("entry not valid", ClientErrorCodes.ENTRY_NOT_VALID)


class ResourceRepository:
    def __init__(self, indexer: IndexInterface = None):
        self.indexer = indexer

    def get_by_id(
        self, resource_id: str, version: Optional[int] = None
    ) -> resourcemgr.Resource:
        return resourcemgr.get_resource(resource_id, version=version)

    def add_entries(
        self,
        resource_id: str,
        entries: List[Dict],
        user_id: str,
        message: str = None,
        resource_version: int = None,
    ) -> List:
        """
        Add entries to DB and INDEX (if present and resource is active).

        Raises
        ------
        RuntimeError
            If the resource.entry_json_schema fails to compile.
        KarpError
            - If an entry fails to be validated against the json schema.
            - If the DB interaction fails.

        Returns
        -------
        List
            List of the id's of the created entries.
        """
        resource = self.get_by_id(resource_id, version=resource_version)

        validate_entry = _compile_schema(resource.entry_json_schema)

        try:
            created_db_entries = []
            for entry in entries:
                _validate_entry(validate_entry, entry)

                entry_json = json.dumps(entry)
                db_entry = resource.src_entry_to_db_entry(entry, entry_json)
                created_db_entries.append((db_entry, entry, entry_json))
                db.session.add(db_entry)

            db.session.commit()

            created_history_entries = []
            for db_entry, entry, entry_json in created_db_entries:
                history_entry = resource.history_model(
                    entry_id=db_entry.id,
                    user_id=user_id,
                    body=entry_json,
                    version=1,
                    op="ADD",
                    message=message,
                    timestamp=datetime.now(timezone.utc).timestamp(),
                )
                created_history_entries.append((db_entry, entry, history_entry))
                db.session.add(history_entry)
            db.session.commit()
        except sql_exception.IntegrityError as e:
            _logger.exception("IntegrityError")
            print("e = {e!r}".format(e=e))
            print("e.orig.args = {e!r}".format(e=e.orig.args))
            raise KarpError(
                "Database error: {msg}".format(msg=e.orig.args),
                ClientErrorCodes.DB_INTEGRITY_ERROR,
            )
        except sql_exception.SQLAlchemyError as e:
            _logger.exception("Adding entries to DB failed.")
            print("e = {e!r}".format(e=e))
            raise KarpError(f"Database error: {e}", ClientErrorCodes.DB_GENERAL_ERROR)

        if resource.active and self.indexer:
            self.indexer.add_entries(
                resource_id,
                [
                    (
                        db_entry.entry_id,
                        entrymetadata.EntryMetadata.init_from_model(history_entry),
                        self.indexer.transform_to_index_entry(resource, entry)
                        # _src_entry_to_index_entry(resource, entry),
                    )
                    for db_entry, entry, history_entry in created_history_entries
                ],
            )

        return [db_entry.entry_id for db_entry, _, _ in created_db_entries]


class ResourceDefRepository:
    @staticmethod
    def get_available() -> List[ResourceDefinition]:
        return ResourceDefinition.query.filter_by(active=True)

    @staticmethod
    def get_by_id(
        resource_id: str, version: Optional[int] = None
    ) -> Optional[ResourceDefinition]:
        """Get the resource definition for the given id and optional version.

        Arguments:
            resource_id {str} -- id to get.

        Keyword Arguments:
            version {Optional[int]} -- If not given, returns the latest. (default: {None})

        Returns:
            Optional[ResourceDefinition] -- The resource definition if found.
        """
        if version is None:
            return (
                ResourceDefinition.query.filter_by(resource_id=resource_id)
                .order_by(ResourceDefinition.version.desc())
                .first()
            )
        else:
            return ResourceDefinition.query.filter_by(
                resource_id=resource_id, version=version
            ).first()

    @staticmethod
    def get_active_by_id(resource_id: str) -> Optional[ResourceDefinition]:
        """Get the active resource definition for the given id.

        Arguments:
            resource_id {str} -- id to get.

        Returns:
            Optional[ResourceDefinition] -- The resource definition if found.
        """
        return ResourceDefinition.query.filter_by(
            resource_id=resource_id, active=True
        ).first()

    @classmethod
    def get_active_or_latest_by_id(
        cls, resource_id: str
    ) -> Optional[ResourceDefinition]:
        """Get the active or latest resource definition for the given id.

        Arguments:
            resource_id {str} -- id to get.

        Returns:
            Optional[ResourceDefinition] -- The resource definition if found.
        """
        return cls.get_active_by_id(resource_id) or cls.get_by_id(resource_id)


class SQLwES6:
    def __init__(self, app):
        _es = es.Elasticsearch(
            hosts=app.config["ELASTICSEARCH_HOST"],
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=60,
            sniff_timeout=10,
        )
        self.search = es_search.EsSearch(_es)
        self.index_service = es.EsIndex(_es)
        self.auth_service = None
        self.resource_def_repo = ResourceDefRepository()
        self.resource_repo = ResourceRepository(self.index_service)


class SQL:
    def __init__(self, app):
        self.search = search.SearchInterface()
        self.index_service = None
        self.auth_service = None
        self.resource_def_repo = ResourceDefRepository()
        self.resource_repo = ResourceRepository()

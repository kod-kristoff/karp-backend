import json

from typing import List, Dict, Optional

from sb_json_tools import jsondiff

from karp import errors
from karp.database import ResourceDefinition


class Resource:
    def __init__(
        self,
        model,
        history_model,
        resource_def: ResourceDefinition,
        version: int,
        config: Optional[Dict] = None,
    ) -> None:
        self.model = model
        self.history_model = history_model
        if config:
            self.config = config
        else:
            self.config = json.loads(resource_def.config)
        self.entry_json_schema = json.loads(resource_def.entry_json_schema)
        self.active = resource_def.active
        self.version = version

    def __repr__(self):
        return "ResourceConfig(config={})".format(json.dumps(self.config))

    def default_sort(self) -> str:
        return ""

    def get_fields(self) -> List[str]:
        return []

    def is_protected(self, mode: str, fields: List[str]) -> bool:
        print(__name__)
        print(repr(self.config))
        if "protected" in self.config:
            if mode in self.config["protected"]:
                # mode was found
                return self.config["protected"][mode]

        return mode != "read"

    def has_format_query(self, fmt: str) -> bool:
        return True

    @property
    def id(self) -> str:
        return self.config["resource_id"]

    def get_entry_by_id(self, entry_id: str):
        return self.model.query.filter_by(entry_id=entry_id).first()

    def diff(
        self,
        entry_id: str,
        from_version: int = None,
        to_version: int = None,
        from_date: Optional[int] = None,
        to_date: Optional[int] = None,
        entry: Optional[Dict] = None,
    ):
        src = self.model.query.filter_by(entry_id=entry_id).first()

        query = self.history_model.query.filter_by(entry_id=src.id)
        timestamp_field = self.history_model.timestamp

        if from_version:
            obj1_query = query.filter_by(version=from_version)
        elif from_date is not None:
            obj1_query = query.filter(timestamp_field >= from_date).order_by(
                timestamp_field
            )
        else:
            obj1_query = query.order_by(timestamp_field)
        if to_version:
            obj2_query = query.filter_by(version=to_version)
        elif to_date is not None:
            obj2_query = query.filter(timestamp_field <= to_date).order_by(
                timestamp_field.desc()
            )
        else:
            obj2_query = None

        obj1 = obj1_query.first()
        obj1_body = json.loads(obj1.body) if obj1 else None

        if obj2_query:
            obj2 = obj2_query.first()
            obj2_body = json.loads(obj2.body) if obj2 else None
        elif entry is not None:
            obj2 = None
            obj2_body = entry
        else:
            obj2 = query.order_by(timestamp_field.desc()).first()
            obj2_body = json.loads(obj2.body) if obj2 else None

        if not obj1_body or not obj2_body:
            raise errors.KarpError("diff impossible!")

        return (
            jsondiff.compare(obj1_body, obj2_body),
            obj1.version,
            obj2.version if obj2 else None,
        )

    def src_entry_to_db_entry(self, entry, entry_json):
        db_kwargs = self.src_entry_to_db_kwargs(entry, entry_json)
        db_entry = self.model(**db_kwargs)
        return db_entry

    def src_entry_to_db_kwargs(self, entry, entry_json) -> Dict:
        kwargs = {"body": entry_json}

        for field_name in self.config.get("referenceable", ()):
            field_val = entry.get(field_name)
            if self.config["fields"][field_name].get("collection", False):
                child_table = self.model.child_tables[field_name]
                for elem in field_val:
                    if field_name not in kwargs:
                        kwargs[field_name] = []
                    kwargs[field_name].append(child_table(**{field_name: elem}))
            else:
                if field_val:
                    kwargs[field_name] = field_val
        id_field = resource_conf.get("id")
        if id_field:
            kwargs["entry_id"] = entry[id_field]
        else:
            kwargs["entry_id"] = "TODO"  # generate id for resources that are missing it
        return kwargs

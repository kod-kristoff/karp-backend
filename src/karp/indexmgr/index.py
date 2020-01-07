import json
from typing import Dict, List, Tuple

from karp.resourcemgr.entrymetadata import EntryMetadata
from karp import models
from karp import resourcemgr

# from karp import context


class IndexInterface:
    def __init__(self, resource_repo=None):  # context.context.SQLResourceRepository):
        self.resource_repo = resource_repo

    def create_index(self, resource_id: str, config: Dict):
        raise NotImplementedError()

    def publish_index(self, alias_name: str, index_name: str):
        raise NotImplementedError()

    def add_entries(
        self, resource_id: str, entries: List[Tuple[str, EntryMetadata, Dict]]
    ):
        raise NotImplementedError()

    def delete_entry(self, resource_id: str, entry_id: str):
        raise NotImplementedError()

    def create_empty_object(self):
        raise NotImplementedError()

    def assign_field(self, _index_entry, field_name: str, part):
        raise NotImplementedError()

    def create_empty_list(self):
        raise NotImplementedError()

    def add_to_list_field(self, elems: List, elem):
        raise NotImplementedError()

    def transform_to_index_entry(
        self, resource, src_entry: Dict, fields: Tuple[str, Dict] = None
    ):
        index_entry = self.create_empty_object()
        if fields is None:
            fields = resource.config["fields"].items()
        self._transform_to_index_entry(resource, src_entry, index_entry, fields)

    def _evaluate_function(
        self, function_conf: Dict, src_entry: Dict, src_resource: models.Resource
    ):
        if "multi_ref" in function_conf:
            function_conf = function_conf["multi_ref"]
            target_field = function_conf["field"]
            if "resource_id" in function_conf:
                target_resource = self.resource_repo.get_by_id(
                    function_conf["resource_id"], function_conf["resource_version"]
                )
            else:
                target_resource = src_resource

            if "test" in function_conf:
                operator, args = list(function_conf["test"].items())[0]
                filters = {"deleted": False}
                if operator == "equals":
                    for arg in args:
                        if "self" in arg:
                            filters[target_field] = src_entry[arg["self"]]
                        else:
                            raise NotImplementedError()
                    target_entries = target_resource.get_entries_by_column(filters)
                    #entryread.get_entries_by_column(
                    #    target_resource, filters
                    #)
                elif operator == "contains":
                    for arg in args:
                        if "self" in arg:
                            filters[target_field] = src_entry[arg["self"]]
                        else:
                            raise NotImplementedError()
                    target_entries = target_resource.get_entries_by_column(filters)
                    #target_entries = entryread.get_entries_by_column(
                    #    target_resource, filters
                    #)
                else:
                    raise NotImplementedError()
            else:
                raise NotImplementedError()

            res = self.create_empty_list()
            for entry in target_entries:
                index_entry = self.create_empty_object()
                list_of_sub_fields = (("tmp", function_conf["result"]),)
                self._transform_to_index_entry(
                    target_resource,
                    {"tmp": entry["entry"]},
                    index_entry,
                    list_of_sub_fields,
                )
                self.add_to_list_field(res, index_entry["tmp"])
        elif "plugin" in function_conf:
            plugin_id = function_conf["plugin"]
            import karp.pluginmanager as plugins

            res = plugins.plugins[plugin_id].apply_plugin_function(
                src_resource.id, src_resource.version, src_entry
            )
        else:
            raise NotImplementedError()
        return res

    def _transform_to_index_entry(
        self, resource: resourcemgr.Resource, _src_entry: Dict, _index_entry, fields
    ):
        for field_name, field_conf in fields:
            if field_conf.get("virtual", False):
                res = self._evaluate_function(
                    field_conf["function"], _src_entry, resource
                )
                if res:
                    self.assign_field(_index_entry, "v_" + field_name, res)
            elif field_conf.get("ref", {}):
                ref_field = field_conf["ref"]
                if ref_field.get("resource_id"):
                    ref_resource = resourcemgr.get_resource(
                        ref_field["resource_id"], version=ref_field["resource_version"]
                    )
                    if ref_field["field"].get("collection"):
                        ref_objs = []
                        for ref_id in _src_entry[field_name]:
                            ref_entry_body = ref_resource.get_entry_by_id(str(ref_id))
                            #ref_entry_body = entryread.get_entry_by_entry_id(
                            #    ref_resource, str(ref_id)
                            #)
                            if ref_entry_body:
                                ref_entry = {
                                    field_name: json.loads(ref_entry_body.body)
                                }
                                ref_index_entry = {}
                                list_of_sub_fields = ((field_name, ref_field["field"]),)
                                self._transform_to_index_entry(
                                    resource,
                                    ref_entry,
                                    ref_index_entry,
                                    list_of_sub_fields,
                                )
                                ref_objs.append(ref_index_entry[field_name])
                        self.assign_field(_index_entry, "v_" + field_name, ref_objs)
                    else:
                        raise NotImplementedError()
                else:
                    ref_id = _src_entry.get(field_name)
                    if not ref_id:
                        continue
                    if not ref_field["field"].get("collection", False):
                        ref_id = [ref_id]

                    for elem in ref_id:
                        ref = resource.get_entry_by_id(str(elem))
                        # ref = entryread.get_entry_by_entry_id(resource, str(elem))
                        if ref:
                            ref_entry = {field_name: json.loads(ref.body)}
                            ref_index_entry = {}
                            list_of_sub_fields = ((field_name, ref_field["field"]),)
                            self._transform_to_index_entry(
                                resource, ref_entry, ref_index_entry, list_of_sub_fields
                            )
                            self.assign_field(
                                _index_entry,
                                "v_" + field_name,
                                ref_index_entry[field_name],
                            )

            if field_conf["type"] == "object":
                field_content = self.create_empty_object()
                if field_name in _src_entry:
                    self._transform_to_index_entry(
                        resource,
                        _src_entry[field_name],
                        field_content,
                        field_conf["fields"].items(),
                    )
            else:
                field_content = _src_entry.get(field_name)

            if field_content:
                self.assign_field(_index_entry, field_name, field_content)


class IndexModule:
    def __init__(self):
        self.impl = IndexInterface()

    def init(self, impl: IndexInterface):
        self.impl = impl

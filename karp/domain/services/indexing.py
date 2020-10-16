import json
from karp.infrastructure.unit_of_work import unit_of_work
import sys
from typing import Dict, List, Tuple, Optional
import collections
import logging

from karp.domain.models.entry import Entry, create_entry
from karp.domain.models.resource import Resource, ResourceRepository
from karp.domain.models.search_service import IndexEntry, SearchService
from karp.domain.services import network

# from .index import IndexModule
# import karp.resourcemgr as resourcemgr
# import karp.resourcemgr.entryread as entryread
# from karp.resourcemgr.resource import Resource
from karp import errors

# from karp.resourcemgr.entrymetadata import EntryMetadata

# indexer = IndexModule()

logger = logging.getLogger("karp")


# def pre_process_resource(
#     resource_obj: Resource,
# ) -> List[Tuple[str, EntryMetadata, Dict]]:
#     metadata = resourcemgr.get_all_metadata(resource_obj)
#     fields = resource_obj.config["fields"].items()
#     entries = resource_obj.model.query.filter_by(deleted=False)
#     return [
#         (
#             entry.entry_id,
#             metadata[entry.id],
#             transform_to_index_entry(resource_obj, json.loads(entry.body), fields),
#         )
#         for entry in entries
#     ]


def pre_process_resource(
    resource: Resource,
    resource_repo: ResourceRepository,
    indexer: SearchService,
) -> List[IndexEntry]:
    with unit_of_work(using=resource.entry_repository) as uw:
        index_entries = [
            transform_to_index_entry(resource_repo, indexer, resource, entry)
            for entry in uw.all_entries()
        ]
    return index_entries
    # metadata = resourcemgr.get_all_metadata(resource_obj)
    # fields = resource_obj.config["fields"].items()
    # entries = resource_obj.model.query.filter_by(deleted=False)
    # return [
    #     (
    #         entry.entry_id,
    #         metadata[entry.id],
    #         transform_to_index_entry(resource_obj, json.loads(entry.body), fields),
    #     )
    #     for entry in entries
    # ]


# def reindex(
#     resource_id: str,
#     version: Optional[int] = None,
#     search_entries: Optional[List[Tuple[str, EntryMetadata, Dict]]] = None,
# ) -> None:
#     """
#     If `search_entries` is not given, they will be fetched from DB and processed using `transform_to_index_entry`
#     If `search_entries` is given, they most have the same format as the output from `pre_process_resource`
#     """
#     resource_obj = resourcemgr.get_resource(resource_id, version=version)
#     try:
#         index_name = indexer.impl.create_index(resource_id, resource_obj.config)
#     except NotImplementedError:
#         _logger.error("No Index module is loaded. Check your configurations...")
#         sys.exit(errors.NoIndexModuleConfigured)
#     if not search_entries:
#         search_entries = pre_process_resource(resource_obj)
#     add_entries(index_name, search_entries, update_refs=False)
#     indexer.impl.publish_index(resource_id, index_name)
def reindex(
    indexer: SearchService,
    resource_repo: ResourceRepository,
    resource: Resource,
    search_entries: Optional[List[IndexEntry]] = None,
):
    print("creating index ...")
    index_name = indexer.create_index(resource.resource_id, resource.config)

    if not search_entries:
        print("preprocessing entries ...")
        search_entries = pre_process_resource(resource, resource_repo, indexer)
    print(f"adding entries to '{index_name}' ...")
    # add_entries(
    #     resource_repo,
    #     indexer,
    #     resource,
    #     search_entries,
    #     index_name=index_name,
    #     update_refs=False,
    # )
    indexer.add_entries(index_name, search_entries)
    print("publishing ...")
    indexer.publish_index(resource.resource_id, index_name)


# def publish_index(resource_id: str, version: Optional[int] = None) -> None:
def publish_index(
    indexer: SearchService,
    resource_repo: ResourceRepository,
    resource: Resource,
    version: Optional[int] = None,
) -> None:
    print("calling reindex ...")
    reindex(indexer, resource_repo, resource)
    # if version:
    #     resourcemgr.publish_resource(resource_id, version)


# def add_entries(
#     resource_id: str,
#     entries: List[Tuple[str, EntryMetadata, Dict]],
#     update_refs: bool = True,
# ) -> None:
#     indexer.impl.add_entries(resource_id, entries)
#     if update_refs:
#         _update_references(resource_id, [entry_id for (entry_id, _, _) in entries])


def add_entries(
    resource_repo: ResourceRepository,
    indexer: SearchService,
    resource: Resource,
    entries: List[Entry],
    *,
    update_refs: bool = True,
    index_name: Optional[str] = None,
) -> None:
    if not index_name:
        index_name = resource.resource_id
    indexer.add_entries(
        index_name,
        [
            transform_to_index_entry(resource_repo, indexer, resource, entry)
            for entry in entries
        ],
    )
    if update_refs:
        _update_references(resource_repo, indexer, resource, entries)


# def delete_entry(resource_id: str, entry_id: str) -> None:
#     indexer.impl.delete_entry(resource_id, entry_id)
#     _update_references(resource_id, [entry_id])


def _update_references(
    resource_repo: ResourceRepository,
    indexer: SearchService,
    resource: Resource,
    entries: List[Entry],
) -> None:
    add = collections.defaultdict(list)
    with unit_of_work(using=resource_repo) as resources_uw:
        for src_entry in entries:
            refs = network.get_referenced_entries(
                resource_repo, resource, None, src_entry.entry_id
            )
            for field_ref in refs:
                ref_resource_id = field_ref["resource_id"]
                ref_resource = resources_uw.by_resource_id(
                    ref_resource_id, version=(field_ref["resource_version"])
                )

                ref_index_entry = transform_to_index_entry(
                    resource_repo,
                    indexer,
                    ref_resource,
                    field_ref["entry"],
                    # ref_resource.config["fields"].items(),
                )
                # metadata = resourcemgr.get_metadata(ref_resource, field_ref["id"])
                add[ref_resource_id].append(ref_index_entry)
    for ref_resource_id, ref_entries in add.items():
        indexer.add_entries(ref_resource_id, ref_entries)


def transform_to_index_entry(
    resource_repo: ResourceRepository,
    indexer: SearchService,
    resource: Resource,
    src_entry: Entry,
) -> IndexEntry:
    """
    TODO This is very slow (for resources with references) because of db-lookups everywhere in the code
    TODO We can pre-fetch the needed entries (same code that only looks for refs?) or
    TODO somehow get the needed entries in bulk after transforming some entries and insert them into
    TODO the transformed entries afterward. Very tricky.
    """
    print(f"transforming entry_id={src_entry.entry_id}")
    index_entry = indexer.create_empty_object()
    index_entry.id = src_entry.entry_id
    _transform_to_index_entry(
        resource,
        resource_repo,
        indexer,
        src_entry.body,
        index_entry,
        resource.config["fields"].items(),
    )
    return index_entry


def _evaluate_function(
    resource_repo: ResourceRepository,
    indexer: SearchService,
    function_conf: Dict,
    src_entry: Dict,
    src_resource: Resource,
):
    if "multi_ref" in function_conf:
        function_conf = function_conf["multi_ref"]
        target_field = function_conf["field"]
        target_resource = None
        if "resource_id" in function_conf:
            target_resource = resource_repo.by_resource_id(
                function_conf["resource_id"], version=function_conf["resource_version"]
            )
        if target_resource is None:
            target_resource = src_resource

        if "test" in function_conf:
            operator, args = list(function_conf["test"].items())[0]
            if operator in ["equals", "contains"]:
                filters = {"discarded": False}
                for arg in args:
                    if "self" in arg:
                        filters[target_field] = src_entry[arg["self"]]
                    else:
                        raise NotImplementedError()
                # target_entries = entryread.get_entries_by_column(
                #     target_resource, filters
                # )
                with unit_of_work(
                    using=target_resource.entry_repository
                ) as target_entries_uw:
                    target_entries = target_entries_uw.by_referenceable(filters)
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        res = indexer.create_empty_list()
        for entry in target_entries:
            index_entry = indexer.create_empty_object()
            list_of_sub_fields = (("tmp", function_conf["result"]),)
            _transform_to_index_entry(
                target_resource,
                resource_repo,
                indexer,
                {"tmp": entry.body},
                index_entry,
                list_of_sub_fields,
            )
            indexer.add_to_list_field(res, index_entry.entry["tmp"])
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
    resource: Resource,
    resource_repo: ResourceRepository,
    indexer: SearchService,
    _src_entry: Dict,
    _index_entry: IndexEntry,
    fields,
):
    for field_name, field_conf in fields:
        if field_conf.get("virtual"):
            print("found virtual field")
            res = _evaluate_function(
                resource_repo, indexer, field_conf["function"], _src_entry, resource
            )
            print(f"res = {res}")
            if res:
                indexer.assign_field(_index_entry, "v_" + field_name, res)
        elif field_conf.get("ref"):
            ref_field = field_conf["ref"]
            if ref_field.get("resource_id"):
                ref_resource = resource_repo.by_resource_id(
                    ref_field["resource_id"], version=ref_field["resource_version"]
                )
                # if not ref_resource:
                #     raise errors.ResourceNotFoundError(
                #         ref_field["resource_id"], ref_field["resource_version"]
                #     )
                if ref_field["field"].get("collection"):
                    ref_objs = []
                    if ref_resource:
                        for ref_id in _src_entry[field_name]:
                            with unit_of_work(
                                using=ref_resource.entry_repository
                            ) as ref_resource_entries_uw:
                                ref_entry_body = ref_resource_entries_uw.by_entry_id(
                                    str(ref_id)
                                )
                            if ref_entry_body:
                                ref_entry = {field_name: ref_entry_body.body}
                                ref_index_entry = indexer.create_empty_object()
                                list_of_sub_fields = ((field_name, ref_field["field"]),)
                                _transform_to_index_entry(
                                    resource,
                                    resource_repo,
                                    indexer,
                                    ref_entry,
                                    ref_index_entry,
                                    list_of_sub_fields,
                                )
                                ref_objs.append(ref_index_entry.entry[field_name])
                    indexer.assign_field(_index_entry, "v_" + field_name, ref_objs)
                else:
                    raise NotImplementedError()
            else:
                ref_id = _src_entry.get(field_name)
                if not ref_id:
                    continue
                if not ref_field["field"].get("collection", False):
                    ref_id = [ref_id]

                for elem in ref_id:
                    with unit_of_work(
                        using=resource.entry_repository
                    ) as resource_entries_uw:
                        ref = resource_entries_uw.by_entry_id(str(elem))
                    if ref:
                        ref_entry = {field_name: ref.body}
                        ref_index_entry = indexer.create_empty_object()
                        list_of_sub_fields = ((field_name, ref_field["field"]),)
                        _transform_to_index_entry(
                            resource,
                            resource_repo,
                            indexer,
                            ref_entry,
                            ref_index_entry,
                            list_of_sub_fields,
                        )
                        indexer.assign_field(
                            _index_entry,
                            "v_" + field_name,
                            ref_index_entry.entry[field_name],
                        )

        if field_conf["type"] == "object":
            print("found field with type 'object'")
            field_content = indexer.create_empty_object()
            if field_name in _src_entry:
                _transform_to_index_entry(
                    resource,
                    resource_repo,
                    indexer,
                    _src_entry[field_name],
                    field_content,
                    field_conf["fields"].items(),
                )
        else:
            field_content = _src_entry.get(field_name)

        if field_content:
            indexer.assign_field(_index_entry, field_name, field_content)

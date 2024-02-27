import json  # noqa: I001
import logging
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

import elasticsearch
import elasticsearch.helpers  # pyre-ignore
import elasticsearch_dsl as es_dsl  # pyre-ignore
from tatsu import exceptions as tatsu_exc
from tatsu.walkers import NodeWalker

from karp.search.domain import errors, QueryRequest
from karp.lex.domain.entities.entry import Entry
from karp.lex.domain.entities.resource import Resource
from karp.search.domain.query_dsl.karp_query_v6_parser import KarpQueryV6Parser
from karp.search.domain.query_dsl.karp_query_v6_model import (
    KarpQueryV6ModelBuilderSemantics,
)
from .mapping_repo import EsMappingRepository
from .query import EsQuery


logger = logging.getLogger(__name__)


class EsQueryBuilder(NodeWalker):
    def __init__(self, q=None):
        super().__init__()
        self._q = q

    def walk__equals(self, node):
        return self.match(self.walk(node.field), self.walk(node.arg))

    def walk__freetext(self, node):
        return self.match("*", self.walk(node.arg))

    def walk__regexp(self, node):
        return self.regexp(self.walk(node.field), self.walk(node.arg))

    def walk__freergxp(self, node):
        return self.regexp("*", self.walk(node.arg))

    def walk__contains(self, node):
        return self.regexp(self.walk(node.field), f".*{self.walk(node.arg)}.*")

    def walk__startswith(self, node):
        return self.regexp(self.walk(node.field), f"{self.walk(node.arg)}.*")

    def walk__endswith(self, node):
        return self.regexp(self.walk(node.field), f".*{self.walk(node.arg)}")

    def walk__exists(self, node):
        self.no_wildcards("exists", node)
        return es_dsl.Q("exists", field=self.walk(node.field))

    def walk__missing(self, node):
        self.no_wildcards("exists", node)
        return es_dsl.Q("bool", must_not=es_dsl.Q("exists", field=self.walk(node.field)))

    def walk_range(self, node):
        self.no_wildcards(node.op, node)
        return es_dsl.Q(
            "range",
            **{self.walk(node.field): {self.walk(node.op): self.walk(node.arg)}},
        )

    walk__gt = walk_range
    walk__gte = walk_range
    walk__lt = walk_range
    walk__lte = walk_range

    def walk__not(self, node):
        must_nots = [self.walk(expr) for expr in node.exps]
        return es_dsl.Q("bool", must_not=must_nots)

    def walk__or(self, node):
        result = self.walk(node.exps[0])
        for n in node.exps[1:]:
            result = result | self.walk(n)

        return result

    def walk__and(self, node):
        result = self.walk(node.exps[0])
        for n in node.exps[1:]:
            result = result & self.walk(n)

        return result

    def walk_object(self, node):
        return node

    def walk__string_value(self, node):
        return self.walk(node.ast).lower()

    def walk__quoted_string_value(self, node):
        return "".join([part.replace('\\"', '"') for part in node.ast])

    def no_wildcards(self, query, node):
        if "*" in node.field:
            raise errors.IncompleteQuery(
                self._q, f"{query} queries don't support wildcards in field names"
            )

    def regexp(self, field, regexp):
        if "*" in field:
            return es_dsl.Q(
                "query_string",
                query="/" + regexp.replace("/", "\\/") + "/",
                default_field=field,
                lenient=True,
            )
        else:
            return es_dsl.Q("regexp", **{field: regexp})

    def match(self, field, query):
        if "*" in field:
            return es_dsl.Q("multi_match", query=query, fields=[field], lenient=True)
        else:
            return es_dsl.Q(
                "match",
                **{field: {"query": query, "operator": "and"}},
            )


class EsFieldNameCollector(NodeWalker):
    # Return a set of all field names occurring in the given query
    def walk_Node(self, node):
        result = set().union(*(self.walk(child) for child in node.children()))
        # TODO maybe a bit too automagic?
        if hasattr(node, "field"):
            result.add(node.field)
        return result

    def walk_object(self, _obj):
        return set()


class EsSearchService:
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: EsMappingRepository,
    ):
        self.es: elasticsearch.Elasticsearch = es
        self.mapping_repo = mapping_repo
        self.field_name_collector = EsFieldNameCollector()
        self.parser = KarpQueryV6Parser(semantics=KarpQueryV6ModelBuilderSemantics())

    def _format_result(self, resource_ids, response):
        logger.debug("_format_result called", extra={"resource_ids": resource_ids})
        resource_id_map = {
            resource_id: self.mapping_repo.get_name_base(resource_id)
            for resource_id in resource_ids
        }

        def format_entry(entry):
            dict_entry = entry.to_dict()
            version = dict_entry.pop("_entry_version", None)
            last_modified_by = dict_entry.pop("_last_modified_by", None)
            last_modified = dict_entry.pop("_last_modified", None)
            return {
                "id": entry.meta.id,
                "version": version,
                "last_modified": last_modified,
                "last_modified_by": last_modified_by,
                "resource": next(
                    resource
                    for resource, index_base in resource_id_map.items()
                    if entry.meta.index.startswith(index_base)
                ),
                "entry": dict_entry,
            }

        result = {
            "total": response.hits.total,
            "hits": [format_entry(entry) for entry in response],
        }
        return result

    def query(self, request: QueryRequest):
        logger.info("query called", extra={"request": request})
        query = EsQuery.from_query_request(request)
        return self.search_with_query(query)

    def query_split(self, request: QueryRequest):
        logger.info("query_split called", extra={"request": request})
        query = EsQuery.from_query_request(request)
        query.split_results = True
        return self.search_with_query(query)

    def search_with_query(self, query: EsQuery):
        logger.info("search_with_query called", extra={"query": query})
        es_query = None
        field_names = set()
        if query.q:
            try:
                model = self.parser.parse(query.q)
                es_query = EsQueryBuilder(query.q).walk(model)
                field_names = self.field_name_collector.walk(model)
            except tatsu_exc.FailedParse as err:
                logger.info("Parse error", extra={"err": err})
                raise errors.IncompleteQuery(
                    failing_query=query.q, error_description=str(err)
                ) from err
        if query.split_results:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in query.resources:
                s = self.build_search(query, es_query, [resource], field_names)
                ms = ms.add(s)

            responses = ms.execute()
            result: dict[str, Any] = {"total": 0, "hits": {}}
            for i, response in enumerate(responses):
                result["hits"][query.resources[i]] = self._format_result(
                    query.resources, response
                ).get("hits", [])
                result["total"] += response.hits.total
                if query.lexicon_stats:
                    if "distribution" not in result:
                        result["distribution"] = {}
                    result["distribution"][query.resources[i]] = response.hits.total
        else:
            s = self.build_search(query, es_query, query.resources, field_names)
            response = s.execute()

            # TODO format response in a better way, because the whole response takes up too much space in the logs
            # logger.debug('response = {}'.format(response.to_dict()))

            logger.debug("calling _format_result")
            result = self._format_result(query.resources, response)
            if query.lexicon_stats:
                result["distribution"] = {}
                for bucket in response.aggregations.distribution.buckets:
                    key = bucket["key"]
                    result["distribution"][key.rsplit("_", 1)[0]] = bucket["doc_count"]

        return result

    def build_search(self, query, es_query, resources, field_names):
        alias_names = [self.mapping_repo.get_alias_name(resource) for resource in resources]
        s = es_dsl.Search(using=self.es, index=alias_names, doc_type="entry")
        s = self.add_runtime_mappings(s, field_names)
        if es_query is not None:
            s = s.query(es_query)

        s = s[query.from_ : query.from_ + query.size]

        if query.lexicon_stats:
            s.aggs.bucket("distribution", "terms", field="_index", size=len(resources))
        if query.sort:
            s = s.sort(*self.mapping_repo.translate_sort_fields(resources, query.sort))
        elif query.sort_dict:
            sort_fields = []
            for resource, sort in query.sort_dict.items():
                if resource in resources:
                    sort_fields.extend(self.mapping_repo.translate_sort_fields([resource], sort))
            if sort_fields:
                s = s.sort(*sort_fields)
        logger.debug("s = %s", extra={"es_query s": s.to_dict()})
        return s

    def add_runtime_mappings(self, s: es_dsl.Search, field_names: set[str]) -> es_dsl.Search:
        # When a query uses a field of the form "f.length", add a
        # runtime_mapping so it gets interpreted as "the length of the field f".
        mappings = {}
        for field in field_names:
            if field.endswith(".length"):
                base_field = field.removesuffix(".length")
                mappings[field] = {
                    "type": "long",
                    "script": {
                        "source": f"emit(doc.containsKey('{base_field}') ? doc['{base_field}'].length : 0)"
                    },
                }

        # elasticsearch_dsl doesn't know about runtime_mappings so we have to add them 'by hand'
        if mappings:
            s.update_from_dict({"runtime_mappings": mappings})
        return s

    def search_ids(self, resource_id: str, entry_ids: str):
        logger.info(
            "Called EsSearch.search_ids with:",
            extra={"resource_id": resource_id, "entry_ids": entry_ids},
        )
        entries = entry_ids.split(",")
        query = es_dsl.Q("terms", _id=entries)
        logger.debug("query", extra={"query": query})
        alias_name = self.mapping_repo.get_alias_name(resource_id)
        s = es_dsl.Search(using=self.es, index=alias_name).query(query)
        logger.debug("s", extra={"es_query s": s.to_dict()})
        response = s.execute()

        return self._format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str) -> Iterable:
        alias_name = self.mapping_repo.get_alias_name(resource_id)
        s = es_dsl.Search(using=self.es, index=alias_name)
        s = s[:0]
        if (
            field in self.mapping_repo.fields[alias_name]
            and self.mapping_repo.fields[alias_name][field].analyzed
        ):
            field += ".raw"
        logger.debug(
            "Doing aggregations on resource_id: {resource_id}, on field {field}".format(
                resource_id=resource_id, field=field
            )
        )
        s.aggs.bucket("field_values", "terms", field=field, size=2147483647)
        response = s.execute()
        logger.debug("Elasticsearch response", extra={"response": response})
        return [
            {"value": bucket["key"], "count": bucket["doc_count"]}
            for bucket in response.aggregations.field_values.buckets
        ]

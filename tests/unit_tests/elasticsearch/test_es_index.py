from unittest import mock

from karp.infrastructure.elasticsearch6.es_search_index import (
    _create_es_mapping,
    EsSearchIndex,
)

# from karp.elasticsearch.es_observer import OnPublish


def test_create_es_mapping_empty():
    config = {"fields": {}}
    mapping = _create_es_mapping(config)

    assert mapping == {"dynamic": False, "properties": {}}


def test_create_es_mapping_string():
    config = {"fields": {"test": {"type": "string"}}}
    mapping = _create_es_mapping(config)

    assert mapping == {
        "dynamic": False,
        "properties": {
            "test": {"fields": {"raw": {"type": "keyword"}}, "type": "text"}
        },
    }


def test_create_es_mapping_string_skip_raw():
    config = {"fields": {"test": {"type": "string", "skip_raw": True}}}
    mapping = _create_es_mapping(config)

    assert mapping == {
        "dynamic": False,
        "properties": {"test": {"type": "text"}},
    }


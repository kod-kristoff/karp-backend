import json

from karp.elasticsearch.index import _create_es_mapping


def test_places():
    with open('tests/data/config/places.json') as f:
        schema = json.load(f)

    mappings = _create_es_mapping(schema)

    print(repr(mappings))
    assert mappings is not None

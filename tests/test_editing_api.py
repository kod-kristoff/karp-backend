import json
import pytest
import time

import karp.resourcemgr.entryread as entryread


def get_json(client, path):
    response = client.get(path)
    return json.loads(response.data.decode())


def init(client, es_status_code, entries):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    client_with_data = client(use_elasticsearch=True)

    for entry in entries:
        client_with_data.post('places/add',
                              data=json.dumps({'entry': entry}),
                              content_type='application/json')
    return client_with_data


def test_add(es, client_with_data_f):
    client = init(client_with_data_f, es, [])

    client.post('places/add', data=json.dumps({
        'entry': {
            'code': 3,
            'name': 'test3',
            'population': 4,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        }
    }), content_type='application/json')

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'test3'


def test_delete(es, client_with_data_f):
    client = init(client_with_data_f, es, [{
        'code': 3,
        'name': 'test3',
        'population': 4,
        'area': 50000,
        'density': 5,
        'municipality': [2, 3]
    }])

    entries = get_json(client, 'places/query')
    entry_id = entries['hits'][0]['id']

    client.delete('places/%s/delete' % entry_id)

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 0


def test_update(es, client_with_data_f):
    client = init(client_with_data_f, es, [{
        'code': 3,
        'name': 'test3',
        'population': 4,
        'area': 50000,
        'density': 5,
        'municipality': [2, 3]
    }])

    entries = get_json(client, 'places/query')
    entry_id = entries['hits'][0]['id']

    client.post('places/%s/update' % entry_id, data=json.dumps({
        'entry': {
            'code': 3,
            'name': 'test3',
            'population': 5,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        },
        'message': 'changes'
    }), content_type='application/json')

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['id'] == entry_id
    assert entries['hits'][0]['entry']['population'] == 5


def test_refs(es, client_with_data_f):
    client = init(client_with_data_f, es, [
        {
            'code': 1,
            'name': 'test1',
            'population': 10,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        },
        {
            'code': 2,
            'name': 'test2',
            'population': 5,
            'larger_place': 1,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        }
    ])

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 2
    for val in entries['hits']:
        assert 'entry' in val
        entry = val['entry']
        print('entry = {}'.format(entry))
        if entry['code'] == 1:
            assert 'v_larger_place' not in entry
            assert 'larger_place' not in entry
            assert 'v_smaller_places' in entry
            assert entry['v_smaller_places'][0]['code'] == 2
        else:
            assert entry['v_larger_place']['code'] == 1
            assert entry['v_larger_place']['name'] == 'test1'
            assert 'v_smaller_places' not in entry


def test_external_refs(es, client_with_data_f):
    client = init(client_with_data_f, es, [
        {
            'code': 1,
            'name': 'test1',
            'population': 10,
            'area': 50000,
            'density': 5,
            'municipality': [1]
        },
        {
            'code': 2,
            'name': 'test2',
            'population': 5,
            'larger_place': 1,
            'area': 50000,
            'density': 5,
            'municipality': [1, 2]
        },
        {
            'code': 3,
            'name': 'test2',
            'population': 5,
            'larger_place': 1,
            'area': 50000,
            'density': 5,
            'municipality': [2]
        }
    ])

    client.post('municipalities/add',
                data=json.dumps({
                    'entry': {
                        'code': 1,
                        'name': 'municipality1',
                        'state': 'state1',
                        'region': 'region1'
                    }
                }),
                content_type='application/json')

    client.post('municipalities/add',
                data=json.dumps({
                    'entry': {
                        'code': 2,
                        'name': 'municipality2',
                        'state': 'state2',
                        'region': 'region2'
                    }
                }),
                content_type='application/json')

    entries = get_json(client, 'municipalities/query')
    for val in entries['hits']:
        assert 'entry' in val
        entry = val['entry']

        assert 'v_places' in entry
        place_codes = [place['code'] for place in entry['v_places']]
        assert len(place_codes) == 2
        if entry['code'] == 1:
            assert 1 in place_codes
            assert 2 in place_codes
        else:
            assert 2 in place_codes
            assert 3 in place_codes

    places_entries = get_json(client, 'places/query')
    for val in places_entries['hits']:
        assert 'entry' in val
        entry = val['entry']
        assert 'municipality' in entry
        assert isinstance(entry['v_municipality'], list)
        if entry['code'] == 2:
            assert {'code': 1, 'name': 'municipality1', 'state': 'state1'} in entry['v_municipality']
            assert {'code': 2, 'name': 'municipality2', 'state': 'state2'} in entry['v_municipality']


def test_update_refs(es, client_with_data_f):
    client = init(client_with_data_f, es, [
        {
            'code': 5,
            'name': 'test1',
            'population': 10,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        },
        {
            'code': 6,
            'name': 'test2',
            'population': 5,
            'larger_place': 5,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        }
    ])

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 2
    for val in entries['hits']:
        assert 'entry' in val
        entry = val['entry']
        print('entry = {}'.format(entry))
        if entry['code'] == 5:
            assert 'v_smaller_places' in entry
            assert entry['v_smaller_places'][0]['code'] == 6

    client.delete('/places/6/delete')

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 1
    entry = entries['hits'][0]
    assert 'v_smaller_places' not in entry


def test_update_refs2(es, client_with_data_f):
    client = init(client_with_data_f, es, [{
        'code': 3,
        'name': 'test3',
        'municipality': [2, 3]
    }])

    client.post('places/3/update', data=json.dumps({
        'entry': {
            'code': 3,
            'name': 'test3',
            'municipality': [2]
        },
        'message': 'changes'
    }), content_type='application/json')

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['id'] == '3'
    assert entries['hits'][0]['entry']['municipality'] == [2]
    assert 'v_municipality' not in entries['hits'][0] or len(entries['hits'][0]['municipality']) == 0
    with client.application.app_context():
        db_entry = entryread.get_entry('places', '3')
        assert len(db_entry.municipality) == 1
        assert db_entry.municipality[0].municipality == 2

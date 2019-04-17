import json
import pytest
from datetime import datetime, timezone
import time
import re

import karp.resourcemgr.entrywrite as entrywrite

places = [
    {
        'code': 3,
        'name': 'a',
        'municipality': [1]
    },
    {
        'code': 4,
        'name': 'b',
        'municipality': [2, 3]
    },
    {
        'code': 5,
        'name': 'c',
        'municipality': [2, 3],
        'larger_place': 4
    },
    {
        'code': 6,
        'name': 'c',
        'municipality': [1],
        'larger_place': 5
    }
]


def get_helper(client, url):
    response = client.get(url)
    return json.loads(response.data.decode())


@pytest.fixture(scope='module')
def history_data_client(client_with_data_f_scope_module, es):
    if es == 'skip':
        pytest.skip('elasticsearch disabled')
    client = client_with_data_f_scope_module(use_elasticsearch=True)
    with client.application.app_context():
        for entry in places[0:2]:
            entrywrite.add_entry('places', entry, 'user1', message='Add it')
            time.sleep(1)
        for entry in places[2:]:
            entrywrite.add_entry('places', entry, 'user2', message='Add it')
            time.sleep(1)
        for entry in places[0:2]:
            changed_entry = entry.copy()
            changed_entry['name'] = entry['name'] + entry['name']
            entrywrite.update_entry('places', str(entry['code']), 1, changed_entry, 'user2', message='Change it')
            time.sleep(1)
        for entry in places[2:]:
            changed_entry = entry.copy()
            changed_entry['name'] = entry['name'] + entry['name']
            entrywrite.update_entry('places', str(entry['code']), 1, changed_entry, 'user1', message='Change it')
            time.sleep(1)
    return client


def test_empty_user_history(history_data_client):
    response_data = get_helper(history_data_client, 'places/history?user_id=user3')
    assert 0 == len(response_data['history'])


def test_user1_history(history_data_client):
    response_data = get_helper(history_data_client, 'places/history?user_id=user1')
    assert 4 == len(response_data['history'])
    for history_entry in response_data['history']:
        assert 'user1' == history_entry['user_id']


def test_user2_history(history_data_client):
    response_data = get_helper(history_data_client, 'places/history?user_id=user2')
    assert 4 == len(response_data['history'])
    assert 'ADD' == response_data['history'][0]['op']
    assert 'ADD' == response_data['history'][1]['op']
    assert 'UPDATE' == response_data['history'][2]['op']
    assert 'UPDATE' == response_data['history'][3]['op']
    assert re.match(r'^\d{10}\.\d{6}$', str(response_data['history'][3]['timestamp']))
    for history_entry in response_data['history']:
        assert 'user2' == history_entry['user_id']


def test_user_history_from_date(history_data_client):
    response_data = get_helper(history_data_client,
                               'places/history?user_id=user1&from_date=%s' % str(datetime.now(timezone.utc).timestamp() - 5))
    assert 4 > len(response_data['history'])


def test_user_history_to_date(history_data_client):
    response_data = get_helper(history_data_client,
                               'places/history?user_id=user2to_date=%s' % str(datetime.now(timezone.utc).timestamp() - 5))
    assert 4 > len(response_data['history'])


def test_entry_id(history_data_client):
    response_data = get_helper(history_data_client, 'places/history?entry_id=3')
    assert 2 == len(response_data['history'])
    for history_entry in response_data['history']:
        assert '3' == history_entry['entry_id']


def test_entry_id_and_user_id(history_data_client):
    response_data = get_helper(history_data_client, 'places/history?entry_id=3&user_id=user2')
    assert 1 == len(response_data['history'])
    history_entry = response_data['history'][0]
    assert '3' == history_entry['entry_id']
    assert 'user2' == history_entry['user_id']
    assert 'UPDATE' == history_entry['op']


def test_diff_against_nothing(history_data_client):
    response_data = get_helper(history_data_client, 'places/history?entry_id=3&to_version=2')
    assert 1 == len(response_data['history'])
    history_entry = response_data['history'][0]
    assert 'ADD' == history_entry['op']
    for diff in history_entry['diff']:
        assert 'ADDED' == diff['type']


def test_historical_entry(history_data_client):
    response_data = get_helper(history_data_client, 'places/4/2/history')
    assert datetime.now(timezone.utc).timestamp() > response_data['last_modified']
    assert 'user2' == response_data['last_modified_by']
    assert 'id' in response_data
    assert 'resource' in response_data
    assert 'bb' == response_data['entry']['name']
    assert 'version' in response_data

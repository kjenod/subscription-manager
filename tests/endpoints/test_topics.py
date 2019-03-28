"""
Copyright 2019 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the 
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following 
   disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following 
   disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products 
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE 
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open Source Initiative: 
http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""
import json
from unittest import mock

import pytest
from sqlalchemy.exc import IntegrityError

from subscription_manager import BASE_PATH
from subscription_manager.db.topics import get_topic_by_id
from subscription_manager.db.utils import db_save
from tests.utils import make_topic

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def generate_topic():
    def _generate_topic(name):
        topic = make_topic(name)
        return db_save(topic)

    return _generate_topic


def test_get_topic__topic_does_not_exist__returns_404(test_client):
    url = f'{BASE_PATH}/topics/123456'

    response = test_client.get(url)

    assert 404 == response.status_code


def test_get_topic__topic_exists_and_its_data_is_returned(test_client, generate_topic):
    topic = generate_topic('test_topic')

    url = f'{BASE_PATH}/topics/{topic.id}'

    response = test_client.get(url)

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert topic.name == response_data['name']


def test_get_topics__not_topic_exists__empty_list_is_returned(test_client):
    url = f'{BASE_PATH}/topics/'

    response = test_client.get(url)

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert [] == response_data


def test_get_topics__topics_exist_and_are_returned_as_list(test_client, generate_topic):
    topics = [generate_topic('test_topic_1'), generate_topic('test_topic_2')]

    url = f'{BASE_PATH}/topics/'

    response = test_client.get(url)

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert isinstance(response_data, list)
    assert [t.name for t in topics] == [d['name'] for d in response_data]


def test_post_topic__missing_name__returns_400(test_client):
    topic_data = {}

    url = f'{BASE_PATH}/topics/'

    response = test_client.post(url, data=json.dumps(topic_data), content_type='application/json')

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert "'name' is a required property" == response_data['detail']


@mock.patch('subscription_manager.db.topics.create_topic', side_effect=IntegrityError(None, None, None))
def test_post_topic__db_error__returns_409(mock_create_topic, test_client, generate_topic):
    topic_data = {'name': 'test_topic'}

    url = f'{BASE_PATH}/topics/'

    response = test_client.post(url, data=json.dumps(topic_data), content_type='application/json')

    assert 409 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while saving topic in DB" == response_data['detail']


def test_post_topic__topic_is_saved_in_db(test_client):
    topic_data = {'name': 'test_topic'}

    url = f'{BASE_PATH}/topics/'

    response = test_client.post(url, data=json.dumps(topic_data), content_type='application/json')

    assert 201 == response.status_code

    response_data = json.loads(response.data)
    assert 'id' in response_data
    assert isinstance(response_data['id'], int)
    assert topic_data['name'] == response_data['name']

    db_topic = get_topic_by_id(response_data['id'])
    assert db_topic is not None
    assert topic_data['name'] == db_topic.name


@mock.patch('subscription_manager.db.topics.update_topic', side_effect=IntegrityError(None, None, None))
def test_put_topic__db_error__returns_409(mock_update_topic, test_client, generate_topic):
    topic = generate_topic('test_topic')

    topic_data = {'name': 'test_topic'}

    url = f'{BASE_PATH}/topics/{topic.id}'

    response = test_client.put(url, data=json.dumps(topic_data), content_type='application/json')

    assert 409 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while saving topic in DB" == response_data['detail']


def test_put_topic__topic_does_not_exist__returns_404(test_client):
    topic_data = {'active': False}

    url = f'{BASE_PATH}/topics/1234'

    response = test_client.put(url, data=json.dumps(topic_data), content_type='application/json')

    assert 404 == response.status_code

    response_data = json.loads(response.data)
    assert "Topic with id 1234 does not exist" == response_data['detail']


def test_put_topic__topic_is_updated(test_client, generate_topic):
    topic = generate_topic('test_topic')

    topic_data = {'name': 'test_topic'}

    url = f'{BASE_PATH}/topics/{topic.id}'

    response = test_client.put(url, data=json.dumps(topic_data), content_type='application/json')

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert topic_data['name'] == response_data['name']

    db_topic = get_topic_by_id(response_data['id'])
    assert topic_data['name'] == db_topic.name

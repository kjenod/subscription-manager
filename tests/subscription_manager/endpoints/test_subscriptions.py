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

from backend.db import db_save
from subscription_manager import BASE_PATH
from subscription_manager.db.models import QOS
from subscription_manager.db.subscriptions import get_subscription_by_id
from tests.subscription_manager.utils import make_subscription, make_topic

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def generate_topic(session):
    def _generate_topic(name):
        topic = make_topic(name)
        return db_save(session, topic)

    return _generate_topic


@pytest.fixture
def generate_subscription(session):
    def _generate_subscription():
        subscription = make_subscription()
        return db_save(session, subscription)

    return _generate_subscription


def test_get_subscription__subscription_does_not_exist__returns_404(test_client, make_basic_auth_header):
    url = f'{BASE_PATH}/subscriptions/123456'

    response = test_client.get(url, headers=make_basic_auth_header(is_admin=True))

    assert 404 == response.status_code


def test_get_subscription__authorized_user__returns_401(test_client, generate_subscription, make_basic_auth_header):
    subscription = generate_subscription()

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=make_basic_auth_header(authorized=False))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_get_subscription__non_admin_user__returns_403(test_client, generate_subscription, make_basic_auth_header):
    subscription = generate_subscription()

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=make_basic_auth_header(is_admin=False))

    assert 403 == response.status_code

    response_data = json.loads(response.data)
    assert 'Admin rights required' == response_data['detail']


def test_get_subscription__subscription_exists_and_its_data_is_returned(test_client, generate_subscription,
                                                                        make_basic_auth_header):
    subscription = generate_subscription()

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=make_basic_auth_header(is_admin=True))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert subscription.topic.name == response_data['topic']['name']
    assert subscription.queue == response_data['queue']
    assert subscription.active == response_data['active']
    assert subscription.qos.value == response_data['qos']
    assert subscription.durable == response_data['durable']
    assert subscription.id == response_data['id']


def test_get_subscriptions__not_subscription_exists__empty_list_is_returned(test_client, make_basic_auth_header):
    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=make_basic_auth_header(is_admin=True))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert [] == response_data


def test_get_subscriptions__unauthorized_user__returns_401(test_client, generate_subscription, make_basic_auth_header):
    subscriptions = [generate_subscription(), generate_subscription()]

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=make_basic_auth_header(authorized=False))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_get_subscriptions__non_admin_user__returns_401(test_client, generate_subscription, make_basic_auth_header):
    subscriptions = [generate_subscription(), generate_subscription()]

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=make_basic_auth_header(is_admin=False))

    assert 403 == response.status_code

    response_data = json.loads(response.data)
    assert 'Admin rights required' == response_data['detail']


def test_get_subscriptions__subscriptions_exist_and_are_returned_as_list(test_client, generate_subscription,
                                                                         make_basic_auth_header):
    subscriptions = [generate_subscription(), generate_subscription()]

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=make_basic_auth_header(is_admin=True))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert isinstance(response_data, list)
    assert [t.id for t in subscriptions] == [d['id'] for d in response_data]
    assert [t.queue for t in subscriptions] == [d['queue'] for d in response_data]
    assert [t.topic.name for t in subscriptions] == [d['topic']['name'] for d in response_data]
    assert [t.durable for t in subscriptions] == [d['durable'] for d in response_data]
    assert [t.active for t in subscriptions] == [d['active'] for d in response_data]
    assert [t.qos.value for t in subscriptions] == [d['qos'] for d in response_data]


def test_post_subscription__missing_topic_id__returns_400(test_client, make_basic_auth_header):
    subscription_data = {
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=make_basic_auth_header())

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert "'topic_id' is a required property" == response_data['detail']


def test_post_subscription__invalid_qos__returns_400(test_client, generate_topic, make_basic_auth_header):
    topic = generate_topic('test_topic')

    subscription_data = {
        'topic_id': topic.id,
        'active': True,
        'qos': 'invalid',
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=make_basic_auth_header())

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert f"'invalid' is not one of {QOS.all()}" == response_data['detail']


def test_post_subscription__invalid_topic_id__returns_400(test_client, make_basic_auth_header):
    subscription_data = {
        'topic_id': 1234,
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=make_basic_auth_header())

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert f"'topic_id': ['there is no topic with id 1234']" == response_data['detail']


@mock.patch('subscription_manager.db.subscriptions.create_subscription', side_effect=IntegrityError(None, None, None))
def test_post_subscription__db_error__returns_409(mock_create_subscription, test_client, generate_topic,
                                                  make_basic_auth_header):
    topic = generate_topic('test_topic')

    subscription_data = {
        'topic_id': topic.id,
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=make_basic_auth_header())

    assert 409 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while saving subscription in DB" == response_data['detail']


def test_post_subscription__subscription_is_saved_in_db(test_client, generate_topic, make_basic_auth_header):
    topic = generate_topic('test_topic')

    subscription_data = {
        'topic_id': topic.id,
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=make_basic_auth_header())

    assert 201 == response.status_code

    response_data = json.loads(response.data)
    assert 'id' in response_data
    assert isinstance(response_data['id'], int)
    assert 'queue' in response_data
    assert isinstance(response_data['queue'], str)

    assert subscription_data['durable'] == response_data['durable']
    assert subscription_data['active'] == response_data['active']
    assert subscription_data['qos'] == response_data['qos']
    assert subscription_data['topic_id'] == response_data['topic']['id']

    db_subscription = get_subscription_by_id(response_data['id'])
    assert db_subscription is not None
    assert subscription_data['qos'] == db_subscription.qos.value
    assert subscription_data['active'] == db_subscription.active
    assert subscription_data['durable'] == db_subscription.durable
    assert subscription_data['topic_id'] == db_subscription.topic.id


def test_put_subscription__subscription_does_not_exist__returns_404(test_client, make_basic_auth_header):

    subscription_data = {'active': False}

    url = f'{BASE_PATH}/subscriptions/1234'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=make_basic_auth_header())

    assert 404 == response.status_code

    response_data = json.loads(response.data)
    assert "Subscription with id 1234 does not exist" == response_data['detail']


def test_put_subscription__invalid_qos__returns_400(test_client, generate_subscription, make_basic_auth_header):
    subscription = generate_subscription()

    subscription_data = {
        'topic_id': subscription.topic.id,
        'active': True,
        'qos': 'invalid',
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=make_basic_auth_header())

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert f"'invalid' is not one of {QOS.all()}" == response_data['detail']


def test_put_subscription__invalid_topic_id__returns_400(test_client, generate_subscription, make_basic_auth_header):
    subscription = generate_subscription()

    subscription_data = {
        'topic_id': 1234,
    }

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=make_basic_auth_header())

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert f"'topic_id': ['there is no topic with id 1234']" == response_data['detail']


@mock.patch('subscription_manager.db.subscriptions.update_subscription', side_effect=IntegrityError(None, None, None))
def test_put_subscription__db_error__returns_409(mock_update_subscription, test_client, generate_subscription,
                                                 make_basic_auth_header):
    subscription = generate_subscription()

    subscription_data = {'active': not(subscription.active)}

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=make_basic_auth_header())

    assert 409 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while saving subscription in DB" == response_data['detail']


def test_put_subscription__subscription_is_updated(test_client, generate_subscription, make_basic_auth_header):
    subscription = generate_subscription()

    subscription_data = {'active': not(subscription.active)}

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=make_basic_auth_header())

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert subscription_data['active'] == response_data['active']

    db_subscription = get_subscription_by_id(subscription.id)
    assert subscription_data['active'] == db_subscription.active

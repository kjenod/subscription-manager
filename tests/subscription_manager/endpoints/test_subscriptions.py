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
from sqlalchemy.exc import SQLAlchemyError

from swim_backend.db import db_save
from subscription_manager import BASE_PATH
from subscription_manager.broker import broker
from subscription_manager.broker.broker import BrokerError
from subscription_manager.db.models import QOS
from subscription_manager.db.subscriptions import get_subscription_by_id
from tests.conftest import DEFAULT_LOGIN_PASS, basic_auth_header
from tests.subscription_manager.utils import make_subscription, make_topic, make_user, \
    make_basic_auth_header

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def generate_user(session):
    def _generate_user(username, password, is_admin=False):
        user = make_user(username=username, password=password, is_admin=is_admin)
        return db_save(session, user)
    return _generate_user


@pytest.fixture
def generate_topic(session):
    def _generate_topic(name):
        topic = make_topic(name)
        return db_save(session, topic)

    return _generate_topic


@pytest.fixture
def generate_subscription(session):
    def _generate_subscription(topics, user=None, with_broker_queue=False):
        subscription = make_subscription(topics, user=user)
        db_save(session, subscription)

        if with_broker_queue:
            broker.create_queue_for_topics(subscription.queue, subscription.topic_names)

        return subscription
    return _generate_subscription


def test_get_subscription__subscription_does_not_exist__returns_404(test_client, test_user):
    url = f'{BASE_PATH}/subscriptions/123456'

    response = test_client.get(url, headers=basic_auth_header(test_user))

    assert 404 == response.status_code


def test_get_subscription__user_tries_to_get_subscription_of_another_user__returns_404(
        test_client, generate_user, generate_subscription, generate_topic):

    user1 = generate_user('username1', DEFAULT_LOGIN_PASS)
    user2 = generate_user('username2', DEFAULT_LOGIN_PASS)
    subscription = generate_subscription(topics=[generate_topic('topic name')], user=user1)

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=basic_auth_header(user2))

    assert 404 == response.status_code


def test_get_subscription__admin_user_can_get_subscription_of_another_user(test_client, test_user, test_admin_user,
                                                                           generate_subscription, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user)

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=basic_auth_header(test_admin_user))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert subscription.topics[0].name == response_data['topics'][0]['name']
    assert subscription.queue == response_data['queue']
    assert subscription.active == response_data['active']
    assert subscription.qos.value == response_data['qos']
    assert subscription.durable == response_data['durable']
    assert subscription.id == response_data['id']


def test_get_subscription__unauthorized_user__returns_401(test_client, generate_subscription, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')])

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=make_basic_auth_header('fake', 'fake'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_get_subscription__subscription_exists_and_its_data_is_returned(
        test_client, test_user, generate_subscription, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user)

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=basic_auth_header(test_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert subscription.topics[0].name == response_data['topics'][0]['name']
    assert subscription.queue == response_data['queue']
    assert subscription.active == response_data['active']
    assert subscription.qos.value == response_data['qos']
    assert subscription.durable == response_data['durable']
    assert subscription.id == response_data['id']


def test_get_subscriptions__no_subscription_exists_for_user__empty_list_is_returned(
        test_client, generate_user, generate_subscription, generate_topic):

    user1 = generate_user('username1', DEFAULT_LOGIN_PASS)
    user2 = generate_user('username2', DEFAULT_LOGIN_PASS)
    generate_subscription(topics=[generate_topic('topic name')], user=user1)

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=basic_auth_header(user2))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert [] == response_data


def test_get_subscriptions__admin_user_can_get_all_existing_subscriptions(
        test_client, test_admin_user, generate_user, generate_subscription, generate_topic):
    topic = generate_topic('topic name')
    generate_subscription(topics=[topic])
    generate_subscription(topics=[topic])

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=basic_auth_header(test_admin_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert 2 == len(response_data)


def test_get_subscriptions__unauthorized_user__returns_401(test_client):
    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_get_subscriptions__filter_by_queue(test_client, test_user, generate_subscription, generate_topic):
    topic = generate_topic('topic name')
    subscriptions = [generate_subscription(topics=[topic], user=test_user),
                     generate_subscription(topics=[topic], user=test_user)]

    url = f'{BASE_PATH}/subscriptions/?queue={subscriptions[0].queue}'

    response = test_client.get(url, headers=basic_auth_header(test_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert isinstance(response_data, list)
    assert 1 == len(response_data)
    assert subscriptions[0].queue == response_data[0]['queue']


def test_get_subscriptions__subscriptions_exist_and_are_returned_as_list(
        test_client, test_user, generate_subscription, generate_topic):

    topic = generate_topic('topic name')
    subscriptions = [generate_subscription(topics=[topic], user=test_user),
                     generate_subscription(topics=[topic], user=test_user)]

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.get(url, headers=basic_auth_header(test_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert isinstance(response_data, list)
    assert [s.id for s in subscriptions] == [d['id'] for d in response_data]
    assert [s.queue for s in subscriptions] == [d['queue'] for d in response_data]
    assert [s.topics[0].name for s in subscriptions] == [d['topics'][0]['name'] for d in response_data]
    assert [s.durable for s in subscriptions] == [d['durable'] for d in response_data]
    assert [s.active for s in subscriptions] == [d['active'] for d in response_data]
    assert [s.qos.value for s in subscriptions] == [d['qos'] for d in response_data]


@pytest.mark.parametrize('topics, expected_error_message', [
    ([], "{'topics': ['No topics were provided']}"),
    (['invalid topic'], """{'topics': ["No topic found with name 'invalid topic'"]}""")
])
def test_post_subscription__invalid_topics__returns_400(test_client, test_user, topics, expected_error_message):
    subscription_data = {
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True,
        'topics': topics
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=basic_auth_header(test_user))

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert expected_error_message == response_data['detail']


def test_post_subscription__invalid_qos__returns_400(test_client, generate_topic, test_user):
    topic = generate_topic('test_topic')

    subscription_data = {
        'topics': [topic.name],
        'active': True,
        'qos': 'invalid',
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=basic_auth_header(test_user))

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert f"'invalid' is not one of {QOS.all()}" == response_data['detail']


@mock.patch('subscription_manager.db.subscriptions.create_subscription', side_effect=SQLAlchemyError(None, None, None))
def test_post_subscription__db_error__returns_500(mock_create_subscription, test_client, generate_topic, test_user):
    topic = generate_topic('test_topic')

    subscription_data = {
        'topics': [topic.name],
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=basic_auth_header(test_user))

    assert 500 == response.status_code


@mock.patch('subscription_manager.broker.broker.create_queue_for_topics', side_effect=BrokerError('error'))
def test_post_subscription__broker_error__returns_502(mock_queue_for_topic, test_client, generate_topic, test_user):
    topic = generate_topic('test_topic')

    subscription_data = {
        'topics': [topic.name],
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=basic_auth_header(test_user))

    assert 502 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while accessing the broker: error" == response_data['detail']


def test_post_subscription__unauthorized_user__returns_401(test_client, generate_topic):
    topic = generate_topic('test_topic')

    subscription_data = {
        'topics': [topic.name],
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


@mock.patch('subscription_manager.broker.broker.broker_client')
def test_post_subscription__subscription_is_saved_in_db(mock_broker_client, test_client, generate_topic, test_user):
    mock_broker_client.create_queue_for_topic = mock.Mock(return_value=None)

    topic = generate_topic('test_topic')

    subscription_data = {
        'topics': [topic.name],
        'active': True,
        'qos': QOS.EXACTLY_ONCE.value,
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/'

    response = test_client.post(url, data=json.dumps(subscription_data), content_type='application/json',
                                headers=basic_auth_header(test_user))

    assert 201 == response.status_code

    response_data = json.loads(response.data)
    assert 'id' in response_data
    assert isinstance(response_data['id'], int)
    assert 'queue' in response_data
    assert isinstance(response_data['queue'], str)

    assert subscription_data['durable'] == response_data['durable']
    assert subscription_data['active'] == response_data['active']
    assert subscription_data['qos'] == response_data['qos']
    assert subscription_data['topics'][0] == response_data['topics'][0]['name']

    db_subscription = get_subscription_by_id(response_data['id'])
    assert db_subscription is not None
    assert subscription_data['qos'] == db_subscription.qos.value
    assert subscription_data['active'] == db_subscription.active
    assert subscription_data['durable'] == db_subscription.durable
    assert subscription_data['topics'][0] == db_subscription.topics[0].name

    broker.delete_queue(response_data['queue'])


def test_put_subscription__subscription_does_not_exist__returns_404(test_client, test_user):
    subscription_data = {'active': False}

    url = f'{BASE_PATH}/subscriptions/1234'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=basic_auth_header(test_user))

    assert 404 == response.status_code

    response_data = json.loads(response.data)
    assert "Subscription with id 1234 does not exist" == response_data['detail']


def test_put_subscription__invalid_qos__returns_400(test_client, test_user, generate_subscription, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic_name')], user=test_user)

    subscription_data = {
        'topics': [subscription.topics[0].name],
        'active': True,
        'qos': 'invalid',
        'durable': True
    }

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=basic_auth_header(test_user))

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert f"'invalid' is not one of {QOS.all()}" == response_data['detail']


def test_put_subscription__invalid_topic_id__returns_400(test_client, test_user, generate_subscription, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user)

    subscription_data = {
        'topics': ['invalid topic'],
    }

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=basic_auth_header(test_user))

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert '{\'topics\': ["No topic found with name \'invalid topic\'"]}' == response_data['detail']


@mock.patch('subscription_manager.broker.broker.delete_queue_binding', return_value=None)
@mock.patch('subscription_manager.broker.broker.bind_queue_to_topic', return_value=None)
@mock.patch('subscription_manager.db.subscriptions.update_subscription', side_effect=SQLAlchemyError(None, None, None))
def test_put_subscription__db_error__returns_500(mock_update_subscription, mock_bind_queue_to_topic,
                                                 mock_delete_queue_binding, test_client, generate_subscription,
                                                 test_user, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user)

    subscription_data = {'active': not subscription.active}

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=basic_auth_header(test_user))

    assert 500 == response.status_code


@mock.patch('subscription_manager.broker.broker.delete_queue_binding', side_effect=BrokerError('error'))
@mock.patch('subscription_manager.broker.broker.bind_queue_to_topic', side_effect=BrokerError('error'))
def test_put_subscription__broker_error__returns_502(mock_bind_queue_to_topic, mock_delete_queue_binding, test_client,
                                                     generate_subscription, test_user, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user)

    subscription_data = {'active': not subscription.active}

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=basic_auth_header(test_user))

    assert 502 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while accessing broker: error" == response_data['detail']


def test_put_subscription__unauthorized_user_returns_401(test_client, generate_subscription, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')])

    subscription_data = {'active': not subscription.active}

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


@mock.patch('subscription_manager.broker.broker.broker_client')
def test_put_subscription__admin_user_can_update_any_subscription(mock_broker_client, test_client, test_user,
                                                                  test_admin_user, generate_subscription,
                                                                  generate_topic):
    mock_broker_client.bind_queue_to_topic = mock.Mock(return_value=None)
    mock_broker_client.delete_queue_binding = mock.Mock(return_value=None)

    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user, with_broker_queue=True)

    subscription_data = {'active': not subscription.active}

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=make_basic_auth_header(test_admin_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert subscription_data['active'] == response_data['active']

    db_subscription = get_subscription_by_id(subscription.id)
    assert subscription_data['active'] == db_subscription.active

    # remove the queue from the broker
    broker.delete_queue(subscription.queue)


@mock.patch('subscription_manager.broker.broker.broker_client')
def test_put_subscription__subscription_is_updated_in_db_and_broker(mock_broker_client, test_client,
                                                                    generate_subscription, test_user, generate_topic):
    mock_broker_client.bind_queue_to_topic = mock.Mock(return_value=None)
    mock_broker_client.delete_queue_binding = mock.Mock(return_value=None)

    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user, with_broker_queue=True)

    subscription_data = {'active': not subscription.active}

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.put(url, data=json.dumps(subscription_data), content_type='application/json',
                               headers=basic_auth_header(test_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert subscription_data['active'] == response_data['active']

    db_subscription = get_subscription_by_id(subscription.id)
    assert subscription_data['active'] == db_subscription.active

    # remove the queue from the broker
    broker.delete_queue(subscription.queue)


def test_delete_subscription__subscription_does_not_exist__returns_404(test_client, test_user):

    url = f'{BASE_PATH}/subscriptions/123456'

    response = test_client.get(url, headers=basic_auth_header(test_user))

    assert 404 == response.status_code


def test_delete_subscription__unauthorized_user__returns_401(test_client, generate_subscription, generate_topic):
    subscription = generate_subscription(topics=[generate_topic('topic name')])

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.get(url, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


@mock.patch('subscription_manager.broker.broker.broker_client')
def test_delete_subscription__admin_user_can_delete_any_subscription(mock_broker_client, test_client, test_user,
                                                                     test_admin_user, generate_subscription,
                                                                     generate_topic):
    mock_broker_client.delete_queue_binding = mock.Mock(return_value=None)

    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user, with_broker_queue=True)

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.delete(url, headers=basic_auth_header(test_admin_user))

    assert 204 == response.status_code

    # check that the subscription has been deleted from db
    response = test_client.get(url, headers=basic_auth_header(test_user))
    assert 404 == response.status_code


@mock.patch('subscription_manager.broker.broker.broker_client')
def test_delete_subscription__subscription_is_deleted_and_returns_204(mock_broker_client, test_client,
                                                                      generate_subscription, test_user, generate_topic):
    mock_broker_client.delete_queue_binding = mock.Mock(return_value=None)

    subscription = generate_subscription(topics=[generate_topic('topic name')], user=test_user, with_broker_queue=True)

    url = f'{BASE_PATH}/subscriptions/{subscription.id}'

    response = test_client.delete(url, headers=basic_auth_header(test_user))

    assert 204 == response.status_code

    # check that the subscription has been deleted from db
    response = test_client.get(url, headers=basic_auth_header(test_user))
    assert 404 == response.status_code

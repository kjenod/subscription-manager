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
from werkzeug.security import check_password_hash

from subscription_manager import BASE_PATH
from swim_backend.auth import HASH_METHOD
from swim_backend.db import db_save
from subscription_manager.db.users import get_user_by_id
from tests.subscription_manager.utils import make_user, make_basic_auth_header
from tests.conftest import DEFAULT_LOGIN_PASSWORD

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def generate_user(session):
    def _generate_user(is_admin=False):
        user = make_user(is_admin=is_admin)
        return db_save(session, user)

    return _generate_user


def basic_auth_header(user):
    return make_basic_auth_header(user.username, DEFAULT_LOGIN_PASSWORD)


def test_get_user__user_does_not_exist__returns_404(test_client, test_admin_user):
    url = f'{BASE_PATH}/users/123456'

    response = test_client.get(url, headers=basic_auth_header(test_admin_user))

    assert 404 == response.status_code


def test_get_user__unauthorized_user__returns_401(test_client, generate_user):
    user = generate_user()
    user.password = 'password'

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.get(url, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_get_user__non_admin_user__returns_403(test_client, generate_user):
    user = generate_user(is_admin=False)

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.get(url, headers=make_basic_auth_header(user.username, 'password'))

    assert 403 == response.status_code

    response_data = json.loads(response.data)
    assert 'Admin rights required' == response_data['detail']


def test_get_user__user_exists_and_is_returned(test_client, generate_user, test_admin_user):
    user = generate_user()

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.get(url, headers=basic_auth_header(test_admin_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert user.username == response_data['username']
    assert user.active == response_data['active']
    assert user.is_admin == response_data['is_admin']


def test_get_users__unauthorized_user__returns_401(test_client, generate_user):
    users = [generate_user(), generate_user()]

    url = f'{BASE_PATH}/users/'

    response = test_client.get(url, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_get_users__non_admin_user__returns_403(test_client, generate_user, test_user):
    users = [generate_user(), generate_user()]

    url = f'{BASE_PATH}/users/'

    response = test_client.get(url, headers=basic_auth_header(test_user))

    assert 403 == response.status_code

    response_data = json.loads(response.data)
    assert 'Admin rights required' == response_data['detail']


def test_get_users__users_exist_and_are_returned_as_list(test_client, generate_user, test_admin_user):
    users = [generate_user(), generate_user()]

    url = f'{BASE_PATH}/users/'

    response = test_client.get(url, headers=basic_auth_header(test_admin_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert isinstance(response_data, list)
    assert 3 == len(response_data)  # plus the test_user


@pytest.mark.parametrize('missing_property', ['username', 'password'])
def test_post_user__missing_required_property__returns_400(test_client, missing_property, test_admin_user):
    user_data = {
        'username': 'username',
        'password': 'password'
    }

    del user_data[missing_property]

    url = f'{BASE_PATH}/users/'

    response = test_client.post(url, data=json.dumps(user_data), content_type='application/json',
                                headers=basic_auth_header(test_admin_user))

    assert 400 == response.status_code

    response_data = json.loads(response.data)
    assert f"'{missing_property}' is a required property" == response_data['detail']


@mock.patch('subscription_manager.db.users.save_user', side_effect=IntegrityError(None, None, None))
def test_post_user__db_error__returns_409(mock_create_user, test_client, generate_user, test_admin_user):
    user_data = {
        'username': 'username',
        'password': 'password'
    }

    url = f'{BASE_PATH}/users/'

    response = test_client.post(url, data=json.dumps(user_data), content_type='application/json',
                                headers=basic_auth_header(test_admin_user))

    assert 409 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while saving user in DB" == response_data['detail']


def test_post_user__unauthorized_user__returns_401(test_client):
    user_data = {
        'username': 'username',
        'password': 'password'
    }

    url = f'{BASE_PATH}/users/'

    response = test_client.post(url, data=json.dumps(user_data), content_type='application/json',
                                headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_post_user__non_admin_user__returns_403(test_client, test_user):
    user_data = {
        'username': 'username',
        'password': 'password'
    }

    url = f'{BASE_PATH}/users/'

    response = test_client.post(url, data=json.dumps(user_data), content_type='application/json',
                                headers=basic_auth_header(test_user))

    assert 403 == response.status_code

    response_data = json.loads(response.data)
    assert 'Admin rights required' == response_data['detail']


def test_post_user__user_is_saved_in_db(test_client, test_admin_user):
    user_data = {
        'username': 'username',
        'password': 'password'
    }

    url = f'{BASE_PATH}/users/'

    response = test_client.post(url, data=json.dumps(user_data), content_type='application/json',
                                headers=basic_auth_header(test_admin_user))

    assert 201 == response.status_code

    response_data = json.loads(response.data)
    assert 'id' in response_data
    assert isinstance(response_data['id'], int)
    assert user_data['username'] == response_data['username']

    db_user = get_user_by_id(response_data['id'])
    assert db_user is not None
    assert user_data['username'] == db_user.username
    assert db_user.password.startswith(HASH_METHOD)
    assert check_password_hash(db_user.password, 'password') is True


@mock.patch('subscription_manager.db.users.save_user', side_effect=IntegrityError(None, None, None))
def test_put_user__db_error__returns_409(mock_update_user, test_client, generate_user, test_admin_user):
    user = generate_user()

    user_data = {
        'username': 'username',
        'password': 'password'
    }

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.put(url, data=json.dumps(user_data), content_type='application/json',
                               headers=basic_auth_header(test_admin_user))

    assert 409 == response.status_code
    response_data = json.loads(response.data)
    assert "Error while saving user in DB" == response_data['detail']


def test_put_user__user_does_not_exist__returns_404(test_client, test_admin_user):
    user_data = {
        'username': 'username',
        'password': 'password'
    }

    url = f'{BASE_PATH}/users/1234'

    response = test_client.put(url, data=json.dumps(user_data), content_type='application/json',
                               headers=basic_auth_header(test_admin_user))

    assert 404 == response.status_code

    response_data = json.loads(response.data)
    assert "User with id 1234 does not exist" == response_data['detail']


def test_put_user__unauthorized_user__returns_401(test_client, generate_user):
    user = generate_user()

    user_data = {
        'username': 'new username',
    }

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.put(url, data=json.dumps(user_data), content_type='application/json',
                               headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code

    response_data = json.loads(response.data)
    assert 'Invalid credentials' == response_data['detail']


def test_put_user__non_admin_user__returns_403(test_client, generate_user, test_user):
    user = generate_user()

    user_data = {
        'username': 'new username',
    }

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.put(url, data=json.dumps(user_data), content_type='application/json',
                               headers=basic_auth_header(test_user))

    assert 403 == response.status_code

    response_data = json.loads(response.data)
    assert 'Admin rights required' == response_data['detail']


def test_put_user__user_is_updated(test_client, generate_user, test_admin_user):
    user = generate_user()

    user_data = {
        'username': 'new username',
    }

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.put(url, data=json.dumps(user_data), content_type='application/json',
                               headers=basic_auth_header(test_admin_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)
    assert user_data['username'] == response_data['username']

    db_user = get_user_by_id(response_data['id'])
    assert user_data['username'] == db_user.username


def test_put_user__new_password_is_updated_and_hashed_correctly(test_client, generate_user, test_admin_user):
    user = generate_user()

    user_data = {
        'password': 'new password',
    }

    url = f'{BASE_PATH}/users/{user.id}'

    response = test_client.put(url, data=json.dumps(user_data), content_type='application/json',
                               headers=basic_auth_header(test_admin_user))

    assert 200 == response.status_code

    response_data = json.loads(response.data)

    db_user = get_user_by_id(response_data['id'])

    assert db_user.password.startswith(HASH_METHOD)
    assert check_password_hash(db_user.password, 'new password') is True

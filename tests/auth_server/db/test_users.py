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
import pytest

from backend.db import db_save
from auth_server.db import User
from auth_server.db.users import get_user_by_id, get_users, save_user, get_user_by_username
from tests.auth_server.utils import make_user

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def generate_user(session):
    def _generate_user():
        user = make_user()
        return db_save(session, user)

    return _generate_user


def test_get_user_by_id__does_not_exist__returns_none():
    assert get_user_by_id(1111) is None


def test_get_user_by_id__object_exists_and_is_returned(generate_user):
    user = generate_user()

    db_user = get_user_by_id(user.id)

    assert isinstance(db_user, User)
    assert user == db_user


def test_get_user_by_username__does_not_exist__returns_none():
    assert get_user_by_username('invalid') is None


def test_get_user_by_username__object_exists_and_is_returned(generate_user):
    user = generate_user()

    db_user = get_user_by_username(user.username)

    assert isinstance(db_user, User)
    assert user == db_user


def test_get_users__no_user_in_db__returns_empty_list(generate_user):
    db_users = get_users()

    assert [] == db_users


def test_get_users__existing_users_are_returned(generate_user):
    users = [generate_user(), generate_user()]

    db_users = get_users()

    assert 2 == len(db_users)
    assert users == db_users


def test_create_user():
    user = make_user()
    user.password = 'password'

    db_user = save_user(user)

    assert isinstance(db_user, User)
    assert isinstance(db_user.id, int)
    assert user.username == db_user.username
    assert user.password == db_user.password
    assert user.active == db_user.active
    assert user.created_at == db_user.created_at


def test_update_user(generate_user):
    user = generate_user()

    user.username = 'new username'

    updated_user = save_user(user)

    assert isinstance(updated_user, User)
    assert 'new username' == updated_user.username

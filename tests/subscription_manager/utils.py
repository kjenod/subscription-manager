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
from base64 import b64encode
from uuid import uuid4

from swim_backend.auth.auth import hash_password
from subscription_manager.db import Topic, Subscription, User

__author__ = "EUROCONTROL (SWIM)"


def unique_id():
    return uuid4().hex


def make_topic(name='test_topic', user=None) -> Topic:
    return Topic(
        name=name,
        user = user or make_user()
    )


def make_subscription(topic=None, user=None) -> Subscription:
    return Subscription(
        topic=topic or make_topic(name=unique_id()),
        user=user or make_user(),
        queue=unique_id()
    )


def make_user(username: str = 'username', password: str = 'password', is_admin: bool = False) -> User:
    """

    :param username:
    :param password:
    :param is_admin:
    :return:
    """
    return User(
        username=(username + uuid4().hex)[:50],
        password=hash_password(password),
        is_admin=is_admin
    )


def make_basic_auth_header(username, password):
    basic_auth_str = b64encode(bytes(f'{username}:{password}', 'utf-8'))

    result = {'Authorization': f"Basic {basic_auth_str.decode('utf-8')}"}

    return result

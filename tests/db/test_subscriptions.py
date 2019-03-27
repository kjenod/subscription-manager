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

from subscription_manager.db import Subscription
from subscription_manager.db.subscriptions import get_subscription_by_id, get_subscriptions, create_subscription, update_subscription
from subscription_manager.db.utils import db_save
from tests.utils import make_subscription

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def generate_subscription():
    def _generate_subscription():
        subscription = make_subscription()
        return db_save(subscription)

    return _generate_subscription


def test_get_subscription_by_id__does_not_exist__returns_none():
    assert get_subscription_by_id(1111) is None


def test_get_subscription_by_id__object_exists_and_is_returned(generate_subscription):
    subscription = generate_subscription()

    db_subscription = get_subscription_by_id(subscription.id)

    assert isinstance(db_subscription, Subscription)
    assert subscription.id == db_subscription.id


def test_get_subscriptions__no_subscription_in_db__returns_empty_list(generate_subscription):
    db_subscriptions = get_subscriptions()

    assert [] == db_subscriptions


def test_get_subscriptions__existing_subscriptions_are_returned(generate_subscription):
    subscriptions = [generate_subscription(), generate_subscription()]

    db_subscriptions = get_subscriptions()

    assert 2 == len(db_subscriptions)
    assert subscriptions == db_subscriptions


def test_create_subscription():
    subscription = make_subscription()

    db_subscription = create_subscription(subscription)

    assert isinstance(db_subscription, Subscription)
    assert isinstance(db_subscription.id, int)
    assert subscription.topic == db_subscription.topic
    assert subscription.queue == db_subscription.queue
    assert subscription.active == db_subscription.active
    assert subscription.qos == db_subscription.qos
    assert subscription.durable == db_subscription.durable


def test_update_subscription(generate_subscription):
    subscription = generate_subscription()

    new_active = not(subscription.active)
    subscription.active = new_active

    updated_subscription = update_subscription(subscription)

    assert isinstance(updated_subscription, Subscription)
    assert new_active == updated_subscription.active

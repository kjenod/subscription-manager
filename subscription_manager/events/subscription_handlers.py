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

from subscription_manager.broker import broker
from subscription_manager.db import subscriptions as db
from subscription_manager.db.utils import generate_queue

__author__ = "EUROCONTROL (SWIM)"


def create_subscription_handler(subscription):
    subscription.queue = generate_queue()

    db.create_subscription(subscription)

    broker.create_queue_for_topic(subscription.queue, subscription.topic.name)


def update_subscription_handler(current_subscription, updated_subscription):
    if current_subscription.active != updated_subscription.active:
        if not updated_subscription.active:
            broker.delete_queue_binding(queue=updated_subscription.queue,
                                        topic=updated_subscription.topic.name)
        else:
            broker.bind_queue_to_topic(queue=updated_subscription.queue,
                                       topic=updated_subscription.topic.name,
                                       durable=updated_subscription.durable)

    db.update_subscription(updated_subscription)


def delete_subscription_handler(subscription):
    broker.delete_queue(subscription.queue)
    db.delete_subscription(subscription)

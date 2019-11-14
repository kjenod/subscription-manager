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
from swim_backend.events import Event
from swim_backend.local import LazyProxy
from subscription_manager.events.subscription_handlers import create_subscription_handler, update_subscription_handler,\
    delete_subscription_handler
from subscription_manager.events.topic_handlers import create_topic_handler, delete_topic_handler, \
    delete_topic_subscriptions_handler

__author__ = "EUROCONTROL (SWIM)"


class CreateTopicEvent(Event):
    _type = 'Create topic'


class DeleteTopicEvent(Event):
    _type = 'Delete topic'


class CreateSubscription(Event):
    _type = 'Create subscription'


class UpdateSubscription(Event):
    _type = 'Update subscription'


class DeleteSubscription(Event):
    _type = 'Delete subscription'


# ############
# Topic events
# ############

create_topic_event = LazyProxy(lambda: CreateTopicEvent())
create_topic_event.append(create_topic_handler)

delete_topic_event = LazyProxy(lambda: DeleteTopicEvent())
delete_topic_event.append(delete_topic_subscriptions_handler)
delete_topic_event.append(delete_topic_handler)


# ###################
# Subscription events
# ###################

create_subscription_event = LazyProxy(lambda: CreateSubscription())
create_subscription_event.append(create_subscription_handler)

update_subscription_event = LazyProxy(lambda: UpdateSubscription())
update_subscription_event.append(update_subscription_handler)

delete_subscription_event = LazyProxy(lambda: DeleteSubscription())
delete_subscription_event.append(delete_subscription_handler)

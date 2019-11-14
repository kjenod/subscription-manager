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

from marshmallow import post_dump, ValidationError, pre_dump, pre_load, post_load
from marshmallow.fields import Nested, Integer, List, String
from marshmallow_sqlalchemy import ModelSchemaOpts, ModelSchema

from swim_backend.db import db
from subscription_manager.db.models import Topic, Subscription, User
from subscription_manager.db.topics import get_topic_by_id, get_topic_by_name

__author__ = "EUROCONTROL (SWIM)"


class BaseOpts(ModelSchemaOpts):
    def __init__(self, meta, ordered):
        if not hasattr(meta, 'sql_session'):
                meta.sqla_session = db.session
        if not hasattr(meta, 'include_fk'):
            meta.include_fk = True
        super(BaseOpts, self).__init__(meta)


class BaseSchema(ModelSchema):
    OPTIONS_CLASS = BaseOpts


class TopicSchema(BaseSchema):

    class Meta:
        model = Topic
        load_only = ("user", "user_id", "subscriptions")
        # dump_only = ("id",)

    user_id = Integer(required=False)


class SubscriptionSchema(BaseSchema):

    class Meta:
        model = Subscription
        load_only = ("user", "user_id")
        dump_only = ("id", "queue")

    topics = Nested(TopicSchema, many=True)
    user_id = Integer(required=False)

    @post_dump
    def serialize_qos(self, subscription_data, **kwargs):
        subscription_data['qos'] = subscription_data['qos'].value

        return subscription_data


class SubscriptionPostSchema(BaseSchema):

    class Meta:
        model = Subscription
        dump_only = ("id", "queue", "user_id")

    topics = Nested(TopicSchema, many=True)

    @staticmethod
    def _validate_topic_exists(topic_name):
        topic = get_topic_by_name(topic_name)

        if topic is None:
            raise ValidationError(f"No topic found with name '{topic_name}'", field_name='topics')

        return {'name': topic_name}

    def _handle_topics(self, data, **kwargs):
        if not data['topics']:
            raise ValidationError(f"No topics were provided", field_name='topics')

        data['topics'] = [self._validate_topic_exists(topic_name) for topic_name in data['topics']]

        return data

    @pre_load
    def handle_topics(self, data, **kwargs):
        return self._handle_topics(data, **kwargs)

    @post_load
    def post(self, item, **kwargs):
        item.topics = [get_topic_by_name(topic.name) for topic in item.topics]

        return item


class SubscriptionPutSchema(SubscriptionPostSchema):
    def _handle_topics(self, data, **kwargs):
        if data.get('topics'):
            data['topics'] = [self._validate_topic_exists(topic_name) for topic_name in data['topics']]

        return data


class UserSchema(BaseSchema):

    class Meta:
        model = User
        load_only = ("password",)
        dump_only = ("id",)
        exclude = ('topics', 'subscriptions',)
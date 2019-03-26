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
from functools import wraps

from marshmallow import post_load, post_dump, ValidationError
from marshmallow.fields import Nested, String
from marshmallow_sqlalchemy import ModelSchemaOpts, ModelSchema

from subscription_manager.db import db
from subscription_manager.db.models import Topic, Subscription, QOS

__author__ = "EUROCONTROL (SWIM)"

class BaseOpts(ModelSchemaOpts):
    def __init__(self, meta):
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
        dump_only = ("id",)


def validate_qos(qos):
    all_qos = QOS.all()

    if qos not in all_qos:
        raise ValidationError(f"qos should be one of {all_qos}")


class SubscriptionSchema(BaseSchema):

    class Meta:
        model = Subscription
        load_only = ("topic_id",)
        dump_only = ("id", "queue", "topic")

    qos = String(validate=validate_qos, required=True)
    topic = Nested(TopicSchema)

    @post_dump
    def serialize_qos(self, subscription_data):
        qos_model_name, qos_property = subscription_data['qos'].split(".")

        subscription_data['qos'] = qos_property

        return subscription_data


def unmarshal(schema_class, data, instance=None):
    object, errors = schema_class().load(data, instance=instance)
    if errors:
        raise ValidationError(", ".join(list(errors.values())[0]))

    return object


def marshal_with(schema_class, many=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            marshaled_result = schema_class(many=many).dump(result).data

            return marshaled_result
        return wrapper
    return decorator

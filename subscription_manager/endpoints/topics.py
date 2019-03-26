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
from sqlalchemy.exc import IntegrityError

from subscription_manager.base.errors import NotFoundError, ConflictError
from subscription_manager.db.topics import get_topics as db_get_topics, get_topic_by_id as db_get_topic_by_id, \
    create_topic, update_topic
from subscription_manager.endpoints.schemas import TopicSchema, marshal_with

__author__ = "EUROCONTROL (SWIM)"


@marshal_with(TopicSchema, many=True)
def get_topics():
    return db_get_topics()


@marshal_with(TopicSchema)
def get_topic(topic_id):
    result = db_get_topic_by_id(topic_id)

    if result is None:
        raise NotFoundError(f"Topic with id {topic_id} does not exist")

    return result


@marshal_with(TopicSchema)
def post_topic(topic_data):
    topic = TopicSchema().load(topic_data).data

    try:
        topic_created = create_topic(topic)
    except IntegrityError:
        raise ConflictError("Error while saving topic in DB")

    return topic_created


@marshal_with(TopicSchema)
def put_topic(topic_id, topic_data):
    topic = db_get_topic_by_id(topic_id)

    if topic is None:
        raise NotFoundError(f"Topic with id {topic_id} does not exist")

    topic = TopicSchema().load(topic_data, instance=topic).data

    try:
        topic_updated = update_topic(topic)
    except IntegrityError:
        raise ConflictError("Error while saving topic in DB")

    return topic_updated

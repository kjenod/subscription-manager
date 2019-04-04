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
import typing as t
from flask import request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from backend.auth import admin_required
from backend.errors import NotFoundError, ConflictError, BadRequestError
from backend.typing import JSONType
from subscription_manager.db import topics as db
from subscription_manager.endpoints.schemas import TopicSchema
from backend.marshal import unmarshal, marshal_with

__author__ = "EUROCONTROL (SWIM)"


@admin_required
@marshal_with(TopicSchema, many=True)
def get_topics() -> JSONType:
    """
    GET /topics/

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
    """

    return db.get_topics()


@admin_required
@marshal_with(TopicSchema)
def get_topic(topic_id: int) -> JSONType:
    """
    GET /topic/{topic_id}

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.NotFoundError (HTTP error 404)
    """

    result = db.get_topic_by_id(topic_id)

    if result is None:
        raise NotFoundError(f"Topic with id {topic_id} does not exist")

    return result


@admin_required
@marshal_with(TopicSchema)
def post_topic() -> t.Tuple[JSONType, int]:
    """
    POST /topics/

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.BadRequestError (HTTP error 400)
    """

    try:
        topic = unmarshal(TopicSchema, request.get_json())
    except ValidationError as e:
        raise BadRequestError(str(e))

    try:
        topic_created = db.create_topic(topic)
    except IntegrityError:
        raise ConflictError("Error while saving topic in DB")

    return topic_created, 201


@admin_required
@marshal_with(TopicSchema)
def put_topic(topic_id: int) -> JSONType:
    """
    PUT /topics/{tpic_id}

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.NotFoundError (HTTP error 404)
             backend.errors.BadRequestError (HTTP error 400)
    """

    topic = db.get_topic_by_id(topic_id)

    if topic is None:
        raise NotFoundError(f"Topic with id {topic_id} does not exist")

    try:
        topic = unmarshal(TopicSchema, request.get_json(), instance=topic)
    except ValidationError as e:
        raise BadRequestError(str(e))

    try:
        topic_updated = db.update_topic(topic)
    except IntegrityError:
        raise ConflictError("Error while saving topic in DB")

    return topic_updated

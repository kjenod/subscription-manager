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
from copy import deepcopy

from flask import request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.errors import ConflictError, NotFoundError, BadRequestError, BadGatewayError
from backend.typing import JSONType
from subscription_manager.broker import broker
from subscription_manager.db import subscriptions as db, Subscription
from subscription_manager.db.utils import is_duplicate_record_error
from subscription_manager.endpoints.schemas import SubscriptionSchema
from backend.marshal import unmarshal, marshal_with
from subscription_manager.events import events

__author__ = "EUROCONTROL (SWIM)"


@marshal_with(SubscriptionSchema, many=True)
def get_subscriptions() -> t.List[Subscription]:
    """
    GET /subscriptions/

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
    """
    user = request.user
    params = {} if user.is_admin else {'user_id': user.id}

    return db.get_subscriptions(**params)


@marshal_with(SubscriptionSchema)
def get_subscription(subscription_id: int) -> Subscription:
    """
    GET /subscription/{subscription_id}

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.NotFoundError (HTTP error 404)

    """
    user = request.user
    params = {} if user.is_admin else {'user_id': user.id}

    result = db.get_subscription_by_id(subscription_id, **params)

    if result is None:
        raise NotFoundError(f"Subscription with id {subscription_id} does not exist")

    return result


@marshal_with(SubscriptionSchema)
def post_subscription() -> t.Tuple[Subscription, int]:
    """
    POST /subscriptions/

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.BadRequestError (HTTP error 400)
             backend.errors.BadGatewayError (HTTP error 502)
    """
    try:
        subscription = unmarshal(SubscriptionSchema, request.get_json())
        subscription.user_id = request.user.id

        events.create_subscription_event(subscription)
    except ValidationError as e:
        raise BadRequestError(str(e))
    except broker.BrokerError as e:
        raise BadGatewayError(f"Error while accessing the broker: {str(e)}")
    except SQLAlchemyError as e:
        if is_duplicate_record_error(e):
            raise ConflictError("Record with same data already exists in DB")
        raise

    return subscription, 201


@marshal_with(SubscriptionSchema)
def put_subscription(subscription_id: int) -> JSONType:
    """
    PUT /subscriptions/{subscription_id}

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.NotFoundError (HTTP error 404)
             backend.errors.BadRequestError (HTTP error 400)
    """

    user = request.user
    params = {} if user.is_admin else {'user_id': user.id}

    subscription = db.get_subscription_by_id(subscription_id, **params)

    if subscription is None:
        raise NotFoundError(f"Subscription with id {subscription_id} does not exist")

    current_subscription = deepcopy(subscription)
    try:
        updated_subscription = unmarshal(SubscriptionSchema, request.get_json(), instance=subscription)

        events.update_subscription_event(current_subscription, updated_subscription)
    except ValidationError as e:
        raise BadRequestError(str(e))
    except broker.BrokerError as e:
        raise BadGatewayError(f"Error while accessing broker: {str(e)}")
    except SQLAlchemyError as e:
        if is_duplicate_record_error(e):
            raise ConflictError("Record with same data already exists in DB")
        raise

    return updated_subscription


def delete_subscription(subscription_id: int) -> t.Tuple[None, int]:
    """
    DELETE /subscriptions/{subscription_id}

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.NotFoundError (HTTP error 404)
    """
    user = request.user
    params = {} if user.is_admin else {'user_id': user.id}

    subscription = db.get_subscription_by_id(subscription_id, **params)

    if subscription is None:
        raise NotFoundError(f"Topic with id {subscription_id} does not exist")

    try:
        events.delete_subscription_event(subscription)
    except broker.BrokerError as e:
        raise BadGatewayError(f"Error while accessing broker: {str(e)}")

    return None, 204

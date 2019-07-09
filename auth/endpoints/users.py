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
from backend.db import property_has_changed
from backend.errors import NotFoundError, ConflictError, BadRequestError
from backend.marshal import marshal_with, unmarshal
from backend.typing import JSONType
from auth.auth import hash_password
from auth.db import users as user_service, User
from auth.endpoints.schemas import UserSchema

__author__ = "EUROCONTROL (SWIM)"


def _admin_required_callback(user):
    return getattr(user, 'is_admin', False)


@admin_required(callback=_admin_required_callback)
@marshal_with(UserSchema, many=True)
def get_users() -> JSONType:
    """
    GET /users/ endpoint

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
    """

    return user_service.get_users()


@admin_required(callback=_admin_required_callback)
@marshal_with(UserSchema)
def get_user(user_id: int) -> JSONType:
    """
    GET /users/{user_id}

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.NotFoundError (HTTP error 404)
    """

    result = user_service.get_user_by_id(user_id)

    if result is None:
        raise NotFoundError(f"User with id {user_id} does not exist")

    return result


@admin_required(callback=_admin_required_callback)
@marshal_with(UserSchema)
def post_user() -> t.Tuple[JSONType, int]:
    """
    POST /users/

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.BadRequestError (HTTP error 400)
    """

    try:
        user = unmarshal(UserSchema, request.get_json())
    except ValidationError as e:
        raise BadRequestError(str(e))

    # hash password before saving in DB
    user.password = hash_password(user.password)

    try:
        user_created = user_service.save_user(user)
    except IntegrityError:
        raise ConflictError("Error while saving user in DB")

    return user_created, 201


@admin_required(callback=_admin_required_callback)
@marshal_with(UserSchema)
def put_user(user_id: int) -> JSONType:
    """
    PUT /users/{user_id}

    :raises: backend.errors.UnauthorizedError (HTTP error 401)
             backend.errors.ForbiddenError (HTTP error 403)
             backend.errors.NotFoundError (HTTP error 404)
             backend.errors.BadRequestError (HTTP error 400)
    """

    user = user_service.get_user_by_id(user_id)

    if user is None:
        raise NotFoundError(f"User with id {user_id} does not exist")

    try:
        user = unmarshal(UserSchema, request.get_json(), instance=user, partial=True)
    except ValidationError as e:
        raise BadRequestError(str(e))

    # in case the user has provided a new password then it needs to be hashed
    if _password_has_changed(user):
        user.password = hash_password(user.password)

    try:
        user_updated = user_service.save_user(user)
    except IntegrityError:
        raise ConflictError("Error while saving user in DB")

    return user_updated


def _password_has_changed(user: User) -> bool:
    """
    Indicates whether the password of the user has changed after being loaded from DB
    """
    return property_has_changed(user, 'password')

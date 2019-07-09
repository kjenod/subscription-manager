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
from functools import wraps

from flask import request

from auth.auth import validate_credentials
from backend.errors import UnauthorizedError, ForbiddenError

__author__ = "EUROCONTROL (SWIM)"


def basic_auth(username: str, password: str, required_scopes: t.Optional[t.List[str]] = None) -> t.Dict[str, t.Any]:
    """
    Implements basic authentication. The function will be called from the connexion library after it has decoded the
    base64 encoded string "username:password" by the client.
    The authenticated user will be added in the global Flask request for further usage.
    :param username:
    :param password:
    :param required_scopes: it is required by connexion but OPENAPI 3 specs do not foresee scopes for basic
                            authentication
    :return:
    """
    try:
        user = validate_credentials(username, password)
    except ValueError as e:
        raise UnauthorizedError(str(e))

    request.user = user

    return {}


def admin_required(callback: t.Callable) -> t.Callable:
    """
    Decorator that determines whether the user is admin or not. To be used on endpoint views.
    :param f:
    :return:
    """
    def wrapper(f: t.Callable) -> t.Callable:
        @wraps(f)
        def decorated(*args, **kwargs) -> t.Callable:
            # if request.user and not getattr(request.user, 'is_admin', False):
            if request.user and not callback(request.user):
                raise ForbiddenError('Admin rights required')

            return f(*args, **kwargs)

        return decorated
    return wrapper
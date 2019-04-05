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

import flask_sqlalchemy
import marshmallow

from backend.typing import ViewResponse, JSONType

__author__ = "EUROCONTROL (SWIM)"


def unmarshal(schema_class: marshmallow.Schema,
              data: t.Dict[str, t.Any],
              instance: t.Optional[flask_sqlalchemy.model.DefaultMeta] = None,
              **kwargs: object) -> flask_sqlalchemy.model.DefaultMeta:
    """
    Deserializes a dictionary into a Model.

    :param schema_class:
    :param data:
    :param instance:
    :param kwargs: extra arguments applying to Schema.load()
    :return:
    :raises: marshmallow.ValidationError
    """
    obj, errors = schema_class(**kwargs).load(data, instance=instance)
    if errors:
        error_per_property = [f"'{property}': {error_message}" for property, error_message in errors.items()]
        raise marshmallow.ValidationError(", ".join(error_per_property))

    return obj


def marshal_with(schema_class: marshmallow.Schema, many: bool= False) -> t.Callable:
    """
    Decorator used to serialize the data returned by an endpoint view.

    :param schema_class:
    :param many: in case of se
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result: ViewResponse = func(*args, **kwargs)

            if isinstance(result, tuple):
                obj, status_code = result
            else:
                obj, status_code = result, 200

            marshaled_obj: JSONType = schema_class(many=many).dump(obj).data

            return marshaled_obj, status_code
        return wrapper
    return decorator
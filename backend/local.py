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
from threading import Lock

from werkzeug.local import LocalProxy

__author__ = "EUROCONTROL (SWIM)"


def import_flask():
    try:
        import flask
        from flask import current_app
        return flask, current_app
    except ImportError:
        return None, None


flask, flask_app = import_flask()


def _get_app_context():
    if flask and flask_app:
        return flask_app

    raise Exception("No flask app context found.")


app_context = LocalProxy(_get_app_context)


class BaseProxy(LocalProxy):
    _private = {"_lock", "_key", "_container", "_create_func"}

    def __init__(self, container, key, create_func):
        super().__init__(self.__get_object)

        self._lock = Lock()
        self._container = container
        self._key = key
        self._create_func = create_func

    def __get_object(self):
        result = getattr(self._container, self._key, None)

        if result is None:
            with self._lock:
                result = getattr(self._container, self._key, None)
                if result is None:
                    result = self._create_func()
                    setattr(self._container, self._key, result)

        return result

    def __setattr__(self, key, value):
        if key in self._private:
            object.__setattr__(self, key, value)
        else:
            return super().__setattr__(key, value)


class AppContextProxy(BaseProxy):
    def __init__(self, create_func):
        super().__init__(app_context, f"_swim_{id(self)}", create_func)


class _StaticContainer:
    pass


class LazyProxy(BaseProxy):
    def __init__(self, create_func):
        super().__init__(_StaticContainer(), "_object", create_func)

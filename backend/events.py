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
import abc

__author__ = "EUROCONTROL (SWIM)"


class Event(list):
    """
    Simplistic implementation of event handling.

    A list of callable objects. Calling an instance of this will cause a
    call to each item in the list in ascending order by index.
    """
    _type = 'Generic'

    def __call__(self, *args, **kwargs):
        for handler in self:
            handler(*args, **kwargs)

    def __repr__(self):
        return f"{self._type} Event({list.__repr__(self)})"


class EventSafe(list):

    def __call__(self, *args, **kwargs):
        handlers = [handler_class(*args, **kwargs) for handler_class in self]
        processed_handlers = []

        for handler in handlers:
            try:
                handler.do()
                processed_handlers.append(handler)
            except:
                handler.undo()

                processed_handlers.reverse()
                for processed_handler in processed_handlers:
                    processed_handler.undo()

                raise


class EventHandler(abc.ABC):

    @abc.abstractmethod
    def do(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def undo(self, *args, **kwargs):
        pass

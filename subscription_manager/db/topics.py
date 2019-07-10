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

from sqlalchemy.orm.exc import NoResultFound

from swim_backend.db import db_save, db, db_delete
from subscription_manager.db import Topic

__author__ = "EUROCONTROL (SWIM)"


def get_topic_by_id(topic_id: int, user_id: t.Optional[int] = None) -> t.Union[Topic, None]:
    filters = {
        'id': topic_id
    }

    if user_id:
        filters['user_id'] = user_id
    try:
        result = Topic.query.filter_by(**filters).one()
    except NoResultFound:
        result = None

    return result


def get_topics(user_id: t.Optional[int] = None) -> t.List[Topic]:
    filters = {'user_id': user_id} if user_id else {}

    return Topic.query.filter_by(**filters).all()


def create_topic(topic: Topic) -> Topic:
    return db_save(db.session, topic)


def update_topic(topic: Topic) -> Topic:
    return db_save(db.session, topic)


def delete_topic(topic: Topic) -> None:
    db_delete(db.session, topic)

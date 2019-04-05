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
import flask_sqlalchemy as flask_sa
import sqlalchemy as sa


__author__ = "EUROCONTROL (SWIM)"

db = flask_sa.SQLAlchemy()


def db_save(session: sa.orm.session.Session,
            obj: flask_sa.model.DefaultMeta) -> flask_sa.model.DefaultMeta:
    """
    Saves an object in db and rollbacks before raising in case of DB error

    :param session:
    :param obj:
    :return:
    """
    try:
        session.add(obj)
        session.commit()
        return obj
    except sa.exc.IntegrityError:
        session.rollback()
        raise


def property_has_changed(obj: flask_sa.model.Model,
                         property: str,
                         db: flask_sa.SQLAlchemy = db) -> bool:
    """
    Indicates whether a property of an object has changed after it was loaded from DB.

    :param obj:
    :param property:
    :param db:
    :return:
    """
    state = db.inspect(obj)
    history = state.get_history(property, True)

    return history.has_changes()

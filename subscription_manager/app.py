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
import os
from pathlib import Path

import connexion
from pkg_resources import resource_filename

from subscription_manager import VERSION, DESCRIPTION, BASE_PATH
from subscription_manager.base.flask import configure_flask
from subscription_manager.db import db

__author__ = "EUROCONTROL (SWIM)"


def create_app(config_file):
    connexion_app = connexion.App(__name__)

    connexion_app.add_api(
        Path('swagger.yml'),
        arguments=(dict(
            version=VERSION,
            description=DESCRIPTION,
            base_path=BASE_PATH)),
        strict_validation=True
    )

    app = connexion_app.app

    _load_config(app, config_file)

    configure_flask(app, {})

    _configure_db(db, app)

    return app


def _load_config(app, filename):
    app.config.from_pyfile(filename)

    # app_config_file = os.getenv('FLASK_APPLICATION_CONFIG')
    # if app_config_file:
    #     app.config.from_pyfile(app_config_file)


def _configure_db(db, app):

    with app.app_context():
        db.init_app(app)
        db.create_all()


if __name__ == '__main__':
    config_file = resource_filename(__name__, 'config.py')
    app = create_app(config_file)
    app.run(port=8080, debug=False)

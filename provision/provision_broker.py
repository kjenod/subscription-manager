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
import logging
import logging.config
import os

from broker_rest_client.models import RabbitMQUserPermissions
from broker_rest_client.rabbitmq_rest_client import RabbitMQRestClient
from pkg_resources import resource_filename
from rest_client.errors import APIError

from provision.utils import load_config

__author__ = "EUROCONTROL (SWIM)"


_logger = logging.getLogger(__name__)

BROKER_USERS = [
    {
        'prefix': 'BROKER_MGMT',
        'permissions': RabbitMQUserPermissions(configure=".*", write=".*", read=".*"),
        'tags': ['management']
    },
    {
        'prefix': 'SWIM_EXPLORER_BROKER',
        'permissions': RabbitMQUserPermissions(configure=".*", write="", read=".*"),
        'tags': []
    }
]


def _get_rabbitmq_rest_client(config):
    return RabbitMQRestClient.create(
        host=config['host'],
        https=config['https'],
        username=config.get('username'),
        password=config.get('password'),
        verify=config.get('cert_path') or False,
        retry=config['retry']
    )


def _add_users():
    for user in BROKER_USERS:
        name = os.environ.get(user['prefix'] + '_USER')
        password = os.environ.get(user['prefix'] + '_PASS')

        if name is None or password is None:
            _logger.warning(f"username or password not found for {user['prefix']}. Skipping...")
            continue

        if client.user_exists(name):
            _logger.info(f"User {name} already exists. Skipping...")
            continue

        try:
            client.add_user(name, password, user['permissions'], user['tags'])
            _logger.info(f'User {name} was successfully added in RabbitMQ')
        except APIError as e:
            _logger.error(f'User {name} failed to be added in RabbitMQ: {str(e)}')


def _apply_policies():
    try:
        client.create_policy(
            name='max-queue-length',
            pattern=".*",
            priority=1,
            apply_to="queues",
            definitions={'max-length': config['MAX_BROKER_QUEUE_LENGTH']}
        )
        _logger.info(f"Policy 'max-queue-length' was successfully appplied in RabbitMQ")
    except APIError as e:
        _logger.error(f'Error while applying policy to RabbitMQ: {str(e)}')


if __name__ == '__main__':
    config = load_config(resource_filename(__name__, 'config.yml'))

    logging.config.dictConfig(config['LOGGING'])

    client = _get_rabbitmq_rest_client(config['BROKER'])

    _logger.info(f"Adding users...")
    _add_users()

    _logger.info(f"Applying policies...")
    _apply_policies()

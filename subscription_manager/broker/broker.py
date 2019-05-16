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
from broker_rest_client.rabbitmq_rest_client import RabbitMQRestClient
from flask import current_app as app
from rest_client.errors import APIError

from backend.local import AppContextProxy

__author__ = "EUROCONTROL (SWIM)"


def _get_rabbitmq_rest_client():
    return RabbitMQRestClient.create(
        host=app.config['BROKER_HOST'],
        https=True,
        username=app.config['BROKER_USERNAME'],
        password=app.config['BROKER_PASSWORD'],
        verify=app.config['BROKER_CERT_PATH']
    )

broker_client = AppContextProxy(_get_rabbitmq_rest_client)


class BrokerError(Exception):
    pass


def create_topic(topic, durable=False):
    try:
        broker_client.create_topic(topic, durable)
    except APIError as e:
        raise BrokerError(f"Error while creating topic {topic}: {str(e)}")


def delete_topic(topic):
    try:
        broker_client.delete_topic(topic)
    except APIError as e:
        raise BrokerError(f"Error while deleting topic {topic}: {str(e)}")


def bind_queue_to_topic(queue, topic, durable=False):
    try:
        broker_client.bind_queue_to_topic(queue, topic, durable=durable)
    except APIError as e:
        raise BrokerError(f"Error while binding queue {queue} with topic {topic}: {str(e)}")


def get_queue(queue):
    try:
        return broker_client.get_queue(queue)
    except(APIError):
        return None


def create_queue_for_topic(queue, topic):
    try:
        broker_client.create_queue(name=queue)
        broker_client.bind_queue_to_topic(queue=queue, topic='default', key=topic)
    except APIError as e:
        raise BrokerError(f"Error while creating queue {queue} for topic {topic}") from e


def delete_queue(queue):
    try:
        broker_client.delete_queue(queue)
    except APIError as e:
        raise BrokerError(f"Error while deleting queue {queue}: {str(e)}")


def delete_queue_binding(queue, topic):
    try:
        broker_client.delete_queue_binding(queue, topic='default', key=topic)
    except APIError as e:
        raise BrokerError(f"Error while deleting queue binding: {str(e)}")

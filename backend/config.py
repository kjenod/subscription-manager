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

import flask
import yaml
import logging.config
from pkg_resources import resource_filename

__author__ = "EUROCONTROL (SWIM)"


def _from_yaml(filename: str) -> t.Union[t.Dict[str, t.Any], None]:
    """
    Converts a YAML file into a Python dict

    :param filename:
    :return:
    """
    if not filename.endswith(".yml"):
        raise ValueError("YAML config files should end with '.yml' extension (RTFMG).")

    with open(filename) as f:
        obj = yaml.load(f, Loader=yaml.FullLoader)

    return obj or None


def load_app_config(package: str, filename: t.Optional[str] = None) -> t.Dict[str, t.Any]:
    """
    It expects and loads a default config.yml under the package directory. Optionally, there might be an additional
    config file provided which must also exist under the same directory. The second file overrides the configuration
    of the default one.

    :param package:
    :param filename:
    :return:
    """
    default_config_file = resource_filename(package, 'config.yml')
    config = _from_yaml(default_config_file)

    if filename:
        extra_config = _from_yaml(filename)
        config.update(extra_config)

    return config


def configure_logging(app: flask.Flask):
    """
    Initializes the logging of the provided app. The app should be already loaded with the necessary configuration
    which should provide a 'LOGGING' property.

    An example in YAML could be:

        LOGGING:
          version: 1

          handlers:
            console:
              class: logging.StreamHandler
              formatter: default
              level: DEBUG

          formatters:
            default:
              format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
              class: logging.Formatter

          disable_existing_loggers: false

          root:
            level: DEBUG
            handlers: [console]

          loggers:
            requests:
              level: INFO

            openapi_spec_validator:
              level: INFO

            connexion:
              level: INFO

    :param app:
    """
    logging.config.dictConfig(app.config['LOGGING'])

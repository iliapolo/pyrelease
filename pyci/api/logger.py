#############################################################################
# Copyright (c) 2018 Eli Polonsky. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   * See the License for the specific language governing permissions and
#   * limitations under the License.
#
#############################################################################

import wryte

from pyci.api import exceptions

loggers = {}


DEFAULT_LOG_LEVEL = 'INFO'


class Logger(object):

    """
    Provides logging capabilities.

    This is a thin wrapper on top a specific implementation. The idea is to hide implementation
    specific features from the API in order to be able to easily switch implementations.

    Args:
        name (str): The name of the logger.
        level (:`str`, optional): The logger level.
    """

    _logger = None

    def __init__(self, name, level=DEFAULT_LOG_LEVEL):

        if not name:
            raise exceptions.InvalidArgumentsException('name cannot be None')

        self._name = name
        self._logger = wryte.Wryte(name)
        self._logger.logger.propagate = False
        self.set_level(level)

    def set_level(self, level):
        self._logger.set_level(level)

    def is_enabled_for(self, level):
        self._logger.logger.isEnabledFor(level)

    def info(self, message, **kwargs):
        self._logger.info('{} {}'.format(message, self._format_key_values(**kwargs)))

    def warning(self, message, **kwargs):
        self._logger.warning('{} {}'.format(message, self._format_key_values(**kwargs)))

    def warn(self, message, **kwargs):
        self._logger.warn('{} {}'.format(message, self._format_key_values(**kwargs)))

    def error(self, message, **kwargs):
        self._logger.error('{} {}'.format(message, self._format_key_values(**kwargs)))

    def debug(self, message, **kwargs):
        self._logger.debug('{} {}'.format(message, self._format_key_values(**kwargs)))

    @staticmethod
    def _format_key_values(**kwargs):
        kvs = []
        for key, value in kwargs.items():
            kvs.append('{}={}'.format(key, value))
        return '[{}]'.format(','.join(kvs))


def get_logger(name):

    """
    Get or create a specific logger by name.

    Returns:
          Logger: The logger instance.
    """

    if name not in loggers:
        loggers[name] = Logger(name)
    return loggers[name]


def setup_loggers(level=DEFAULT_LOG_LEVEL):

    """
    Configure all loggers to the given level.

    """
    for logger in loggers.values():
        logger.set_level(level)

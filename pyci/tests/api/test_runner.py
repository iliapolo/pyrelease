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

import logging

# noinspection PyPackageRequirements
import pytest

from pyci.api import logger, exceptions

logger.setup_loggers(logging.DEBUG)


def test_run_list(runner):

    runner.run(['ls', '-l'])


def test_run_failed_exit_on_failure(runner):

    with pytest.raises(exceptions.CommandExecutionException):
        runner.run('cp')


def test_run_failed_not_exit_on_failure(runner):

    response = runner.run('cp', exit_on_failure=False)

    assert response.return_code != 0
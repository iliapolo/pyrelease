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

import contextlib
import os
import platform
import shutil
import tempfile
import time

import pytest
from github import Github

try:
    # python2
    from mock import MagicMock
except ImportError:
    # python3
    # noinspection PyUnresolvedReferences,PyCompatibility
    from unittest.mock import MagicMock

from pyci.api import logger
from pyci.api import utils
from pyci.api.gh import GitHubRepository
from pyci.api.packager import Packager
from pyci.api.pypi import PyPI
from pyci.api.runner import LocalCommandRunner
from pyci.shell import secrets
from pyci.tests.shell import PyCI
from pyci import tests


log = logger.get_logger(__name__)

REPO_UNDER_TEST = 'iliapolo/pyci-guinea-pig'
LAST_COMMIT = '1b8e0b8ef5929e6d2e6017242bba68425ff64b9a'


@pytest.fixture(name='skip', autouse=True)
def _skip(request):

    def __skip(reason):
        pytest.skip('[{}] {}'.format(request.node.location, reason))

    system = platform.system().lower()

    if hasattr(request.node.function, 'linux') and system == 'windows':
        __skip('This test should not run on windows')


@pytest.fixture(name='cleanup', autouse=True)
def _cleanup(request, repo):
    with _github_cleanup(request, repo):
        yield


@pytest.fixture(name='patch', autouse=True)
def _patch_github_connection(request, connection_patcher):
    connection_patcher.update(_get_data_file(request))
    yield


@pytest.fixture(name='cwd', autouse=True)
def _cwd(temp_dir):

    cwd = os.getcwd()

    try:
        os.chdir(temp_dir)
        yield
    finally:
        os.chdir(cwd)


@pytest.fixture(name='pyci', scope='session')
def _pyci(repo_path):

    yield PyCI(repo_path)


@pytest.fixture(name='release')
def _release(pyci, github):

    # pylint: disable=too-few-public-methods
    class ReleaseCommand(object):

        def __init__(self):
            self.github = github

        @staticmethod
        def run(command, binary=False, catch_exceptions=False):

            command = '--no-ci release --repo {} {}'.format(REPO_UNDER_TEST, command)

            return pyci.run(command=command,
                            binary=binary,
                            catch_exceptions=catch_exceptions)

    yield ReleaseCommand()


@pytest.fixture(name='github')
def _github(pyci, repo):

    repository = GitHubRepository.create(repo=REPO_UNDER_TEST,
                                         access_token=secrets.github_access_token(True))
    setattr(repository, 'repo', repo)

    # pylint: disable=too-few-public-methods
    class GithubSubCommand(object):

        def __init__(self):
            self.api = repository

        @staticmethod
        def run(command, binary=False, catch_exceptions=False):

            command = '--no-ci github --repo {} {}'.format(REPO_UNDER_TEST, command)

            return pyci.run(command=command,
                            binary=binary,
                            catch_exceptions=catch_exceptions)

    yield GithubSubCommand()


@pytest.fixture(name='pack')
def _pack(pyci, repo_path):

    temp_dir = tempfile.mkdtemp()

    ignore = shutil.ignore_patterns('build', '.tox', 'pytest_cache')

    target_repo_path = os.path.join(temp_dir, 'repo')

    shutil.copytree(src=repo_path, dst=target_repo_path, ignore=ignore)

    version = _patch_setup_py(target_repo_path)

    packager = Packager.create(path=target_repo_path)

    # pylint: disable=too-few-public-methods
    class PackSubCommand(object):

        def __init__(self):
            self.api = packager
            self.version = version

        def run(self, command, binary=False, catch_exceptions=False):

            # noinspection PyProtectedMember
            # pylint: disable=protected-access
            pack_options = '--path {}'.format(packager._repo_dir)
            if self.api.target_dir:
                pack_options = '{} --target-dir {}'.format(pack_options, self.api.target_dir)

            command = '--no-ci pack {} {}'.format(pack_options, command)

            return pyci.run(command=command,
                            binary=binary,
                            catch_exceptions=catch_exceptions)

    try:
        yield PackSubCommand()
    finally:
        utils.rmf(packager.repo_dir)


@pytest.fixture(name='pypi')
def _pypi(pyci):

    # pylint: disable=too-few-public-methods
    class PyPISubCommand(object):

        def __init__(self):
            self.api = PyPI.create(username=secrets.twine_username(True),
                                   password=secrets.twine_password(True),
                                   test=True)

        @staticmethod
        def run(command, binary=False, catch_exceptions=False):

            command = '--no-ci pypi --test {}'.format(command)

            return pyci.run(command=command,
                            binary=binary,
                            catch_exceptions=catch_exceptions)

    yield PyPISubCommand()


@pytest.fixture(name='temp_dir')
def _temp_dir(request):

    name = request.node.originalname or request.node.name

    dir_path = tempfile.mkdtemp(suffix=name)

    try:
        yield dir_path
    finally:
        # cleanup
        utils.rmf(dir_path)


@pytest.fixture(name='patched_release')
def _patched_release(mocker, pyci):

    gh = MagicMock()
    packager = MagicMock()
    pypi = MagicMock()

    mocker.patch(target='pyci.api.gh.GitHubRepository.create', new=MagicMock(return_value=gh))
    mocker.patch(target='pyci.api.packager.Packager.create', new=MagicMock(return_value=packager))
    mocker.patch(target='pyci.api.pypi.PyPI.create', new=MagicMock(return_value=pypi))

    # pylint: disable=too-few-public-methods
    class ReleaseCommand(object):

        def __init__(self):
            self.gh = gh
            self.packager = packager
            self.pypi = pypi

        @staticmethod
        def run(command, binary=False, catch_exceptions=False):

            command = '--no-ci release --pypi-test --repo {} {}'.format(
                REPO_UNDER_TEST,
                command)

            return pyci.run(command=command,
                            binary=binary,
                            catch_exceptions=catch_exceptions)

    yield ReleaseCommand()


@pytest.fixture(name='repo', scope='session')
def _repo(connection_patcher):

    get_repo_data = os.path.join(os.path.dirname(tests.__file__),
                                 "replay_data",
                                 "pyci.tests.conftest.get_repo.txt")

    try:
        connection_patcher.patch()
        connection_patcher.update(get_repo_data)
        repo = Github(secrets.github_access_token(True), timeout=30).get_repo(
            REPO_UNDER_TEST, lazy=False)
        yield repo
    finally:
        connection_patcher.reset()


@pytest.fixture(name='connection_patcher', scope='session')
def _github_connection_patcher():

    pytest.register_assert_rewrite('pyci.tests.framework')

    from pyci.tests import github_patcher

    return github_patcher.GithubConnectionPatcher(record=False)


@pytest.fixture(name='runner', scope='session')
def _runner():

    yield LocalCommandRunner()


@pytest.fixture(name='repo_path', scope='session')
def _repo_path():
    import pyci
    return os.path.abspath(os.path.join(pyci.__file__, os.pardir, os.pardir))


@contextlib.contextmanager
def _github_cleanup(request, repo):

    wet = None

    try:
        wet = getattr(request.node.function, 'wet')
    except AttributeError:
        pass

    try:
        yield
    finally:
        if wet:
            _reset_repo(repo)


def _reset_repo(repo):

    _reset_commits(repo)
    _reset_releases(repo)
    _reset_tags(repo)
    _reset_branches(repo)
    _reset_issues(repo)


def _reset_commits(repo):

    log.info('Resetting release branch to original state...')
    ref = repo.get_git_ref('heads/release')
    ref.edit(sha=LAST_COMMIT, force=True)

    log.info('Resetting master branch to original state...')
    ref = repo.get_git_ref('heads/master')
    ref.edit(sha=LAST_COMMIT, force=True)


def _reset_issues(repo):
    log.info('Re-opening and cleaning all issues...')
    for issue in repo.get_issues(state='all'):
        if not issue.pull_request:
            issue.edit(state='open')
            for comment in issue.get_comments():
                comment.delete()


def _reset_releases(repo):
    log.info('Deleting any releases...')
    for release in repo.get_releases():
        release.delete_release()


def _reset_tags(repo):
    log.info('Deleting any tags...')
    for tag in repo.get_tags():
        ref = repo.get_git_ref('tags/{}'.format(tag.name))
        ref.delete()


def _reset_branches(repo):
    log.info('Deleting any additional branches...')
    for branch in repo.get_branches():
        if branch.name not in ['master', 'release']:
            ref = repo.get_git_ref('heads/{}'.format(branch.name))
            ref.delete()


def _patch_setup_py(local_repo_path):

    with open(os.path.join(local_repo_path, 'setup.py'), 'r') as stream:
        setup_py = stream.read()

    version = int(round(time.time() * 1000))
    setup_py = utils.generate_setup_py(setup_py, '{}'.format(version))

    with open(os.path.join(local_repo_path, 'setup.py'), 'w') as stream:
        stream.write(setup_py)

    return version


def _get_data_file(request):

    test_name = request.node.nodeid.replace(os.sep, '.').replace('/', '.').replace('::', '.')

    file_name = os.path.join(os.path.dirname(tests.__file__), "replay_data", test_name + ".txt")

    try:
        record = getattr(request.node.function, 'record')
        if record.kwargs.get('platform', False):
            file_name = '{}[{}]'.format(file_name, platform.system().lower())
    except AttributeError:
        pass

    return file_name

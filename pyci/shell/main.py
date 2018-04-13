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

import sys

import click

from pyci.api import utils
from pyci.api.ci import CIDetector
from pyci.api.packager import Packager
from pyci.api.pypi import PyPI
from pyci.api.releaser import GitHubReleaser
from pyci.api import logger
from pyci.shell import handle_exceptions
from pyci.shell import secrets
from pyci.shell.commands import pack as pack_group
from pyci.shell.commands import release as release_group
from pyci.shell.commands import pypi as pypi_group


@click.group()
@click.option('--repo', required=False)
@click.option('--debug', is_flag=True)
@click.pass_context
@handle_exceptions
def app(ctx, repo, debug):

    if debug:
        logger.setup_loggers('DEBUG')

    ctx.ci = CIDetector().detect()

    if ctx.ci:
        click.echo('Detected CI: {0}'.format(ctx.ci.name))

    repo = repo or (ctx.ci.repo if ctx.ci else utils.get_local_repo())

    if repo is None:
        raise click.ClickException(message='Failed detecting repository name. Please provide it '
                                           'using the "--repo" option.\nIf you are running '
                                           'locally, you can also execute this command from your '
                                           'project root directory (repository will be detected '
                                           'using git).')

    ctx.repo = repo


@click.group()
@click.pass_context
@click.option('--pypi-test', is_flag=True)
@click.option('--pypi-url', is_flag=True)
@handle_exceptions
def release(ctx, pypi_test, pypi_url):

    ctx.releaser = GitHubReleaser(repo=ctx.parent.repo,
                                  access_token=secrets.github_access_token())

    ctx.pypi = PyPI(repository_url=pypi_url,
                    test=pypi_test,
                    username=secrets.twine_username(),
                    password=secrets.twine_password())


@click.group()
@click.pass_context
@click.option('--branch', required=False)
@click.option('--local-repo-path', required=False)
@handle_exceptions
def pack(ctx, branch, local_repo_path):

    access_token = None
    if branch is None:
        access_token = secrets.github_access_token()

    ctx.packager = Packager(repo=ctx.parent.repo,
                            local_repo_path=local_repo_path,
                            branch=branch,
                            access_token=access_token)


@click.group()
@click.pass_context
@click.option('--test', is_flag=True)
@click.option('--repository-url', required=False)
@handle_exceptions
def pypi(ctx, test, repository_url):

    ctx.pypi = PyPI(repository_url=repository_url,
                    test=test,
                    username=secrets.twine_username(),
                    password=secrets.twine_password())


release.add_command(release_group.create)
release.add_command(release_group.delete)
release.add_command(release_group.bump)

pack.add_command(pack_group.binary)
pack.add_command(pack_group.wheel)

pypi.add_command(pypi_group.upload)

app.add_command(release)
app.add_command(pack)
app.add_command(pypi)

# allows running the application as a single executable
# created by pyinstaller
if getattr(sys, 'frozen', False):
    # pylint: disable=no-value-for-parameter
    app(sys.argv[1:])

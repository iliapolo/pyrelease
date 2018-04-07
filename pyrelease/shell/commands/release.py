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

import click

from pyrelease.api.releaser import GithubReleaser
from pyrelease.shell import secrets


@click.command()
@click.option('--repo', required=True)
@click.option('--branch', required=False)
def release(repo, branch):

    releaser = GithubReleaser(repo=repo, access_token=secrets.github_access_token())
    releaser.release(branch)


@click.command()
@click.option('--repo', required=True)
@click.option('--version', required=True)
def delete(repo, version):

    releaser = GithubReleaser(repo=repo, access_token=secrets.github_access_token())
    releaser.delete(version)



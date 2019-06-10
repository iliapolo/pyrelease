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

import os
import platform

import pytest

from pyci.api import utils
from pyci.tests import conftest
from pyci.tests import distros


@pytest.mark.parametrize("binary", [False, True])
def test_binary(pack, runner, binary):

    pack.run('binary --entrypoint pyci.spec', binary=binary)

    expected_package_path = os.path.join(os.getcwd(), 'py-ci-{0}-{1}'.format(
        platform.machine(), platform.system()))

    if platform.system() == 'Windows':
        expected_package_path = '{0}.exe'.format(expected_package_path)

    assert os.path.exists(expected_package_path)

    # lets make sure the binary actually works
    runner.run('{0} --help'.format(expected_package_path))


@pytest.mark.parametrize("binary", [False, True])
def test_binary_options(pack, temp_dir, request, runner, binary):

    pack.api.target_dir = temp_dir

    custom_main = os.path.join('pyci', 'shell', 'custom_main.py')
    with open(os.path.join(pack.api.repo_dir, custom_main), 'w') as stream:
        stream.write('''
import six

if __name__ == '__main__':
    six.print_('It works!')        
''')

    name = request.node.name.replace('[', '-').replace(']', '')

    pack.run('binary --name {} --entrypoint {}'.format(name, custom_main), binary=binary)

    expected_package_path = os.path.join(temp_dir, '{}-{}-{}'
                                         .format(name, platform.machine(), platform.system()))

    if platform.system() == 'Windows':
        expected_package_path = '{0}.exe'.format(expected_package_path)

    assert os.path.exists(expected_package_path)

    # lets make sure the binary actually works
    assert runner.run(expected_package_path).std_out == 'It works!'


@pytest.mark.parametrize("binary", [False, True])
def test_binary_file_exists(pack, binary):

    expected_package_path = os.path.join(os.getcwd(), 'py-ci-{0}-{1}'.format(
        platform.machine(), platform.system()))

    if platform.system() == 'Windows':
        expected_package_path = '{0}.exe'.format(expected_package_path)

    with open(expected_package_path, 'w') as stream:
        stream.write('package')

    result = pack.run('binary --entrypoint pyci.spec', catch_exceptions=True, binary=binary)

    expected_output = 'Binary already exists: {}'.format(expected_package_path)
    expected_possible_solution = 'Delete/Move the binary and try again'

    assert expected_output in result.std_out
    assert expected_possible_solution in result.std_out


@pytest.mark.parametrize("binary", [False, True])
def test_binary_default_entrypoint_doesnt_exist(pack, binary):

    result = pack.run('binary', catch_exceptions=True, binary=binary)

    expected_output = 'Failed locating an entrypoint file'
    expected_possible_solutions = [
        'Create an entrypoint file in one of the following paths',
        'Use --entrypoint to specify a custom entrypoint path'
    ]

    assert expected_output in result.std_out
    for expected_possible_solution in expected_possible_solutions:
        assert expected_possible_solution in result.std_out


@pytest.mark.parametrize("binary", [False, True])
def test_binary_entrypoint_doesnt_exist(pack, binary):

    result = pack.run('binary --entrypoint doesnt-exist', catch_exceptions=True, binary=binary)

    expected_output = 'The entrypoint path you specified does not exist: doesnt-exist'

    assert expected_output in result.std_out


@pytest.mark.parametrize("binary", [False, True])
def test_wheel(pack, binary):

    pack.run('wheel', binary=binary)

    py = 'py3' if utils.is_python_3() else 'py2'

    expected_path = os.path.join(os.getcwd(), 'py_ci-{}-{}-none-any.whl'.format(pack.version, py))

    assert os.path.exists(expected_path)


@pytest.mark.parametrize("binary", [False, True])
def test_wheel_options(pack, temp_dir, binary):

    pack.api.target_dir = temp_dir

    result = pack.run('wheel --universal', binary=binary)

    expected_path = os.path.join(temp_dir, 'py_ci-{0}-py2.py3-none-any.whl'.format(pack.version))

    expected_output = '* Wheel package created: {}'.format(expected_path)

    assert expected_output in result.std_out
    assert os.path.exists(expected_path)


@pytest.mark.parametrize("binary", [False, True])
def test_wheel_file_exists(pack, binary):

    expected_path = os.path.join(os.getcwd(), 'py_ci-{}-py2.py3-none-any.whl'
                                 .format(pack.version))

    with open(expected_path, 'w') as stream:
        stream.write('package')

    result = pack.run('wheel --universal', catch_exceptions=True, binary=binary)

    expected_output = 'Wheel already exists: {}'.format(expected_path)
    expected_possible_solution = 'Delete/Move the package and try again'

    assert expected_output in result.std_out
    assert expected_possible_solution in result.std_out


@pytest.mark.parametrize("binary", [False, True])
def test_wheel_not_python_project(pack, binary):

    os.remove(os.path.join(pack.api.repo_dir, 'setup.py'))

    result = pack.run('wheel', binary=binary, catch_exceptions=True)

    expected_output = 'does not contain a valid python project'

    assert expected_output in result.std_out


# @pytest.mark.skip()
@pytest.mark.linux
@pytest.mark.parametrize("build_distro", [distros.Stretch()])
@pytest.mark.parametrize("run_distro", [distros.Ubuntu()])
def test_binary_cross_distribution_wheel(build_distro, run_distro):

    local_binary_path = build_distro.binary()

    try:
        remote_binary_path = run_distro.add(local_binary_path)
        result = run_distro.run('ls -l {0} && chmod +x {0} && {0} pack --repo {1} --sha {2} wheel'
                                .format(remote_binary_path, conftest.REPO_UNDER_TEST, conftest.LAST_COMMIT))
        assert 'pyci_guinea_pig-0.0.1-py3-none-any.whl' in result.std_out
    finally:
        os.remove(local_binary_path)

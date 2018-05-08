#!/usr/bin/env bash

set -e

echo "[install] Starting script"

TRAVIS=${TRAVIS:-}
CIRCLECI=${CIRCLECI:-}
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


function install_python_on_mac {

    echo "[install] Installing pyenv..."
    HOMEBREW_NO_AUTO_UPDATE=1 brew install pyenv
    echo "[install] Successfully installed pyenv"

    echo "[install] Initializing pyenv..."
    eval "$(pyenv init -)"
    echo "[install] Successfully initialized pyenv..."

    echo "[install] Installing python 2.7.14 with pyenv..."
    # --enable-shared is needed for pyinstaller.
    env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install -s 2.7.14
    pyenv global 2.7.14
    echo "[install] Successfully installed python 2.7.14 with pyenv..."

    echo "[install] Checking where python is"
    which python

    echo "[install] Checking python version"
    $(which python) --version

    echo "[install] Checking where pip is"
    which pip

    echo "[install] Finished installing and configuring python"

}


os=$(uname -s)
if [ ${os} == "Darwin" ] && [ ! -z ${TRAVIS} ]; then
    # only install on travis since it does not have python
    # installed for mac builds
    install_python_on_mac
fi

if [ ! -z ${CIRCLECI} ]; then

    echo "Creating a new virtualenv"
    virtualenv virtualenv

    echo "Activating virtualenv"
    source virtualenv/bin/activate

fi

echo "[install] Installing test dependencies"
pip install -r ${DIR}/../../../test-requirements.txt

echo "[install] Installing dependencies"
pip install -r ${DIR}/../../../requirements.txt

echo "[install] Installing package"
pip install ${DIR}/../../../.

echo "[install] Done!"

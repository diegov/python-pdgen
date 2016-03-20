#!/usr/bin/env bash

set -e

if [ "$VIRTUAL_ENV" == "" ]; then
    echo "No virtual env detected. This script will install custom built libraries which should not be installed globally" >&2
    exit 1
fi

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd "$THIS_SCRIPT_DIR" > /dev/null

pushd libpd/python && make && python setup.py install && popd
pip3 install -r requirements.txt

python setup.py install

popd > /dev/null

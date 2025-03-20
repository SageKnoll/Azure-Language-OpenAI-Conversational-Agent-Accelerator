#!/bin/bash

set -e

CWD=$(pwd)
SCRIPT_DIR=$(dirname $(realpath "$0"))
cd ${SCRIPT_DIR}

# Arguments:
use_mi=$1

if [ "$use_mi" = "true" ]; then
    python3 -m ensurepip --upgrade
    echo "Authenticating with MI..."
    az login --identity
fi

# Fetch data:
cp ../../data/*.json .

echo "Installing requirements..."
python3 -m pip install -r requirements.txt

echo "Running CLU setup..."
python3 clu_setup.py
echo "Running CQA setup..."
python3 cqa_setup.py
echo "Running Orchestration setup..."
python3 orchestration_setup.py

# Cleanup:
rm *.json
cd ${CWD}

echo "Language setup complete"

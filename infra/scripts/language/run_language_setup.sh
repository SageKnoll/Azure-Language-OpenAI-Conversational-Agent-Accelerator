#!/bin/bash

set -e

CWD=$(pwd)
SCRIPT_DIR=$(dirname $(realpath "$0"))
cd ${SCRIPT_DIR}

# Arguments:
is_local_setup=$1

if [ $is_local_setup = "false" ]; then
    base_url=$2
    echo "Downloading dependencies..."
    # Scripts:
    curl --output "clu_setup.py" ${base_url}"infra/scripts/language/clu_setup.py"
    curl --output "cqa_setup.py" ${base_url}"infra/scripts/language/cqa_setup.py"
    curl --output "orchestration_setup.py" ${base_url}"infra/scripts/language/orchestration_setup.py"
    # Requirements:
    curl --output "requirements.txt" ${base_url}"infra/scripts/language/requirements.txt"
    # Data:
    curl --output "clu_import.json" ${base_url}"infra/data/clu_import.json"
    curl --output "cqa_import.json" ${base_url}"infra/data/cqa_import.json"
    curl --output "orchestration_import.json" ${base_url}"infra/data/orchestration_import.json"
    # Authenticate with MI:
    echo "Authenticating..."
    az login --identity
else
    # Fetch data:
    cp ../../data/*.json .
fi

echo "Installing requirements..."
pip install -r requirements.txt

echo "Running CLU setup..."
python clu_setup.py
echo "Running CQA setup..."
python cqa_setup.py
echo "Running Orchestration setup..."
python orchestration_setup.py

# Cleanup:
rm *.json
cd ${CWD}

echo "Language setup complete"

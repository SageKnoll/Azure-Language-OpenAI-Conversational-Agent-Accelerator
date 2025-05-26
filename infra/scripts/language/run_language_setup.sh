#!/bin/bash

set -e

cwd=$(pwd)
script_dir=$(dirname $(realpath "$0"))
cd ${script_dir}

# Fetch data:
cp ../../data/*.json .

# Fetch openapi specs
cp ../../openapi_specs/*.json .

echo "Installing requirements..."
python3 -m pip install -r requirements.txt

echo "Running agent setup..."
python3 agent_setup.py

# Cleanup:
rm *.json
cd ${cwd}

echo "Language setup complete"

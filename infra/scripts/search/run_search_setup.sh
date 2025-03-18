#!/bin/bash

set -e

PRODUCT_INFO_FILE="product_info.tar.gz"
CWD=$(pwd)
SCRIPT_DIR=$(dirname $(realpath "$0"))
cd ${SCRIPT_DIR}

# Arguments:
is_local_setup=$1
storage_account_name=$2
blob_container_name=$3

if [ $is_local_setup = "false" ]; then
    base_url=$4
    echo "Downloading dependencies..."
    # Scripts:
    curl --output "index_setup.py" ${base_url}"infra/scripts/search/index_setup.py"
    # Requirements:
    curl --output "requirements.txt" ${base_url}"infra/scripts/search/requirements.txt"
    # Data:
    curl --output "product_info.tar.gz" ${base_url}"infra/data/product_info.tar.gz"
    # Authenticate with MI:
    echo "Authenticating..."
    az login --identity
else
    # Fetch data:
    cp ../../data/${PRODUCT_INFO_FILE} .
fi

# Unzip data:
mkdir product_info && mv ${PRODUCT_INFO_FILE} product_info/
cd product_info && tar -xvzf ${PRODUCT_INFO_FILE} && cd ..

echo "Uploading files to blob container..."
az storage blob upload-batch \
    --auth-mode login \
    --destination ${blob_container_name} \
    --account-name ${storage_account_name} \
    --source "product_info" \
    --pattern "*.md" \
    --overwrite

echo "Installing requirements..."
pip install -r requirements.txt

echo "Running index setup..."
python index_setup.py

# Cleanup:
rm -rf product_info/
cd ${CWD}

echo "Search setup complete"

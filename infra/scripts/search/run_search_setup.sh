#!/bin/bash

set -e

PRODUCT_INFO_FILE="product_info.tar.gz"
CWD=$(pwd)
SCRIPT_DIR=$(dirname $(realpath "$0"))
cd ${SCRIPT_DIR}

# Arguments:
use_mi=$1
storage_account_name=$2
blob_container_name=$3

if [ "$use_mi" = "true" ]; then
    python -m ensurepip --upgrade
    tdnf install -y tar
    echo "Authenticating with MI..."
    az login --identity
fi

# Fetch data:
cp ../../data/${PRODUCT_INFO_FILE} .

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
python3 -m pip install -r requirements.txt

echo "Running index setup..."
python3 index_setup.py

# Cleanup:
rm -rf product_info/
cd ${CWD}

echo "Search setup complete"

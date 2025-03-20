#!/bin/bash

set -e

CWD=$(pwd)
SCRIPT_DIR=$(dirname $(realpath "$0"))
cd ${SCRIPT_DIR}

# Arguments:
use_mi=$1
acr_name=$2
repo=$3
tag=$4

if [ "$use_mi" = "true" ]; then
    echo "Authenticating with MI..."
    az login --identity
fi

# Change dir to repo root:
cd ../../..

echo "Building image..."

az acr build \
    --image ${acr_name}.azurecr.io/${repo}:${tag} \
    --registry ${acr_name} \
    src

# Cleanup:
cd ${CWD}

echo "Image pushed to ACR"

#!/bin/bash

set -e

CWD=$(pwd)
SCRIPT_DIR=$(dirname $(realpath "$0"))
cd ${SCRIPT_DIR}

# Arguments:
acr_name=$1
repo=$2
tag=$3

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

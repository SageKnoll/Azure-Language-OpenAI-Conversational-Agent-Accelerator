#!/bin/bash

set -e
set -x

CWD=$(pwd)
SCRIPT_DIR=$(dirname $(realpath "$0"))
cd ${SCRIPT_DIR}

# Arguments:
is_local_setup=$1
acr_name=$2
repo=$3
tag=$4

if [ $is_local_setup = "false" ]; then
    clone_url=$5
    echo "Cloning repo..."
    git clone ${clone_url} --single-branch repo_src
    cd repo_src
    # Authenticate with MI:
    echo "Authenticating..."
    az login --identity
else
    cd ../../..
fi

echo "Building image..."

az acr build \
    --image ${acr_name}.azurecr.io/${repo}:${tag} \
    --registry ${acr_name} \
    src

# Cleanup:
cd ${CWD}

echo "Image pushed to ACR"

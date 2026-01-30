#!/bin/bash
# ============================================================
# IRIS Symphony OSHA - Search Index Setup
# ============================================================
# Uploads OSHA knowledge files to blob storage and creates
# the Azure AI Search index with vector embeddings.
# ============================================================

set -e

# Use OSHA knowledge files instead of product_info
knowledge_file="osha_knowledge.tar.gz"
cwd=$(pwd)
script_dir=$(dirname $(realpath "$0"))
cd ${script_dir}

# Arguments:
storage_account_name=$1
blob_container_name=$2

# Fetch data - look for OSHA knowledge files
if [ -f "../../data/${knowledge_file}" ]; then
    echo "Found OSHA knowledge archive: ${knowledge_file}"
    cp ../../data/${knowledge_file} .
    
    # Unzip data:
    if [ ! -d "osha_knowledge" ]; then
        mkdir osha_knowledge
    fi
    mv ${knowledge_file} osha_knowledge/
    cd osha_knowledge && tar -xvzf ${knowledge_file} && cd ..
    upload_source="osha_knowledge"
    
elif [ -d "../../data/osha_knowledge" ]; then
    echo "Found OSHA knowledge directory"
    cp -r ../../data/osha_knowledge .
    upload_source="osha_knowledge"
    
else
    echo "ERROR: No OSHA knowledge files found!"
    echo "Expected either:"
    echo "  - ../../data/osha_knowledge.tar.gz"
    echo "  - ../../data/osha_knowledge/ directory"
    echo ""
    echo "Please add your OSHA knowledge .md files to one of these locations."
    exit 1
fi

# Upload data to storage account blob container:
echo "Uploading OSHA knowledge files to blob container..."

# Retry logic for blob upload to handle role assignment propagation delays
max_retries=3
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if az storage blob upload-batch \
        --auth-mode login \
        --destination ${blob_container_name} \
        --account-name ${storage_account_name} \
        --source "${upload_source}" \
        --pattern "*.md" \
        --overwrite; then
        echo "Successfully uploaded OSHA knowledge files to blob container"
        break
    else
        retry_count=$((retry_count + 1))
        echo "Upload failed (attempt $retry_count/$max_retries). Waiting 30 seconds before retry..."
        if [ $retry_count -lt $max_retries ]; then
            sleep 30
        else
            echo "All upload attempts failed. Exiting."
            exit 1
        fi
    fi
done

# Install requirements:
echo "Installing requirements..."
python3 -m pip install -r requirements.txt

# Run setup:
echo "Running index setup..."
python3 index_setup.py

# Cleanup:
rm -rf osha_knowledge/
cd ${cwd}

echo "OSHA Search setup complete"
echo "Index name: ${SEARCH_INDEX_NAME}"

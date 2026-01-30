#!/bin/bash
# ============================================================
# IRIS Symphony OSHA - AZD Parameter Setup Script
# ============================================================
# This script helps configure Azure environment variables for 
# deploying the IRIS Symphony OSHA Conversational Agent.
# ============================================================

set -e

echo "=============================================="
echo "IRIS Symphony OSHA - Deployment Configuration"
echo "=============================================="

# ============ Region Selection ============
declare -a regions=(
    "centralus"
    "eastus"
    "eastus2"
    "westus2"
    "westus3"
    "northeurope"
    "westeurope"
    "uksouth"
    "australiaeast"
    "southcentralus"
)

declare -a models=(
    "OpenAI.GlobalStandard.gpt-4o"
    "OpenAI.GlobalStandard.gpt-4o-mini"
    "OpenAI.Standard.gpt-4o"
    "OpenAI.Standard.gpt-4o-mini"
    "OpenAI.Standard.text-embedding-3-large"
    "OpenAI.Standard.text-embedding-3-small"
    "OpenAI.GlobalStandard.text-embedding-3-small"
    "OpenAI.Standard.text-embedding-ada-002"
)

declare -A valid_regions

# Fetch quota information per region per model:
for region in "${regions[@]}"; do
    echo "----------------------------------------"
    echo "Checking region: $region"

    quota_info="$(az cognitiveservices usage list --location "$region" --output json 2>/dev/null)" || continue

    if [ -z "$quota_info" ]; then
        echo "WARNING: failed to retrieve quota information for region $region. Skipping."
        continue
    fi

    gpt_available="false"
    embedding_available="false"
    region_quota_info=""

    for model in "${models[@]}"; do
        model_info="$(echo "$quota_info" | awk -v model="\"value\": \"$model\"" '
            BEGIN { RS="},"; FS="," }
            $0 ~ model { print $0 }
        ')"

        if [ -z "$model_info" ]; then
            continue
        fi

        current_value="$(echo "$model_info" | awk -F': ' '/"currentValue"/ {print $2}'  | tr -d ',' | tr -d ' ')"
        limit="$(echo "$model_info" | awk -F': ' '/"limit"/ {print $2}' | tr -d ',' | tr -d ' ')"

        current_value="$(echo "${current_value:-0}" | cut -d'.' -f1)"
        limit="$(echo "${limit:-0}" | cut -d'.' -f1)"
        available=$(($limit - $current_value))

        if [ "$available" -gt 0 ]; then
            region_quota_info+="$model=$available "
            if grep -q "gpt" <<< "$model"; then
                gpt_available="true"
            elif grep -q "embedding" <<< "$model"; then
                embedding_available="true"
            fi
        fi

        echo "Model: $model | Used: $current_value | Limit: $limit | Available: $available"
    done

    if [ "$gpt_available" = "true" ] && [ "$embedding_available" = "true" ]; then
        valid_regions[$region]="$region_quota_info"
    fi
done

# Select region:
while true; do
    echo -e "\nAvailable regions with GPT + Embedding quota: "
    for region_option in "${!valid_regions[@]}"; do
        echo "-> $region_option"
    done

    read -p "Select a region: " selected_region
    if [[ -v valid_regions[$selected_region] ]]; then
        break
    else
        echo "Invalid selection"
    fi
done

# Get model information from selected region:
declare -A valid_gpt_models
declare -A valid_embedding_models
region_quota_info="${valid_regions[$selected_region]}"

for model_info in $region_quota_info; do
    model_name="$(echo "$model_info" | cut -d "=" -f1)"
    available="$(echo "$model_info" | cut -d "=" -f2)"

    if grep -q "gpt" <<< "$model_name"; then
        valid_gpt_models[$model_name]="$available"
    elif grep -q "embedding" <<< "$model_name"; then
        valid_embedding_models[$model_name]="$available"
    fi
 done

# Select GPT model:
while true; do
    echo -e "\nAvailable GPT models in $selected_region:"
    for model_option in "${!valid_gpt_models[@]}"; do
        echo "-> $model_option (${valid_gpt_models[$model_option]} quota available)"
    done

    read -p "Select a GPT model: " selected_gpt_model
    if [[ -v valid_gpt_models[$selected_gpt_model] ]]; then
        break
    else
        echo "Invalid selection"
    fi
done

# Select GPT model quota:
while true; do
    available=${valid_gpt_models[$selected_gpt_model]}
    echo -e "\nAvailable quota for $selected_gpt_model: $available"
    read -p "Select capacity (recommended: 30): " selected_gpt_quota

    if [ 0 -lt $selected_gpt_quota ] && [ $selected_gpt_quota -le $available ]; then
        break
    else
        echo "Invalid selection (must be 1-$available)"
    fi
done

# Select embedding model:
while true; do
    echo -e "\nAvailable embedding models in $selected_region:"
    for model_option in "${!valid_embedding_models[@]}"; do
        echo "-> $model_option (${valid_embedding_models[$model_option]} quota available)"
    done
    echo -e "\nRecommended: OpenAI.Standard.text-embedding-3-large (for 3072 dimensions)"

    read -p "Select an embedding model: " selected_embedding_model
    if [[ -v valid_embedding_models[$selected_embedding_model] ]]; then
        break
    else
        echo "Invalid selection"
    fi
done

# Select embedding model quota:
while true; do
    available=${valid_embedding_models[$selected_embedding_model]}
    echo -e "\nAvailable quota for $selected_embedding_model: $available"
    read -p "Select capacity (recommended: 30): " selected_embedding_quota

    if [ 0 -lt $selected_embedding_quota ] && [ $selected_embedding_quota -le $available ]; then
        break
    else
        echo "Invalid selection (must be 1-$available)"
    fi
done

# ============ Container Apps Environment ============
echo -e "\n=============================================="
echo "Container Apps Environment Configuration"
echo "=============================================="
echo "You can use an existing Container Apps Environment or create a new one."

read -p "Enter existing Container Apps Environment name (or leave blank for new): " cae_name
read -p "Enter Container Apps Environment resource group (or leave blank for same RG): " cae_rg

# ============ IRIS Symphony Zone API URLs ============
echo -e "\n=============================================="
echo "IRIS Symphony Zone API Configuration"
echo "=============================================="
echo "Enter your Zone 1/2 API URLs (leave blank if not deployed yet)"

read -p "Zone 1 eCFR Search URL: " ecfr_url
read -p "Zone 1 Recordability Engine URL: " recordability_url
read -p "Zone 1 Analytics API URL: " analytics_url
read -p "Zone 2 Incidents API URL: " incidents_url
read -p "Zone 2 Documents API URL: " documents_url

# ============ Parse Model Info ============
gpt_model_name=$(echo "$selected_gpt_model" | cut -d "." -f3)
gpt_deployment_type=$(echo "$selected_gpt_model" | cut -d "." -f2)

embedding_model_name=$(echo "$selected_embedding_model" | cut -d "." -f3)
embedding_deployment_type=$(echo "$selected_embedding_model" | cut -d "." -f2)

# Set embedding dimensions based on model
if [[ "$embedding_model_name" == "text-embedding-3-large" ]]; then
    embedding_dimensions=3072
elif [[ "$embedding_model_name" == "text-embedding-3-small" ]]; then
    embedding_dimensions=1536
else
    embedding_dimensions=1536
fi

# ============ Summary ============
echo -e "\n=============================================="
echo "Configuration Summary"
echo "=============================================="
echo "Region: $selected_region"
echo ""
echo "GPT Model: $gpt_model_name"
echo "GPT Deployment Type: $gpt_deployment_type"
echo "GPT Capacity: $selected_gpt_quota"
echo ""
echo "Embedding Model: $embedding_model_name"
echo "Embedding Deployment Type: $embedding_deployment_type"
echo "Embedding Capacity: $selected_embedding_quota"
echo "Embedding Dimensions: $embedding_dimensions"
echo ""
echo "Container Apps Environment: ${cae_name:-'(will create new)'}"
echo "Container Apps RG: ${cae_rg:-'(same as deployment RG)'}"
echo ""
echo "IRIS Zone 1 APIs:"
echo "  eCFR: ${ecfr_url:-'(not configured)'}"
echo "  Recordability: ${recordability_url:-'(not configured)'}"
echo "  Analytics: ${analytics_url:-'(not configured)'}"
echo ""
echo "IRIS Zone 2 APIs:"
echo "  Incidents: ${incidents_url:-'(not configured)'}"
echo "  Documents: ${documents_url:-'(not configured)'}"

# ============ Set AZD Environment Variables ============
export AZURE_ENV_GPT_MODEL_NAME=$gpt_model_name
export AZURE_ENV_GPT_MODEL_CAPACITY=$selected_gpt_quota
export AZURE_ENV_GPT_MODEL_DEPLOYMENT_TYPE=$gpt_deployment_type

export AZURE_ENV_EMBEDDING_MODEL_NAME=$embedding_model_name
export AZURE_ENV_EMBEDDING_MODEL_CAPACITY=$selected_embedding_quota
export AZURE_ENV_EMBEDDING_MODEL_DEPLOYMENT_TYPE=$embedding_deployment_type
export AZURE_ENV_EMBEDDING_MODEL_DIMENSIONS=$embedding_dimensions

export AZURE_ENV_CONTAINER_APPS_ENV_NAME=$cae_name
export AZURE_ENV_CONTAINER_APPS_ENV_RG=$cae_rg

export AZURE_ENV_CLU_PROJECT_NAME="sagevia-osha-clu"
export AZURE_ENV_CQA_PROJECT_NAME="sagevia-osha-cqa"
export AZURE_ENV_ORCH_PROJECT_NAME="sagevia-osha-orchestration"

export AZURE_ENV_ROUTER_TYPE="ORCHESTRATION"
export AZURE_ENV_APP_MODE="SEMANTIC_KERNEL"

export IRIS_ZONE1_ECFR_URL=$ecfr_url
export IRIS_ZONE1_RECORDABILITY_URL=$recordability_url
export IRIS_ZONE1_ANALYTICS_URL=$analytics_url
export IRIS_ZONE2_INCIDENTS_URL=$incidents_url
export IRIS_ZONE2_DOCUMENTS_URL=$documents_url

echo -e "\n=============================================="
echo "Environment variables set!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Run: azd up"
echo "2. Select region: $selected_region"
echo "3. Wait for deployment to complete"
echo ""
echo "To verify environment variables:"
echo "  env | grep AZURE_ENV"
echo "  env | grep IRIS_ZONE"

#!/bin/bash
# ============================================================
# IRIS Symphony OSHA - Container App Startup Script
# ============================================================
# This script runs inside the container to:
# 1. Authenticate via Managed Identity
# 2. Set up Language services (CLU/CQA)
# 3. Set up Search index with OSHA knowledge
# 4. Set up AI Foundry agents
# 5. Build and run the application
# ============================================================

set -e

cwd=$(pwd)
script_dir=$(dirname $(realpath "$0"))
src_dir="${script_dir}/../../src"
frontend_dir="${src_dir}/frontend"
backend_dir="${src_dir}/backend"

cd ${script_dir}

echo "=============================================="
echo "IRIS Symphony OSHA - Starting Application"
echo "=============================================="

# Authenticate via Managed Identity:
echo "Authenticating via Managed Identity..."
az login --identity --client-id ${MI_CLIENT_ID}

# Ensure pip:
python3 -m ensurepip --upgrade

# Install deps (for Container Apps, these may already be in the image):
if command -v tdnf &> /dev/null; then
    tdnf install -y tar
    tdnf install -y awk
elif command -v apt-get &> /dev/null; then
    apt-get update && apt-get install -y tar gawk
elif command -v apk &> /dev/null; then
    apk add --no-cache tar gawk
fi

# Install nodejs (if not in image):
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
    \. "$HOME/.nvm/nvm.sh"
    nvm install 22
fi
node -v
npm -v

# Run setup:
export CONFIG_DIR="$(pwd)/config_dir"
mkdir -p $CONFIG_DIR

echo "=============================================="
echo "Setting up Language Services (CLU/CQA)..."
echo "=============================================="
source language/run_language_setup.sh

echo "=============================================="
echo "Setting up Search Index with OSHA Knowledge..."
echo "=============================================="
bash search/run_search_setup.sh ${STORAGE_ACCOUNT_NAME} ${BLOB_CONTAINER_NAME}

echo "=============================================="
echo "Setting up AI Foundry Agents..."
echo "=============================================="
source language/run_agent_setup.sh

# Log IRIS Symphony Zone API configuration:
echo "=============================================="
echo "IRIS Symphony Zone API Configuration:"
echo "=============================================="
echo "Zone 1 (Non-PII):"
echo "  eCFR Search: ${IRIS_ZONE1_ECFR_URL:-'(not configured)'}"
echo "  Recordability: ${IRIS_ZONE1_RECORDABILITY_URL:-'(not configured)'}"
echo "  Analytics: ${IRIS_ZONE1_ANALYTICS_URL:-'(not configured)'}"
echo "Zone 2 (PII-Protected):"
echo "  Incidents: ${IRIS_ZONE2_INCIDENTS_URL:-'(not configured)'}"
echo "  Documents: ${IRIS_ZONE2_DOCUMENTS_URL:-'(not configured)'}"

# Build UI:
echo "=============================================="
echo "Building Frontend UI..."
echo "=============================================="
cd ${frontend_dir}
npm install
npm run build

# Run app:
echo "=============================================="
echo "Starting Backend Application..."
echo "=============================================="
cd ${backend_dir}
python3 -m pip install -r requirements.txt
cd src
cp -r ${frontend_dir}/dist .

# Check if APP_MODE is set, default to SEMANTIC_KERNEL
APP_MODE=${APP_MODE:-SEMANTIC_KERNEL}

# Launch the app:
echo "Launching app with APP_MODE=${APP_MODE}..."
if [ "$APP_MODE" == "SEMANTIC_KERNEL" ]; then
    echo "Starting Semantic Kernel agent-based application..."
    python3 -m uvicorn semantic_kernel_app:app --host 0.0.0.0 --port 8000
elif [ "$APP_MODE" == "UNIFIED" ]; then
    echo "Starting unified (non-agent) application..."
    python3 -m uvicorn unified_app:app --host 0.0.0.0 --port 8000
else
    echo "ERROR: Unknown APP_MODE: $APP_MODE"
    echo "Valid options: SEMANTIC_KERNEL, UNIFIED"
    exit 1
fi

using 'main.bicep'

// ============ GPT Model ============
param gpt_model_name = readEnvironmentVariable('AZURE_ENV_GPT_MODEL_NAME', 'gpt-4o')
param gpt_deployment_capacity = int(readEnvironmentVariable('AZURE_ENV_GPT_MODEL_CAPACITY', '30'))
param gpt_deployment_type = readEnvironmentVariable('AZURE_ENV_GPT_MODEL_DEPLOYMENT_TYPE', 'GlobalStandard')

// ============ Embedding Model ============
param embedding_model_name = readEnvironmentVariable('AZURE_ENV_EMBEDDING_MODEL_NAME', 'text-embedding-3-large')
param embedding_deployment_capacity = int(readEnvironmentVariable('AZURE_ENV_EMBEDDING_MODEL_CAPACITY', '30'))
param embedding_deployment_type = readEnvironmentVariable('AZURE_ENV_EMBEDDING_MODEL_DEPLOYMENT_TYPE', 'Standard')
param embedding_model_dimensions = int(readEnvironmentVariable('AZURE_ENV_EMBEDDING_MODEL_DIMENSIONS', '3072'))

// ============ Container Apps Environment (Your Existing) ============
param container_apps_environment_name = readEnvironmentVariable('AZURE_ENV_CONTAINER_APPS_ENV_NAME', 'cae-sagevia-dev')
param container_apps_environment_rg = readEnvironmentVariable('AZURE_ENV_CONTAINER_APPS_ENV_RG', '')

// ============ OSHA Language Projects ============
param clu_project_name = readEnvironmentVariable('AZURE_ENV_CLU_PROJECT_NAME', 'sagevia-osha-clu')
param cqa_project_name = readEnvironmentVariable('AZURE_ENV_CQA_PROJECT_NAME', 'sagevia-osha-cqa')
param orchestration_project_name = readEnvironmentVariable('AZURE_ENV_ORCH_PROJECT_NAME', 'sagevia-osha-orchestration')

// ============ Router Configuration ============
param router_type = readEnvironmentVariable('AZURE_ENV_ROUTER_TYPE', 'ORCHESTRATION')
param app_mode = readEnvironmentVariable('AZURE_ENV_APP_MODE', 'SEMANTIC_KERNEL')

// ============ IRIS Symphony Zone 1 APIs ============
param iris_zone1_ecfr_url = readEnvironmentVariable('IRIS_ZONE1_ECFR_URL', '')
param iris_zone1_recordability_url = readEnvironmentVariable('IRIS_ZONE1_RECORDABILITY_URL', '')
param iris_zone1_analytics_url = readEnvironmentVariable('IRIS_ZONE1_ANALYTICS_URL', '')

// ============ IRIS Symphony Zone 2 APIs ============
param iris_zone2_incidents_url = readEnvironmentVariable('IRIS_ZONE2_INCIDENTS_URL', '')
param iris_zone2_documents_url = readEnvironmentVariable('IRIS_ZONE2_DOCUMENTS_URL', '')

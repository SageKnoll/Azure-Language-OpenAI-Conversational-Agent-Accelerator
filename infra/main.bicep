// ========== main.bicep - IRIS Symphony OSHA ========== //
targetScope = 'resourceGroup'

// ============ GPT Model Parameters ============
@description('Name of GPT model to deploy.')
@allowed([
  'gpt-4o-mini'
  'gpt-4o'
])
param gpt_model_name string

@description('Capacity of GPT model deployment.')
@minValue(1)
param gpt_deployment_capacity int

@description('GPT model deployment type.')
@allowed([
  'Standard'
  'GlobalStandard'
])
param gpt_deployment_type string

// ============ Embedding Model Parameters ============
@description('Name of Embedding model to deploy.')
@allowed([
  'text-embedding-ada-002'
  'text-embedding-3-small'
  'text-embedding-3-large'
])
param embedding_model_name string

@description('Capacity of embedding model deployment.')
@minValue(1)
param embedding_deployment_capacity int

@description('Embedding model deployment type.')
@allowed([
  'Standard'
  'GlobalStandard'
])
param embedding_deployment_type string

@description('Embedding model dimensions.')
param embedding_model_dimensions int = 1536

// ============ Container Apps Environment (EXISTING) ============
@description('Name of existing Container Apps Environment to deploy to.')
param container_apps_environment_name string

@description('Resource group of existing Container Apps Environment.')
param container_apps_environment_rg string = resourceGroup().name

// ============ OSHA Language Project Names ============
@description('CLU project name')
param clu_project_name string = 'sagevia-osha-clu'

@description('CQA project name')
param cqa_project_name string = 'sagevia-osha-cqa'

@description('Orchestration project name')
param orchestration_project_name string = 'sagevia-osha-orchestration'

// ============ IRIS Symphony Zone API URLs ============
@description('Zone 1 eCFR Search API URL')
param iris_zone1_ecfr_url string = 'https://ca-ecfr-search-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io'

@description('Zone 1 Recordability Engine URL')
param iris_zone1_recordability_url string = 'https://caapi-svo-recordability-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io'

@description('Zone 1 Analytics API URL')
param iris_zone1_analytics_url string = 'https://ca-analytics-api-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io'

@description('Zone 2 Incidents API URL (PII-protected)')
param iris_zone2_incidents_url string = 'https://ca-svo-incidents-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io'

@description('Zone 2 Documents API URL (PII-protected)')
param iris_zone2_documents_url string = 'https://ca-svo-documents-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io'

// ============ Agent IDs (from run_agent_setup.sh) ============
@description('Triage agent ID')
param triage_agent_id string = 'asst_Xeumpw49JJ2QDxmAdJ36NMhL'
@description('Lumi orchestrator agent ID')
param lumi_agent_id string = 'asst_WqND6bfEODDQMe7DspwqQXxK'
@description('Sciences agent ID')
param sciences_agent_id string = 'asst_Su02DkXtTzyYt5N0gtKvC0YC'
@description('Governance agent ID')
param governance_agent_id string = 'asst_T3pi5nSo4UBT0Vz46pE6jqDy'
@description('Analytics agent ID')
param analytics_agent_id string = 'asst_S3NmWxc5N0dQRuFSRtQlRzc6'
@description('Experience agent ID')
param experience_agent_id string = 'asst_682AlT7OQyjvamiVwG0uR4yG'
@description('Translation agent ID')
param translation_agent_id string = 'asst_skeQ8bviyzLJ8RoiatUOOctc'
@description('Head support agent ID')
param head_support_agent_id string = 'asst_WqND6bfEODDQMe7DspwqQXxK'

// ============ Router Configuration ============
@description('Router type for intent classification.')
@allowed([
  'BYPASS'
  'CLU'
  'CQA'
  'ORCHESTRATION'
  'FUNCTION_CALLING'
  'TRIAGE_AGENT'
])
param router_type string = 'ORCHESTRATION'

@description('Application mode.')
@allowed([
  'SEMANTIC_KERNEL'
  'UNIFIED'
])
param app_mode string = 'SEMANTIC_KERNEL'

// ============ Variables ============
var suffix = uniqueString(subscription().id, resourceGroup().id, resourceGroup().location)
var blob_container_name = 'osha-knowledge-files'
var search_index_name = 'sagevia-osha-knowledge-idx'

// ============ Deploy App Dependencies ============
module managed_identity 'resources/managed_identity.bicep' = {
  name: 'deploy_managed_identity'
  params: {
    suffix: suffix
  }
}

module storage_account 'resources/storage_account.bicep' = {
  name: 'deploy_storage_account'
  params: {
    suffix: suffix
    blob_container_name: blob_container_name
  }
}

module search_service 'resources/search_service.bicep' = {
  name: 'deploy_search_service'
  params: {
    suffix: suffix
  }
}

module ai_foundry 'resources/ai_foundry.bicep' = {
  name: 'deploy_ai_foundry'
  params: {
    suffix: suffix
    managed_identity_name: managed_identity.outputs.name
    search_service_name: search_service.outputs.name
    gpt_model_name: gpt_model_name
    gpt_deployment_capacity: gpt_deployment_capacity
    gpt_deployment_type: gpt_deployment_type
    embedding_model_name: embedding_model_name
    embedding_deployment_capacity: embedding_deployment_capacity
    embedding_deployment_type: embedding_deployment_type
    embedding_model_dimensions: embedding_model_dimensions
  }
}

module role_assignments 'resources/role_assignments.bicep' = {
  name: 'create_role_assignments'
  params: {
    managed_identity_name: managed_identity.outputs.name
    ai_foundry_name: ai_foundry.outputs.name
    search_service_name: search_service.outputs.name
    storage_account_name: storage_account.outputs.name
  }
}

// ============ Deploy App (Container Apps instead of Container Instance) ============
module container_app 'resources/container_app.bicep' = {
  name: 'deploy_container_app'
  params: {
    suffix: suffix
    // Container Apps Environment (existing)
    container_apps_environment_name: container_apps_environment_name
    container_apps_environment_rg: container_apps_environment_rg
    // AI Foundry outputs
    agents_project_endpoint: ai_foundry.outputs.agents_project_endpoint
    aoai_deployment: ai_foundry.outputs.gpt_deployment_name
    aoai_endpoint: ai_foundry.outputs.openai_endpoint
    language_endpoint: ai_foundry.outputs.language_endpoint
    translator_resource_id: ai_foundry.outputs.translator_resource_id
    // Managed Identity
    managed_identity_name: managed_identity.outputs.name
    // Search
    search_endpoint: search_service.outputs.endpoint
    search_index_name: search_index_name
    // Storage
    blob_container_name: storage_account.outputs.blob_container_name
    storage_account_connection_string: storage_account.outputs.connection_string
    storage_account_name: storage_account.outputs.name
    // Embeddings
    embedding_deployment_name: ai_foundry.outputs.embedding_deployment_name
    embedding_model_dimensions: ai_foundry.outputs.embedding_model_dimensions
    embedding_model_name: ai_foundry.outputs.embedding_model_name
    // OSHA Language Projects
    clu_project_name: clu_project_name
    cqa_project_name: cqa_project_name
    orchestration_project_name: orchestration_project_name
    // Router
    router_type: router_type
    app_mode: app_mode
    // IRIS Symphony Zone APIs
    iris_zone1_ecfr_url: iris_zone1_ecfr_url
    iris_zone1_recordability_url: iris_zone1_recordability_url
    iris_zone1_analytics_url: iris_zone1_analytics_url
    iris_zone2_incidents_url: iris_zone2_incidents_url
    iris_zone2_documents_url: iris_zone2_documents_url
    // Agent IDs
    triage_agent_id: triage_agent_id
    lumi_agent_id: lumi_agent_id
    sciences_agent_id: sciences_agent_id
    governance_agent_id: governance_agent_id
    analytics_agent_id: analytics_agent_id
    experience_agent_id: experience_agent_id
    translation_agent_id: translation_agent_id
    head_support_agent_id: head_support_agent_id
  }
  dependsOn: [
    role_assignments
  ]
}

// ============ Outputs ============
output WEB_APP_URL string = container_app.outputs.url
output WEB_APP_FQDN string = container_app.outputs.fqdn
output CONTAINER_APP_NAME string = container_app.outputs.name
output AI_FOUNDRY_NAME string = ai_foundry.outputs.name
output SEARCH_SERVICE_ENDPOINT string = search_service.outputs.endpoint
output STORAGE_ACCOUNT_NAME string = storage_account.outputs.name

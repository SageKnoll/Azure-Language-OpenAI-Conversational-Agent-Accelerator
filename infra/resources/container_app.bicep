@description('Resource name suffix.')
param suffix string

@description('Name of Container App resource.')
param name string = 'ca-svo-convo-${suffix}'

@description('Location for all resources.')
param location string = resourceGroup().location

// ============ Container Apps Environment ============
@description('Name of existing Container Apps Environment.')
param container_apps_environment_name string

@description('Resource group of Container Apps Environment (if different).')
param container_apps_environment_rg string = resourceGroup().name

// ============ Language Service Parameters ============
param language_endpoint string

@description('CLU project name')
param clu_project_name string = 'sagevia-osha-clu'

@description('CLU model name')
param clu_model_name string = 'clu-m1'

@description('CLU deployment name')
param clu_deployment_name string = 'production'

@description('CLU confidence threshold')
param clu_confidence_threshold string = '0.7'

@description('CQA project name')
param cqa_project_name string = 'sagevia-osha-cqa'

@description('CQA deployment name')
param cqa_deployment_name string = 'production'

@description('CQA confidence threshold')
param cqa_confidence_threshold string = '0.8'

@description('Orchestration project name')
param orchestration_project_name string = 'sagevia-osha-orchestration'

@description('Orchestration model name')
param orchestration_model_name string = 'orch-m1'

@description('Orchestration deployment name')
param orchestration_deployment_name string = 'production'

@description('Orchestration confidence threshold')
param orchestration_confidence_threshold string = '0.7'

// ============ PII Parameters ============
@description('Enable PII redaction')
param pii_enabled string = 'true'

@description('PII categories to redact')
param pii_categories string = 'person,organization,address,phonenumber'

@description('PII confidence threshold')
param pii_confidence_threshold string = '0.7'

// ============ Translation Parameters ============
param translator_resource_id string
param translator_region string = location

// ============ Search/AOAI Parameters ============
param aoai_endpoint string
param aoai_deployment string
param embedding_deployment_name string
param embedding_model_name string
param embedding_model_dimensions int

param storage_account_name string
param storage_account_connection_string string
param blob_container_name string = 'osha-knowledge-files'

param search_endpoint string
param search_index_name string = 'sagevia-osha-knowledge-idx'

// ============ Agents Parameters ============
param agents_project_endpoint string
param delete_old_agents string = 'false'
param max_agent_retry string = '5'

// ============ IRIS Symphony Zone API URLs ============
@description('Zone 1 eCFR Search API URL')
param iris_zone1_ecfr_url string = ''

@description('Zone 1 Recordability Engine URL')
param iris_zone1_recordability_url string = ''

@description('Zone 1 Analytics API URL')
param iris_zone1_analytics_url string = ''

@description('Zone 2 Incidents API URL')
param iris_zone2_incidents_url string = ''

@description('Zone 2 Documents API URL')
param iris_zone2_documents_url string = ''

// ============ Agent IDs (from run_agent_setup.sh) ============
param triage_agent_id string = ''
param lumi_agent_id string = ''
param sciences_agent_id string = ''
param governance_agent_id string = ''
param analytics_agent_id string = ''
param experience_agent_id string = ''
param translation_agent_id string = ''
param head_support_agent_id string = ''

// ============ App Configuration ============
@allowed([
  'BYPASS'
  'CLU'
  'CQA'
  'ORCHESTRATION'
  'FUNCTION_CALLING'
  'TRIAGE_AGENT'
])
param router_type string = 'ORCHESTRATION'

@allowed([
  'SEMANTIC_KERNEL'
  'UNIFIED'
])
param app_mode string = 'SEMANTIC_KERNEL'

@description('Container image to deploy')
param image string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container port')
param port int = 8000

@description('CPU cores for container')
param cpu string = '0.5'

@description('Memory for container')
param memory string = '1Gi'

@description('Minimum replicas')
param minReplicas int = 0

@description('Maximum replicas')
param maxReplicas int = 3

// ============ Managed Identity ============
@description('Name of managed identity to use for Container App.')
param managed_identity_name string

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managed_identity_name
}

// ============ Container Apps Environment (Create New) ============
resource container_apps_environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-iris-${suffix}'
  location: location
  properties: {
    zoneRedundant: false
  }
}

// ============ Container App Resource ============
resource container_app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managed_identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: container_apps_environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: port
        transport: 'http'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: []
      secrets: [
        {
          name: 'storage-connection-string'
          value: storage_account_connection_string
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'convo-agent'
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            // ============ Agent Configuration ============
            {
              name: 'AGENTS_PROJECT_ENDPOINT'
              value: agents_project_endpoint
            }
            {
              name: 'DELETE_OLD_AGENTS'
              value: delete_old_agents
            }
            {
              name: 'MAX_AGENT_RETRY'
              value: max_agent_retry
            }
            // ============ Authentication ============
            {
              name: 'USE_MI_AUTH'
              value: 'true'
            }
            {
              name: 'MI_CLIENT_ID'
              value: managed_identity.properties.clientId
            }
            // ============ Azure OpenAI ============
            {
              name: 'AOAI_ENDPOINT'
              value: aoai_endpoint
            }
            {
              name: 'AOAI_DEPLOYMENT'
              value: aoai_deployment
            }
            // ============ Translation ============
            {
              name: 'TRANSLATOR_RESOURCE_ID'
              value: translator_resource_id
            }
            {
              name: 'TRANSLATOR_REGION'
              value: translator_region
            }
            // ============ Azure AI Search ============
            {
              name: 'SEARCH_ENDPOINT'
              value: search_endpoint
            }
            {
              name: 'SEARCH_INDEX_NAME'
              value: search_index_name
            }
            // ============ Embeddings ============
            {
              name: 'EMBEDDING_DEPLOYMENT_NAME'
              value: embedding_deployment_name
            }
            {
              name: 'EMBEDDING_MODEL_NAME'
              value: embedding_model_name
            }
            {
              name: 'EMBEDDING_MODEL_DIMENSIONS'
              value: string(embedding_model_dimensions)
            }
            // ============ Storage ============
            {
              name: 'STORAGE_ACCOUNT_NAME'
              value: storage_account_name
            }
            {
              name: 'STORAGE_ACCOUNT_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
            }
            {
              name: 'BLOB_CONTAINER_NAME'
              value: blob_container_name
            }
            // ============ Language Service ============
            {
              name: 'LANGUAGE_ENDPOINT'
              value: language_endpoint
            }
            // ============ CLU ============
            {
              name: 'CLU_PROJECT_NAME'
              value: clu_project_name
            }
            {
              name: 'CLU_MODEL_NAME'
              value: clu_model_name
            }
            {
              name: 'CLU_DEPLOYMENT_NAME'
              value: clu_deployment_name
            }
            {
              name: 'CLU_CONFIDENCE_THRESHOLD'
              value: clu_confidence_threshold
            }
            // ============ CQA ============
            {
              name: 'CQA_PROJECT_NAME'
              value: cqa_project_name
            }
            {
              name: 'CQA_DEPLOYMENT_NAME'
              value: cqa_deployment_name
            }
            {
              name: 'CQA_CONFIDENCE_THRESHOLD'
              value: cqa_confidence_threshold
            }
            // ============ Orchestration ============
            {
              name: 'ORCHESTRATION_PROJECT_NAME'
              value: orchestration_project_name
            }
            {
              name: 'ORCHESTRATION_MODEL_NAME'
              value: orchestration_model_name
            }
            {
              name: 'ORCHESTRATION_DEPLOYMENT_NAME'
              value: orchestration_deployment_name
            }
            {
              name: 'ORCHESTRATION_CONFIDENCE_THRESHOLD'
              value: orchestration_confidence_threshold
            }
            // ============ PII ============
            {
              name: 'PII_ENABLED'
              value: pii_enabled
            }
            {
              name: 'PII_CATEGORIES'
              value: pii_categories
            }
            {
              name: 'PII_CONFIDENCE_THRESHOLD'
              value: pii_confidence_threshold
            }
            // ============ Router Configuration ============
            {
              name: 'ROUTER_TYPE'
              value: router_type
            }
            {
              name: 'APP_MODE'
              value: app_mode
            }
            // ============ IRIS Symphony Zone 1 APIs ============
            {
              name: 'IRIS_ZONE1_ECFR_URL'
              value: iris_zone1_ecfr_url
            }
            {
              name: 'IRIS_ZONE1_RECORDABILITY_URL'
              value: iris_zone1_recordability_url
            }
            {
              name: 'IRIS_ZONE1_ANALYTICS_URL'
              value: iris_zone1_analytics_url
            }
            // ============ Agent IDs ============
            {
              name: 'TRIAGE_AGENT_ID'
              value: triage_agent_id
            }
            {
              name: 'LUMI_AGENT_ID'
              value: lumi_agent_id
            }
            {
              name: 'SCIENCES_AGENT_ID'
              value: sciences_agent_id
            }
            {
              name: 'GOVERNANCE_AGENT_ID'
              value: governance_agent_id
            }
            {
              name: 'ANALYTICS_AGENT_ID'
              value: analytics_agent_id
            }
            {
              name: 'EXPERIENCE_AGENT_ID'
              value: experience_agent_id
            }
            {
              name: 'TRANSLATION_AGENT_ID'
              value: translation_agent_id
            }
            {
              name: 'HEAD_SUPPORT_AGENT_ID'
              value: head_support_agent_id
            }
            // ============ IRIS Symphony Zone 2 APIs ============
            {
              name: 'IRIS_ZONE2_INCIDENTS_URL'
              value: iris_zone2_incidents_url
            }
            {
              name: 'IRIS_ZONE2_DOCUMENTS_URL'
              value: iris_zone2_documents_url
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// ============ Outputs ============
output name string = container_app.name
output fqdn string = container_app.properties.configuration.ingress.fqdn
output url string = 'https://${container_app.properties.configuration.ingress.fqdn}'

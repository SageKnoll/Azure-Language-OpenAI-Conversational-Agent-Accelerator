@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of managed identity to use for scripts.')
param managed_identity_name string

@description('URL to clone repo.')
param repo_clone_url string

// Language setup:
param language_endpoint string
param clu_project_name string = 'conv-assistant-clu'
param clu_model_name string = 'clu-m1'
param clu_deployment_name string = 'clu-m1-d1'
param cqa_project_name string = 'conv-assistant-cqa'
param cqa_deployment_name string = 'production'
param orchestration_project_name string = 'conv-assistant-orch'
param orchestration_model_name string = 'orch-m1'
param orchestration_deployment_name string = 'orch-m1-d1'

// Search setup:
param aoai_endpoint string
param embedding_deployment_name string
param embedding_model_name string
param embedding_model_dimensions int
param storage_account_name string
param storage_account_connection_string string
param blob_container_name string
param search_endpoint string
param search_index_name string = 'conv-assistant-manuals-idx'

// Registry setup:
param tag string = utcNow()
param acr_name string
param repo string = 'conv-agent/app'

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managed_identity_name
}

resource container_group 'Microsoft.ContainerInstance/containerGroups@2024-11-01-preview' = {
  name: 'data_plane_scripts'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managed_identity.id}' : {}
    }
  }
  properties: {
    containers: [
      {
        name: 'run_setup'
        properties: {
          image: 'mcr.microsoft.com/azure-cli:cbl-mariner2.0'
          command: [
            'az login --identity'
            'tdnf install -y git'
            'git clone ${repo_clone_url} --branch murraysean/update-scripts --single-branch repo_src && cd repo_src' // TODO: need to update reference to fork, then back to repo
            'bash infra/scripts/language/run_language_setup.sh'
            'bash infra/scripts/search/run_search_setup.sh ${storage_account_name} ${blob_container_name}'
            'bash infra/scripts/registry/run_registry_setup.sh ${acr_name} ${repo} ${tag}'
            'exit'
          ]
          environmentVariables: [
            {
              name: 'LANGUAGE_ENDPOINT'
              value: language_endpoint
            }
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
              name: 'CQA_PROJECT_NAME'
              value: cqa_project_name
            }
            {
              name: 'CQA_DEPLOYMENT_NAME'
              value: cqa_deployment_name
            }
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
              name: 'AOAI_ENDPOINT'
              value: aoai_endpoint
            }
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
            {
              name: 'STORAGE_ACCOUNT_CONNECTION_STRING'
              value: storage_account_connection_string
            }
            {
              name: 'BLOB_CONTAINER_NAME'
              value: blob_container_name
            }
            {
              name: 'SEARCH_ENDPOINT'
              value: search_endpoint
            }
            {
              name: 'SEARCH_INDEX_NAME'
              value: search_index_name
            }
          ]
          resources: {
            requests: {
              cpu: 1
              memoryInGB: 1
            }
          }
        }
      }
    ]
    osType: 'Linux'
  }
}

// Language setup output:
output clu_project_name string = clu_project_name
output clu_deployment_name string = clu_deployment_name
output cqa_project_name string = cqa_project_name
output cqa_deployment_name string = cqa_deployment_name
output orchestration_project_name string = orchestration_project_name
output orchestration_deployment_name string = orchestration_deployment_name

// Search setup output:
output search_index_name string = search_index_name

// Registry setup output:
output image string = '${acr_name}.azurecr.io/${repo}:${tag}'

@description('Location for all resources.')
param location string = resourceGroup().location

param aoai_endpoint string
param embedding_deployment_name string
param embedding_model_name string
param embedding_model_dimensions int

param storage_account_name string
param storage_account_connection_string string
param blob_container_name string

param search_endpoint string
param search_index_name string = 'conv-assistant-manuals-idx'

@description('Name of managed identity to use for deployment script.')
param managed_identity_name string

@description('Base url of GitHub repo.')
param base_url string

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managed_identity_name
}

resource search_setup_script 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'search_setup_script'
  location: location
  kind: 'AzureCLI'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managed_identity.id}' : {}
    }
  }
  properties: {
    azCliVersion: '2.50.0'
    primaryScriptUri: '${base_url}infra/scripts/search/run_search_setup.sh'
    arguments: 'false ${storage_account_name} ${blob_container_name} ${base_url}'
    timeout: 'PT1H'
    retentionInterval: 'PT1H'
    cleanupPreference: 'OnSuccess'
    environmentVariables: [
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
  }
}

output search_index_name string = search_index_name

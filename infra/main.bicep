// ========== main.bicep ========== //
targetScope = 'resourceGroup'

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

@description('Name of Embedding model to deploy.')
@allowed([
  'text-embedding-ada-002'
  'text-embedding-3-small'
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

var suffix = uniqueString(subscription().id, resourceGroup().id, resourceGroup().location)

// Deploy resources:
module storage_account 'resources/storage_account.bicep' = {
  name: 'deploy_storage_account'
  params: {
    suffix: suffix
  }
}

module openai_service 'resources/openai_service.bicep' = {
  name: 'deploy_openai_service'
  params: {
    suffix: suffix
    gpt_model_name: gpt_model_name
    gpt_deployment_capacity: gpt_deployment_capacity
    gpt_deployment_type: gpt_deployment_type
    embedding_model_name: embedding_model_name
    embedding_deployment_capacity: embedding_deployment_capacity
    embedding_deployment_type: embedding_deployment_type
  }
}

module search_service 'resources/search_service.bicep' = {
  name: 'deploy_search_service'
  params: {
    suffix: suffix
    storage_account_name: storage_account.outputs.name
    openai_service_name: openai_service.outputs.name
  }
}

module language_service 'resources/language_service.bicep' = {
  name: 'deploy_language_service'
  params: {
    suffix: suffix
    search_service_name: search_service.outputs.name
  }
}

module managed_identity 'resources/managed_identity.bicep' = {
  name: 'deploy_managed_identity'
  params: {
    suffix: suffix
    language_service_name: language_service.outputs.name
    openai_service_name: openai_service.outputs.name
    search_service_name: search_service.outputs.name
    storage_account_name: storage_account.outputs.name
  }
}

// Deploy container app:
module container_group 'resources/container_group.bicep' = {
  name: 'deploy_container_group'
  params: {
    suffix: suffix
    aoai_deployment: openai_service.outputs.gpt_deployment_name
    aoai_endpoint: openai_service.outputs.endpoint
    language_endpoint: language_service.outputs.endpoint
    managed_identity_name: managed_identity.outputs.name
    search_endpoint: search_service.outputs.endpoint
    blob_container_name: storage_account.outputs.blob_container_name
    embedding_deployment_name: openai_service.outputs.embedding_deployment_name
    embedding_model_dimensions: openai_service.outputs.embedding_model_dimensions
    embedding_model_name: openai_service.outputs.embedding_model_name
    storage_account_connection_string: storage_account.outputs.connection_string
    storage_account_name: storage_account.outputs.name
  }
}

output WEB_APP_URL string = container_group.outputs.fqdn

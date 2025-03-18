@description('Name of AI Search resource.')
param name string = 'srch-${uniqueString(resourceGroup().id)}'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of Storage Account resource')
param storage_account_name string

@description('Name of OpenAI Service resource.')
param openai_service_name string

//-----------Search Service-----------//
resource search_service 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    disableLocalAuth: false // CQA can only auth to search service using API key...
    semanticSearch: 'free'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      bypass: 'AzureServices'
      ipRules: []
    }
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
  sku: {
    name: 'basic'
  }
}

//-----------Storage Account Role Assignments-----------//
resource storage_account 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storage_account_name
}

resource storage_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage_account.id, search_service.id, storage_blob_data_reader_role.id)
  scope: storage_account
  properties: {
    principalId: search_service.identity.principalId
    roleDefinitionId: storage_blob_data_reader_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Storage Blob Data Reader role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-reader).')
resource storage_blob_data_reader_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
    name: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
}

//-----------OpenAI Service Role Assignments-----------//
resource openai_service 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openai_service_name
}

resource openai_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openai_service.id, search_service.id, cognitive_services_openai_contributor_role.id)
  scope: openai_service
  properties: {
    principalId: search_service.identity.principalId
    roleDefinitionId: cognitive_services_openai_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Cognitive Services OpenAI Contributor role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning#cognitive-services-openai-contributor).')
resource cognitive_services_openai_contributor_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
}

//-----------Outputs-----------//
output name string = search_service.name
output endpoint string = 'https://${search_service.name}.search.windows.net'

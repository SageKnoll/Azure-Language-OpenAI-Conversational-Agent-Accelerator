@description('Name of Managed Identity resource.')
param name string = 'id-${uniqueString(resourceGroup().id)}'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of Storage Account resource.')
param storage_account_name string

@description('Name of Search Service resource.')
param search_service_name string

@description('Name of OpenAI Service resource.')
param openai_service_name string

@description('Name of Language Service resource.')
param language_service_name string

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
}

//-----------Storage Account Role Assignments-----------//
resource storage_account 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storage_account_name
}

resource storage_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage_account.id, managed_identity.id, storage_blob_data_contributor_role.id)
  scope: storage_account
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: storage_blob_data_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Storage Blob Data Contributor role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-contributor).')
resource storage_blob_data_contributor_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
    name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

//-----------Search Service Role Assignments-----------//
resource search_service 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: search_service_name
}

resource search_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search_service.id, managed_identity.id, search_index_data_contributor_role.id)
  scope: search_service
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: search_index_data_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

resource search_contributor_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search_service.id, managed_identity.id, search_contributor_role.id)
  scope: search_service
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: search_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

resource search_contributor_role 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  name: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
}

@description('Built-in Search Index Data Contributor role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning#search-index-data-contributor).')
resource search_index_data_contributor_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
}

//-----------OpenAI Service Role Assignments-----------//
resource openai_service 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openai_service_name
}

resource openai_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openai_service.id, managed_identity.id, cognitive_services_openai_contributor_role.id)
  scope: openai_service
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: cognitive_services_openai_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Cognitive Services OpenAI Contributor role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning#cognitive-services-openai-contributor).')
resource cognitive_services_openai_contributor_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
}

//-----------Language Service Role Assignments-----------//
resource language_service 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: language_service_name
}

resource language_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(language_service.id, managed_identity.id, cognitive_services_language_owner_role.id)
  scope: language_service
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: cognitive_services_language_owner_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Cognitive Services Language Owner role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning#cognitive-services-language-owner).')
resource cognitive_services_language_owner_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: 'f07febfe-79bc-46b1-8b37-790e26e6e498'
}

//-----------Outputs-----------//
output name string = managed_identity.name

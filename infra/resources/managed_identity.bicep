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

@description('Name of Container Registry resource.')
param container_registry_name string

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

//-----------Container Registry Role Assignments-----------//
resource container_registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: container_registry_name
}

resource acr_pull_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container_registry.id, managed_identity.id, acr_pull_role.id)
  scope: container_registry
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: acr_pull_role.id
    principalType: 'ServicePrincipal'
  }
}

resource acr_push_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container_registry.id, managed_identity.id, acr_push_role.id)
  scope: container_registry
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: acr_push_role.id
    principalType: 'ServicePrincipal'
  }
}

resource acr_task_contributor_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container_registry.id, managed_identity.id, acr_task_contributor_role.id)
  scope: container_registry
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: acr_task_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

resource acr_contributor_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container_registry.id, managed_identity.id, acr_contributor_role.id)
  scope: container_registry
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: acr_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

resource acr_task_contributor_role 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  name: 'fb382eab-e894-4461-af04-94435c366c3f'
}

resource acr_contributor_role 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  name: '3bc748fc-213d-45c1-8d91-9da5725539b9'
}

@description('Built-in Acr Pull role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/containers#acrpull).')
resource acr_pull_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
    name: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
}

@description('Built-in Acr Push role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/containers#acrpush).')
resource acr_push_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
    name: '8311e382-0749-4cb8-b61a-304f252e45ec'
}

//-----------Outputs-----------//
output name string = managed_identity.name

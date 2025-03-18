@description('Name of Language Service resource.')
param name string = 'lang-${uniqueString(resourceGroup().id)}'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of AI Search resource')
param search_service_name string

resource search_service 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: search_service_name
}

resource language_service 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  kind: 'TextAnalytics'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    disableLocalAuth: true
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    apiProperties: {
      qnaAzureSearchEndpointId: search_service.id
      qnaAzureSearchEndpointKey: search_service.listAdminKeys().primaryKey
    }
  }
  sku: {
    name: 'S'
  }
}

resource search_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search_service.id, language_service.id, search_index_data_contributor_role.id)
  scope: search_service
  properties: {
    principalId: language_service.identity.principalId
    roleDefinitionId: search_index_data_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Search Index Data Contributor role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning#search-index-data-contributor).')
resource search_index_data_contributor_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
}

output name string = language_service.name
output endpoint string = language_service.properties.endpoint

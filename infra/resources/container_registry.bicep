@description('Name of Container Registry resource.')
param name string = 'acr${uniqueString(resourceGroup().id)}'

@description('Location for all resources.')
param location string = resourceGroup().location

resource container_registry 'Microsoft.ContainerRegistry/registries@2024-11-01-preview' = {
  name: name
  location: location
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
  sku: {
    name: 'Basic'
  }
}

output name string = container_registry.name

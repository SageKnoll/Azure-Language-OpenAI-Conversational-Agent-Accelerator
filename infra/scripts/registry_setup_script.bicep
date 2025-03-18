@description('Location for all resources.')
param location string = resourceGroup().location

param tag string = utcNow()
param acr_name string
param repo string = 'conv-agent/app'
param clone_url string

@description('Name of managed identity to use for deployment script.')
param managed_identity_name string

@description('Base url of GitHub repo.')
param base_url string

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managed_identity_name
}

resource registry_setup_script 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'registry_setup_script'
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
    primaryScriptUri: '${base_url}infra/scripts/registry/run_registry_setup.sh'
    arguments: 'false ${acr_name} ${repo} ${tag} ${clone_url}'
    timeout: 'PT1H'
    retentionInterval: 'PT1H'
    cleanupPreference: 'OnSuccess'
  }
}

output image string = '${acr_name}.azurecr.io/${repo}:${tag}'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of CLU project.')
param clu_project_name string = 'conv-assistant-clu'
@description('Name of CLU model.')
param clu_model_name string = 'clu-m1'
@description('Name of CLU deployment.')
param clu_deployment_name string = 'clu-m1-d1'

@description('Name of CQA project.')
param cqa_project_name string = 'conv-assistant-cqa'
@description('Name of CQA deployment.')
param cqa_deployment_name string = 'production'

@description('Name of Orchestration project.')
param orchestration_project_name string = 'conv-assistant-orch'
@description('Name of Orchestration model.')
param orchestration_model_name string = 'orch-m1'
@description('Name of Orchestration deployment.')
param orchestration_deployment_name string = 'orch-m1-d1'

@description('Endpoint of Language Service.')
param language_endpoint string

@description('Name of managed identity to use for deployment script.')
param managed_identity_name string

@description('Base url of GitHub repo.')
param base_url string

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managed_identity_name
}

resource language_setup_script 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'language_setup_script'
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
    primaryScriptUri: '${base_url}infra/scripts/language/run_language_setup.sh'
    arguments: 'false ${base_url}'
    timeout: 'PT1H'
    retentionInterval: 'PT1H'
    cleanupPreference: 'OnSuccess'
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
    ]
  }
}

output clu_project_name string = clu_project_name
output clu_deployment_name string = clu_deployment_name

output cqa_project_name string = cqa_project_name
output cqa_deployment_name string = cqa_deployment_name

output orchestration_project_name string = orchestration_project_name
output orchestration_deployment_name string = orchestration_deployment_name

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of managed identity to use for Container Apps.')
param managed_identity_name string

param acr_name string

param image string
param port int = 7000

param aoai_endpoint string
param aoai_deployment string

param search_endpoint string
param search_index_name string

param language_endpoint string

param clu_project_name string
param clu_deployment_name string
param clu_confidence_threshold string = '0.5'

param cqa_project_name string
param cqa_deployment_name string
param cqa_confidence_threshold string = '0.5'

param orchestration_project_name string
param orchestration_deployment_name string
param orchestration_confidence_threshold string = '0.5'

param pii_enabled string = 'true'
param pii_categories string = 'organization,person'
param pii_confidence_threshold string = '0.5'

@allowed([
  'BYPASS'
  'CLU'
  'CQA'
  'ORCHESTRATION'
  'FUNCTION_CALLING'
])
param router_type string = 'ORCHESTRATION'

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managed_identity_name
}

resource conv_agent_app 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: 'ca-conv-agent-app'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managed_identity.id}' : {}
    }
  }
  properties: {
    configuration: {
      identitySettings: [
        {
          identity: managed_identity.id
          lifecycle: 'All'
        }
      ]
      ingress: {
        external: true
        targetPort: port
      }
      registries: [
        {
          identity: managed_identity.id
          server: '${acr_name}.azurecr.io'
        }
      ]
    }
    template: {
      containers: [
        {
          env: [
            {
              name: 'AOAI_ENDPOINT'
              value: aoai_endpoint
            }
            {
              name: 'AOAI_DEPLOYMENT'
              value: aoai_deployment
            }
            {
              name: 'SEARCH_ENDPOINT'
              value: search_endpoint
            }
            {
              name: 'SEARCH_INDEX_NAME'
              value: search_index_name
            }
            {
              name: 'LANGUAGE_ENDPOINT'
              value: language_endpoint
            }
            {
              name: 'CLU_PROJECT_NAME'
              value: clu_project_name
            }
            {
              name: 'CLU_DEPLOYMENT_NAME'
              value: clu_deployment_name
            }
            {
              name: 'CLU_CONFIDENCE_THRESHOLD'
              value: clu_confidence_threshold
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
              name: 'CQA_CONFIDENCE_THRESHOLD'
              value: cqa_confidence_threshold
            }
            {
              name: 'ORCHESTRATION_PROJECT_NAME'
              value: orchestration_project_name
            }
            {
              name: 'ORCHESTRATION_DEPLOYMENT_NAME'
              value: orchestration_deployment_name
            }
            {
              name: 'ORCHESTRATION_CONFIDENCE_THRESHOLD'
              value: orchestration_confidence_threshold
            }
            {
              name: 'PII_ENABLED'
              value: pii_enabled
            }
            {
              name: 'PII_CATEGORIES'
              value: pii_categories
            }
            {
              name: 'PII_CONFIDENCE_THRESHOLD'
              value: pii_confidence_threshold
            }
            {
              name: 'ROUTER_TYPE'
              value: router_type
            }
            {
              name: 'USE_MI_AUTH'
              value: 'true'
            }
            {
              name: 'MI_CLIENT_ID'
              value: managed_identity.properties.clientId
            }
          ]
          image: image
          imageType: 'ContainerImage'
          name: 'conv-agent-app'
          resources: {
            cpu: 1
            memory: '2Gi'
          }
        }
      ]
      scale: {
        maxReplicas: 1
        minReplicas: 1
      }
    }
  }
}

output fqdn string = conv_agent_app.properties.configuration.ingress.fqdn

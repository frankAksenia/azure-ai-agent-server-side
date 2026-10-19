param aiFoundryName string
param location string
param principalIds array = []

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2026-07-01' = {
  name: aiFoundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    allowProjectManagement: true
    customSubDomainName: aiFoundryName
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
  }
}

resource foundryUsers 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in principalIds: {
  scope: aiFoundry
  name: guid(aiFoundry.id, principalId, 'foundry-user')
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')
  }
}]

resource modelUsers 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in principalIds: {
  scope: aiFoundry
  name: guid(aiFoundry.id, principalId, 'openai-user')
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}]

output aiFoundryName string = aiFoundry.name
output openAiEndpoint string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/openai/v1'

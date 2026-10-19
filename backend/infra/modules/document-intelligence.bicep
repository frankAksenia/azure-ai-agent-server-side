param name string
param location string
param skuName string = 'S0'
param principalIds array = []

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: name
  location: location
  kind: 'FormRecognizer'

  sku: {
    name: skuName
  }

  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }

  tags: {
    environment: 'dev'
    project: 'azure-ai-agent-server-side'
  }
}

resource users 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in principalIds: {
  scope: documentIntelligence
  name: guid(documentIntelligence.id, principalId, 'cognitive-services-user')
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
  }
}]

output id string = documentIntelligence.id
output name string = documentIntelligence.name
output endpoint string = 'https://${name}.cognitiveservices.azure.com/'

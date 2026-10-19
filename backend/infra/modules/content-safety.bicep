param contentSafetyName string
param location string
param principalIds array = []

resource contentSafety 'Microsoft.CognitiveServices/accounts@2026-07-01' = {
  name: contentSafetyName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'ContentSafety'
  properties: {
    customSubDomainName: contentSafetyName
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

resource users 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in principalIds: {
  scope: contentSafety
  name: guid(contentSafety.id, principalId, 'cognitive-services-user')
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
  }
}]

output contentSafetyName string = contentSafety.name
output contentSafetyEndpoint string = 'https://${contentSafety.properties.customSubDomainName}.cognitiveservices.azure.com/'

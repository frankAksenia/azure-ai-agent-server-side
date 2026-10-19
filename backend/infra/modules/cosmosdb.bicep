param accountName string
param databaseName string
param containerName string
param location string

param throughput int = 400
param serverless bool = false

@description('Must match the existing account; Azure does not allow changing free tier after creation.')
param enableFreeTier bool = !serverless

param writerPrincipalIds array = []
param readerPrincipalIds array = []

var vectorEmbeddingPolicy = loadJsonContent('../cosmosdb/vector-embedding-policy.json')
var indexingPolicy = loadJsonContent('../cosmosdb/indexing-policy.json')

resource account 'Microsoft.DocumentDB/databaseAccounts@2025-04-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: enableFreeTier
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: concat([
      { name: 'EnableNoSQLVectorSearch' }
    ], serverless ? [{ name: 'EnableServerless' }] : [])
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-04-15' = {
  parent: account
  name: databaseName
  properties: {
    resource: { id: databaseName }
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-04-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: ['/domain']
        kind: 'Hash'
      }
      vectorEmbeddingPolicy: vectorEmbeddingPolicy
      indexingPolicy: indexingPolicy
    }
    options: serverless ? {} : { throughput: throughput }
  }
}

resource writerAssignments 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2025-04-15' = [for principalId in writerPrincipalIds: {
  parent: account
  name: guid(account.id, principalId, 'cosmos-data-contributor')
  properties: {
    principalId: principalId
    roleDefinitionId: '${account.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    scope: account.id
  }
}]

resource readerAssignments 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2025-04-15' = [for principalId in readerPrincipalIds: {
  parent: account
  name: guid(account.id, principalId, 'cosmos-data-reader')
  properties: {
    principalId: principalId
    roleDefinitionId: '${account.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000001'
    scope: account.id
  }
}]

output endpoint string = account.properties.documentEndpoint
output databaseName string = database.name
output containerName string = container.name

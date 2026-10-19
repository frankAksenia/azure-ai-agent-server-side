param aiFoundryName string = 'default'

param aiProjectName string = '${aiFoundryName}-proj'

param contentSafetyName string = '${aiFoundryName}-content-safety'

param location string = resourceGroup().location

param llm_model string = 'gpt-5.1'
param llm_model_version string = '2025-11-13'

param slm_model string = 'gpt-4.1'
param slm_model_version string = '2025-04-14'

param embedding_model string = 'text-embedding-3-small'
param embedding_model_version string = '1'

param documentIntelligenceName string = 'azure-agent-doc-intelligence'

param documentIntelligenceSku string = 'S0'

param cosmosAccountName string = 'azure-agent-rag-cosmos'
param cosmosDatabaseName string = 'agent-knowledge'
param cosmosContainerName string = 'knowledge'
param cosmosServerless bool = false

param cosmosFreeTier bool = !cosmosServerless

param cosmosThroughput int = 400

@description('Object ID of the developer or managed identity that indexes PDFs. Leave empty to manage access separately.')
param indexerPrincipalId string = ''

@description('Object ID of the managed identity that runs FastAPI. Leave empty to manage access separately.')
param runtimePrincipalId string = ''

var applicationPrincipalIds = union(
  empty(indexerPrincipalId) ? [] : [indexerPrincipalId],
  empty(runtimePrincipalId) ? [] : [runtimePrincipalId]
)

module aiFoundry './modules/ai-foundry.bicep' = {
  name: 'deploy-ai-foundry'
  params: {
    aiFoundryName: aiFoundryName
    location: location
    principalIds: applicationPrincipalIds
  }
}

module aiProject './modules/ai-project.bicep' = {
  name: 'deploy-ai-project'
  params: {
    aiFoundryName: aiFoundryName
    aiProjectName: aiProjectName
    location: location
  }
  dependsOn: [
    aiFoundry
  ]
}

module llmDeployment './modules/model-deployment.bicep' = {
  name: 'deploy-llm-model'
  params: {
    aiFoundryName: aiFoundryName
    deploymentName: llm_model
    modelName: llm_model
    modelFormat: 'OpenAI'
    modelVersion: llm_model_version
    skuName: 'GlobalStandard'
    capacity: 1
  }
  dependsOn: [
    aiFoundry
  ]
}

module slmDeployment './modules/model-deployment.bicep' = {
  name: 'deploy-slm-model'
  params: {
    aiFoundryName: aiFoundryName
    deploymentName: slm_model
    modelName: slm_model
    modelFormat: 'OpenAI'
    modelVersion: slm_model_version
    skuName: 'GlobalStandard'
    capacity: 1
  }
  dependsOn: [
    llmDeployment
  ]
}

module embeddingDeployment './modules/model-deployment.bicep' = {
  name: 'deploy-embedding-model'
  params: {
    aiFoundryName: aiFoundryName
    deploymentName: embedding_model
    modelName: embedding_model
    modelFormat: 'OpenAI'
    modelVersion: embedding_model_version
    skuName: 'GlobalStandard'
    capacity: 1
  }
  dependsOn: [
    slmDeployment
  ]
}

module contentSafety './modules/content-safety.bicep' = {
  name: 'deploy-content-safety'
  params: {
    contentSafetyName: contentSafetyName
    location: location
    principalIds: empty(runtimePrincipalId) ? [] : [runtimePrincipalId]
  }
}

module documentIntelligence './modules/document-intelligence.bicep' = {
  name: 'document-intelligence-deployment'
  params: {
    name: documentIntelligenceName
    location: location
    skuName: documentIntelligenceSku
    principalIds: empty(indexerPrincipalId) ? [] : [indexerPrincipalId]
  }
}

module cosmos './modules/cosmosdb.bicep' = {
  name: 'deploy-cosmos-vector-store'
  params: {
    accountName: cosmosAccountName
    databaseName: cosmosDatabaseName
    containerName: cosmosContainerName
    location: location
    throughput: cosmosThroughput
    serverless: cosmosServerless
    enableFreeTier: cosmosFreeTier
    writerPrincipalIds: empty(indexerPrincipalId) ? [] : [indexerPrincipalId]
    readerPrincipalIds: empty(runtimePrincipalId) || runtimePrincipalId == indexerPrincipalId ? [] : [runtimePrincipalId]
  }
}

output AZURE_PROJECT_ENDPOINT string = 'https://${aiFoundryName}.services.ai.azure.com/api/projects/${aiProjectName}'
output AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT string = documentIntelligence.outputs.endpoint
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT string = embeddingDeployment.outputs.deploymentName
output AZURE_COSMOS_ENDPOINT string = cosmos.outputs.endpoint
output AZURE_COSMOS_DATABASE string = cosmos.outputs.databaseName
output AZURE_COSMOS_CONTAINER string = cosmos.outputs.containerName
output OPENAI_ENDPOINT string = aiFoundry.outputs.openAiEndpoint
output LLM_MODEL_DEPLOYMENT_NAME string = llmDeployment.outputs.deploymentName
output SLM_MODEL_DEPLOYMENT_NAME string = slmDeployment.outputs.deploymentName
output CONTENT_SAFETY_ENDPOINT string = contentSafety.outputs.contentSafetyEndpoint

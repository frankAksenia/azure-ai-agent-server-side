param aiFoundryName string = 'default'
param aiProjectName string = '${aiFoundryName}-proj'
param contentSafetyName string = '${aiFoundryName}-content-safety'
param location string = resourceGroup().location

param llm_model string = 'gpt-5.1'
param llm_model_version string = '2025-11-13'
param slm_model string = 'gpt-4.1'
param slm_model_version string = '2025-04-14'


module aiFoundry './modules/ai-foundry.bicep' = {
  name: 'deploy-ai-foundry'
  params: {
    aiFoundryName: aiFoundryName
    location: location
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

module contentSafety './modules/content-safety.bicep' = {
  name: 'deploy-content-safety'
  params: {
    contentSafetyName: contentSafetyName
    location: location
  }
}

output OPENAI_ENDPOINT string = aiFoundry.outputs.openAiEndpoint
output LLM_MODEL_DEPLOYMENT_NAME string = llmDeployment.outputs.deploymentName
output SLM_MODEL_DEPLOYMENT_NAME string = slmDeployment.outputs.deploymentName
output CONTENT_SAFETY_ENDPOINT string = contentSafety.outputs.contentSafetyEndpoint


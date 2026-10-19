RESOURCE_GROUP ?= rg-seversideagent-dev
LOCATION ?= swedencentral
AI_FOUNDRY_NAME ?= fndry-seversideagent-dev
INDEXER_PRINCIPAL_ID ?=
RUNTIME_PRINCIPAL_ID ?=
PYTHON ?= python

TEMPLATE_FILE = infra/main.bicep
DEPLOYMENT_NAME = foundry-resources-v2

DEPLOY_PARAMETERS = aiFoundryName=$(AI_FOUNDRY_NAME) \
	indexerPrincipalId='$(INDEXER_PRINCIPAL_ID)' \
	runtimePrincipalId='$(RUNTIME_PRINCIPAL_ID)'

.DEFAULT_GOAL := help
.PHONY: help install seed rag-index agents-deploy serve test group what-if validate deploy outputs cleanup purge

help:
	@printf '%s\n' \
		'Local workflow:' \
		'  make install       Install Python dependencies.' \
		'  make seed          Create or update the local demo database.' \
		'  make rag-index     Index the PDF knowledge corpus.' \
		'  make agents-deploy Publish Foundry agent versions.' \
		'  make serve         Start the FastAPI server.' \
		'  make test          Run tests.' \
		'' \
		'Azure infrastructure:' \
		'  make what-if       Preview the Bicep deployment.' \
		'  make validate      Validate the Bicep deployment.' \
		'  make deploy        Create the resource group and deploy infrastructure.' \
		'  make outputs       Show deployment outputs.' \
		'  make cleanup       Delete the resource group and all its resources.' \
		'  make purge         Permanently purge soft-deleted AI resources.'

install:
	$(PYTHON) -m pip install -r requirements.txt

seed:
	$(PYTHON) -m storage.seed

rag-index:
	$(PYTHON) -m rag.index_knowledge

agents-deploy:
	$(PYTHON) deploy.py

serve:
	$(PYTHON) -m uvicorn main:app --reload

test:
	$(PYTHON) -m unittest discover -s tests -v

group:
	az group create --name $(RESOURCE_GROUP) --location $(LOCATION)

what-if:
	az deployment group what-if --resource-group $(RESOURCE_GROUP) --template-file $(TEMPLATE_FILE) --parameters $(DEPLOY_PARAMETERS)

validate:
	az deployment group validate --resource-group $(RESOURCE_GROUP) --template-file $(TEMPLATE_FILE) --parameters $(DEPLOY_PARAMETERS)

deploy: group
	az deployment group create --name $(DEPLOYMENT_NAME) --resource-group $(RESOURCE_GROUP) --template-file $(TEMPLATE_FILE) --parameters $(DEPLOY_PARAMETERS)

outputs:
	az deployment group show --resource-group $(RESOURCE_GROUP) --name $(DEPLOYMENT_NAME) --query properties.outputs --output json

cleanup:
	az group delete --name $(RESOURCE_GROUP) --yes --no-wait

purge:
	az cognitiveservices account purge --location $(LOCATION) --resource-group $(RESOURCE_GROUP) --name $(AI_FOUNDRY_NAME)
	az cognitiveservices account purge --location $(LOCATION) --resource-group $(RESOURCE_GROUP) --name $(AI_FOUNDRY_NAME)-content-safety

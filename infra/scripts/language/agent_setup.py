import json
import os
import yaml
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import OpenApiTool, OpenApiManagedAuthDetails,OpenApiManagedSecurityScheme
from azure.identity import DefaultAzureCredential
from utils import bind_parameters

config = {}

project_endpoint = os.environ.get("AGENTS_PROJECT_ENDPOINT")
model_name = os.environ.get("AZURE_ENV_GPT_MODEL_NAME")
config['language_resource_url'] = os.environ.get("LANGUAGE_ENDPOINT")
config['clu_project_name'] = os.environ.get("CLU_PROJECT_NAME")
config['clu_deployment_name'] = os.environ.get("CLU_DEPLOYMENT_NAME")
config['cqa_project_name'] = os.environ.get("CQA_PROJECT_NAME")
config['cqa_deployment_name'] = os.environ.get("CQA_DEPLOYMENT_NAME")

# Create agent client
agents_client = AgentsClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
    api_version="2025-05-15-preview"
)

# Set up the auth details for the OpenAPI connection
auth = OpenApiManagedAuthDetails(security_scheme=OpenApiManagedSecurityScheme(audience="https://cognitiveservices.azure.com/"))

# Read in the OpenAPI spec from a file
with open("clu.json", "r") as f:
    clu_openapi_spec = json.loads(bind_parameters(f.read(), config))

clu_api_tool = OpenApiTool(
    name="clu_api",
    spec=clu_openapi_spec,
    description= "An API to extract intent from a given message",
    auth=auth
)

# Read in the OpenAPI spec from a file
with open("cqa.json", "r") as f:
    cqa_openapi_spec = json.loads(bind_parameters(f.read(), config))

# Initialize an Agent OpenApi tool using the read in OpenAPI spec
cqa_api_tool = OpenApiTool(
    name="cqa_api",
    spec=cqa_openapi_spec,
    description= "An API to get answer to questions related to business operation",
    auth=auth
)

# Create an Agent with OpenApi tool and process Agent run
with agents_client:
    instructions = """
        You are a triage agent. Your goal is to answer questions and redirect message according to their intent. You have at your disposition 2 tools:
        1. cqa_api: to answer customer questions such as procedures and FAQs.
        2. clu_api: to extract the intent of the message.
        You must use the tools to perform your task. Only if the tools are not able to provide the information, you can answer according to your general knowledge.
        - When you return answers from the cqa_api return the exact answer without rewriting it.
        - When you return answers from the clu_api return 'Detected Intent: {intent response}' and fill {intent response} with the intent returned from the api.
        To call the clu_api, the following parameters values should be used in the payload:
        - 'projectName': value must be '${clu_project_name}'
        - 'deploymentName': value must be '${clu_deployment_name}'
        - 'text': must be the input from the user.
        """

    instructions = bind_parameters(instructions, config)

    print(f"agents_endpoint: {project_endpoint}")
    print(f"model_name: {model_name}")
    print(f"AZURE_ENV_GPT_MODEL_NAME: {os.environ.get('AZURE_ENV_GPT_MODEL_NAME')}")
    # Create the agent
    agent = agents_client.create_agent(
        model=model_name,
        name="Intent Routing Agent",
        instructions=instructions,
        tools=cqa_api_tool.definitions + clu_api_tool.definitions
    )

    print(f"Created agent, ID: {agent.id}")
    os.environ['TRIAGE_AGENT_ID'] = agent.id
import json
import os
import yaml
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ListSortOrder, OpenApiTool, OpenApiConnectionAuthDetails, OpenApiConnectionSecurityScheme
from azure.identity import DefaultAzureCredential
from utils import bind_parameters

config = yaml.safe_load(open("./config.yaml", "r"))

project_endpoint = "https://yaoswal-ai-agent-resource.services.ai.azure.com/api/projects/yaoswal-ai-agent" #os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
connection_id = "/subscriptions/fecacd8c-07e7-4fad-a455-f65af8db70b3/resourceGroups/rg-yaoswal-7856/providers/Microsoft.CognitiveServices/accounts/yaoswal-ai-agent-resource/projects/yaoswal-ai-agent/connections/yaoswalcustomkey" #os.environ.get("FOUNDRY_CONNECTION_ID")
model_name = "gpt-4o" #os.environ.get("FOUNDRY_MODEL_NAME")

# Create agent client
agents_client = AgentsClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
    api_version="2025-05-15-preview"
)

# Set up the auth details for the OpenAPI connection
auth = OpenApiConnectionAuthDetails(security_scheme=OpenApiConnectionSecurityScheme(connection_id=connection_id))

# Read in the OpenAPI spec from a file
with open("./clu.json", "r") as f:
    clu_openapi_spec = json.loads(bind_parameters(f.read(), config))

clu_api_tool = OpenApiTool(
    name="clu_api",
    spec=clu_openapi_spec,
    description= "An API to extract intent from a given message",
    auth=auth
)

# Read in the OpenAPI spec from a file
with open("./cqa.json", "r") as f:
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

    # Create the agent
    agent = agents_client.create_agent(
        model=model_name,
        name="Intent Routing Agent",
        instructions=instructions,
        tools=cqa_api_tool.definitions + clu_api_tool.definitions
    )

    print(f"Created agent, ID: {agent.id}")
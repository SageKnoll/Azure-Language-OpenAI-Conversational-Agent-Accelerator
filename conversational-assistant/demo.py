# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import importlib
from dotenv import load_dotenv
from router.router_settings import RouterSettings
from unified_conversation_orchestrator import UnifiedConversationOrchestrator

load_dotenv()


def fallback_function(
    query: str,
    language: str,
    id: int
) -> str:
    """
    Orchestrator fallback function.
    """
    # Update with your own solution (e.g. RAG):
    return "I am unable to answer your query."


# Create orchestrator:
orchestrator = UnifiedConversationOrchestrator(
    router_settings=RouterSettings(),
    fallback_function=fallback_function
)


def chat(
    message: str
) -> tuple[str, dict]:
    """
    Orchestrator chat.
    """
    # Route message:
    orchestration_response = orchestrator.orchestrate(
        message=message
    )

    # Parse response:
    chat_response = None
    if orchestration_response["route"] == "fallback":
        chat_response = orchestration_response["result"]

    elif orchestration_response["route"] == "clu":
        intent = orchestration_response["result"]["intent"]
        entities = orchestration_response["result"]["entities"]

        # Here, you may call external functions based on recognized intent:
        hooks_module = importlib.import_module("clu_hooks")
        hook_func = getattr(hooks_module, intent)

        chat_response = hook_func(entities)

    elif orchestration_response["route"] == "cqa":
        answer = orchestration_response["result"]["answer"]

        chat_response = answer

    return chat_response, orchestration_response


# Example chat flow:
print("Contoso Outdoors Orchestrator Chat:")

while (True):
    message = input("\nUser: ")

    if message.lower() == "exit":
        break

    (response, log) = chat(message=message)

    print(f"Assistant: {response}")

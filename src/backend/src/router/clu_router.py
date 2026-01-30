# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# Modified for IRIS Symphony - OSHA Recordkeeping
import os
import logging
from typing import Callable
from azure.ai.language.conversations import ConversationAnalysisClient
from utils import get_azure_credential

_logger = logging.getLogger(__name__)


def create_clu_router() -> Callable[[str, str, str], dict]:
    """
    Create CLU runtime routing function for OSHA recordkeeping intents.
    """
    project_name = os.environ.get('CLU_PROJECT_NAME', 'sagevia-osha-clu')
    deployment_name = os.environ.get('CLU_DEPLOYMENT_NAME', 'production')
    endpoint = os.environ['LANGUAGE_ENDPOINT']
    credential = get_azure_credential()
    client = ConversationAnalysisClient(endpoint, credential)

    def create_input(
        utterance: str,
        language: str,
        id: str
    ) -> dict:
        """
        Create JSON input for CLU runtime.
        """
        return {
            "kind": "Conversation",
            "analysisInput": {
                "conversationItem": {
                    "id": str(id),
                    "participantId": "0",
                    "language": language,
                    "text": utterance
                }
            },
            "parameters": {
                "projectName": project_name,
                "deploymentName": deployment_name
            }
        }

    def call_runtime(
        utterance: str,
        language: str,
        id: str
    ) -> dict:
        """
        Call CLU runtime.
        """
        input_json = create_input(
            utterance=utterance,
            language=language,
            id=id
        )

        try:
            _logger.info(f"Calling {project_name}:{deployment_name} runtime")

            response = client.analyze_conversation(
                task=input_json
            )

            _logger.info(f"Runtime response: {response}")
            return parse_response(
                response=response
            )

        except Exception as e:
            _logger.error(f"Runtime call failed: {e}")
            return {
                "error": e
            }

    return call_runtime


def parse_response(
    response: dict
) -> dict:
    """
    Parse CLU runtime response for OSHA intents.
    
    OSHA Intents:
    - RecordabilityQuestion
    - FirstAidVsMedical
    - DaysAwayCalculation
    - IndustryRiskProfile
    - FormGeneration
    - DefinitionLookup
    """
    confidence_threshold = float(os.environ.get("CLU_CONFIDENCE_THRESHOLD", "0.7"))
    prediction = response["result"]["prediction"]
    confidence = prediction["intents"][0]["confidenceScore"]
    intent = prediction["topIntent"]
    entities = prediction["entities"]
    error = None

    # Filter based on confidence threshold:
    if confidence < confidence_threshold:
        _logger.warning("CLU confidence threshold not met")
        error = "CLU confidence threshold not met"

    # Filter based on intent:
    if intent == "None":
        _logger.warning("No intent recognized")
        error = "No intent recognized"

    return {
        "kind": "clu_result",
        "error": error,
        "intent": intent,
        "entities": entities,
        "confidence": confidence,
        "api_response": response
    }

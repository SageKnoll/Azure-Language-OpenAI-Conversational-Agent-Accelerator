# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import logging
from typing import Callable
from router.router_settings import RouterSettings
from language_http_utils import run_language_api

_logger = logging.getLogger(__name__)


def create_clu_router(
    router_settings: RouterSettings
) -> Callable[[str, str, str], dict]:
    """
    Create CLU runtime routing function.
    """
    project_name = router_settings.clu_settings["project_name"]
    deployment_name = router_settings.clu_settings["deployment_name"]
    url = "".join([
        router_settings.language_settings["endpoint"],
        "/language/:analyze-conversations"
    ])
    query_parameters = {
        "api-version": "2023-04-01"
    }

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
            response_json = run_language_api(
                url=url,
                api_key=router_settings.language_settings["api_key"],
                json_obj=input_json,
                query_parameters=query_parameters
            )

            _logger.info(f"Runtime response: {response_json}")
            return parse_response(
                router_settings=router_settings,
                response_json=response_json
            )

        except Exception as e:
            _logger.error(f"Runtime call failed: {e}")
            return {
                "error": e
            }

    return call_runtime


def parse_response(
    router_settings: RouterSettings,
    response_json: dict
) -> dict:
    """
    Parse CLU runtime response.
    """
    confidence_threshold = router_settings.clu_settings["confidence_threshold"]
    prediction = response_json["result"]["prediction"]
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
        "api_response": response_json
    }

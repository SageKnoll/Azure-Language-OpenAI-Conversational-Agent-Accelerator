# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import logging
from typing import Callable
from router.router_settings import RouterSettings
from router.clu_router import parse_response as parse_clu_response
from router.cqa_router import parse_response as parse_cqa_response
from language_http_utils import run_language_api

_logger = logging.getLogger(__name__)


def create_orchestration_router(
    router_settings: RouterSettings
) -> Callable[[str, str, str], dict]:
    """
    Create Orchestration runtime routing function.
    """
    project_name = router_settings.orchestration_settings["project_name"]
    deployment_name = router_settings.orchestration_settings["deployment_name"]
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
        Create JSON input for Orchestration runtime.
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
        Call Orchestration runtime.
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
    Parse Orchestration runtime response.
    """
    confidence_threshold = router_settings.orchestration_settings["confidence_threshold"]
    prediction = response_json["result"]["prediction"]
    orch_intent = prediction["topIntent"]
    orch_intent_result = prediction["intents"][orch_intent]
    confidence = orch_intent_result["confidenceScore"]
    error = None

    # Filter based on confidence threshold:
    if confidence < confidence_threshold:
        _logger.warning("Orchestration confidence threshold not met")
        error = "Orchestration confidence threshold not met"

    # Check orchestration routing kind:
    kind = orch_intent_result["targetProjectKind"]
    parsed_result = {}
    if kind == "Conversation":
        parsed_result = parse_clu_response(
            router_settings=router_settings,
            response_json=orch_intent_result
        )
    elif kind == "QuestionAnswering":
        parsed_result = parse_cqa_response(
            router_settings=router_settings,
            response_json=orch_intent_result["result"]
        )
    else:
        error = f"Unexpected orchestration intent kind: {kind}"

    if error is not None:
        parsed_result["error"] = error
    parsed_result["api_response"] = response_json

    return parsed_result

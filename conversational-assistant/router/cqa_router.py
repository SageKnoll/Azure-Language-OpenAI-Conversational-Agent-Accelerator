# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import logging
from typing import Callable
from router.router_settings import RouterSettings
from language_http_utils import run_language_api

_logger = logging.getLogger(__name__)


def create_cqa_router(
    router_settings: RouterSettings
) -> Callable[[str, str, str], dict]:
    """
    Create CQA runtime routing function.
    """
    project_name = router_settings.cqa_settings["project_name"]
    deployment_name = router_settings.cqa_settings["deployment_name"]
    url = "".join([
        router_settings.language_settings["endpoint"],
        "/language/:query-knowledgebases"
    ])
    query_parameters = {
        "api-version": "2023-04-01",
        "projectName": project_name,
        "deploymenName": deployment_name
    }

    def create_input(
        question: str
    ) -> dict:
        """
        Create JSON input for CQA runtime.
        """
        return {
            "question": question,
            "top": 1
        }

    def call_runtime(
        question: str,
        language: str,
        id: str
    ) -> dict:
        """
        Call CQA runtime.
        """
        input_json = create_input(question=question)

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
    Parse CQA runtime response.
    """
    confidence_threshold = router_settings.cqa_settings["confidence_threshold"]
    top_answer = response_json["answers"][0]
    confidence = top_answer["confidenceScore"]
    answer = top_answer["answer"]
    answer_id = top_answer["id"]
    question = None
    error = None

    # Filter based on confidence threshold:
    if confidence < confidence_threshold:
        _logger.warning("CQA confidence threshold not met")
        error = "CQA confidence threshold not met"

    # Filter based on answer id:
    if answer_id == -1:
        # -1 means default answer was returned.
        _logger.warning("No answer found")
        error = "No answer found"
    else:
        question = top_answer["questions"][0]

    return {
        "kind": "cqa_result",
        "error": error,
        "answer": answer,
        "question": question,
        "confidence": confidence,
        "api_response": response_json
    }

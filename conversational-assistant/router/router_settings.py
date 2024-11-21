# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from dotenv import load_dotenv
from router.router_type import RouterType

load_dotenv()


class RouterSettings():
    """
    Router settings.
    """

    def __init__(self):
        """
        Create router settings based on current environment variables.
        """
        self.router_type = RouterType(os.environ.get("ROUTER_TYPE", "BYPASS"))
        self.language_settings = {
            "endpoint": os.environ.get("LANGUAGE_ENDPOINT", None),
            "api_key": os.environ.get("LANGUAGE_API_KEY", None),
        }
        self.clu_settings = {
            "project_name": os.environ.get("CLU_PROJECT_NAME", None),
            "deployment_name": os.environ.get("CLU_DEPLOYMENT_NAME", None),
            "confidence_threshold": float(os.environ.get("CLU_CONFIDENCE_THRESHOLD", "0.5"))
        }
        self.cqa_settings = {
            "project_name": os.environ.get("CQA_PROJECT_NAME", None),
            "deployment_name": os.environ.get("CQA_DEPLOYMENT_NAME", None),
            "confidence_threshold": float(os.environ.get("CQA_CONFIDENCE_THRESHOLD", "0.5"))
        }
        self.orchestration_settings = {
            "project_name": os.environ.get("ORCHESTRATION_PROJECT_NAME", None),
            "deployment_name": os.environ.get("ORCHESTRATION_DEPLOYMENT_NAME", None),
            "confidence_threshold": float(os.environ.get("ORCHESTRATION_CONFIDENCE_THRESHOLD", "0.5"))
        }

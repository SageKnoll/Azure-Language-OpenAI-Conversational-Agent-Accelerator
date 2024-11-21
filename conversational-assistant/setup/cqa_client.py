import uuid
import logging
from language_http_utils import run_language_api


class CqaClient():
    """
    Client class to connect to CQA authoring/runtime in a language resource.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = "2023-04-01"
        self.query_parameters = {
            "api-version": self.api_version
        }

    def list_projects(
        self
    ) -> list[str]:
        """
        List all CQA projects in language resource.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/query-knowledgebases/projects"
        ])

        try:
            self.logger.info("Listing projects")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                query_parameters=self.query_parameters,
                method="get"
            )

            projects = [p["projectName"] for p in result_json["value"]]
            return projects

        except Exception as e:
            self.logger.error("Unable to list projects")
            raise e

    def list_deployments(
        self,
        project_name: str
    ) -> list[str]:
        """
        List all deployments in CQA project.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/query-knowledgebases/projects/",
            project_name,
            "/deployments"
        ])

        try:
            self.logger.info(f"Listing deployments for project {project_name}")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                query_parameters=self.query_parameters,
                method="get"
            )

            deployments = [d["deploymentName"] for d in result_json["value"]]
            return deployments

        except Exception as e:
            self.logger.error("Unable to list deployments")
            raise e

    def create_project(
        self,
        project_name: str,
        language: str = "en",
        description: str = "",
        default_answer: str = "No answer found"
    ):
        """
        Create CQA project.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/query-knowledgebases/projects/",
            project_name
        ])

        create_request = {
            "description": description,
            "language": language,
            "settings": {
                "defaultAnswer": default_answer
            },
            "multiLingualResource": False
        }

        try:
            self.logger.info(f"Creating project {project_name}")
            _ = run_language_api(
                url=url,
                api_key=self.api_key,
                json_obj=create_request,
                query_parameters=self.query_parameters,
                method="patch"
            )

        except Exception as e:
            self.logger.error(f"Unable to create project: {e}")
            raise e

    def import_project(
        self,
        import_json: dict,
        project_name: str,
    ) -> bool:
        """
        Import CQA project.

        Returns True if import succeeded, False if failed.
        """
        import_params = self.query_parameters
        import_params["format"] = "json"

        url = "".join([
            self.endpoint,
            "/language/authoring/query-knowledgebases/projects/",
            project_name,
            "/:import"
        ])

        try:
            self.logger.info(f"Importing project {project_name}")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                json_obj=import_json,
                query_parameters=import_params,
                sync=False
            )

            return result_json["status"] == "succeeded"

        except Exception as e:
            self.logger.error(f"Unable to import project: {e}")
            raise e

    def deploy(
        self,
        project_name: str,
        deployment_name: str = "production"
    ) -> bool:
        """
        Deploy knowledge-base in CQA project.

        Returns True if deployment succeeded, False if failed.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/query-knowledgebases/projects/",
            project_name,
            "/deployments/",
            deployment_name
        ])

        try:
            self.logger.info(f"Deploying knowledge-base {deployment_name} in project {project_name}")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                query_parameters=self.query_parameters,
                sync=False,
                method="put"
            )

            return result_json["status"] == "succeeded"

        except Exception as e:
            self.logger.error(f"Unable to deploy knowledge-base: {e}")
            raise e

    def add_qna(
        self,
        project_name: str,
        question: str,
        answer: str
    ) -> bool:
        """
        Add qna pair to CQA project.

        Returns True if update succeeded, False if failed.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/query-knowledgebases/projects/",
            project_name,
            "/qnas"
        ])

        update_request = [
            {
                "op": "add",
                "value": {
                    "id": str(int(uuid.uuid4())),
                    "answer": answer,
                    "questions": [
                        question
                    ]
                }
            }
        ]

        try:
            self.logger.info(f"Adding qna pair to project {project_name}")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                json_obj=update_request,
                query_parameters=self.query_parameters,
                sync=False,
                method="patch"
            )

            return result_json["status"] == "succeeded"

        except Exception as e:
            self.logger.error(f"Unable to add qna pair: {e}")
            raise e

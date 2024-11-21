import logging
from datetime import datetime
from language_http_utils import run_language_api


class CluClient():
    """
    Client class to connect to CLU authoring in a language resource.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        orchestration: bool = False
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = "2023-04-01"
        self.query_parameters = {
            "api-version": self.api_version
        }
        if orchestration:
            self.project_kind = "Orchestration"
        else:
            self.project_kind = "Conversation"

    def list_projects(
        self
    ) -> list[str]:
        """
        List all CLU projects in language resource.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/analyze-conversations/projects"
        ])

        try:
            self.logger.info("Listing projects")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                query_parameters=self.query_parameters,
                method="get"
            )

            projects = []
            for result in result_json["value"]:
                if result["projectKind"] == self.project_kind:
                    projects.append(result["projectName"])
            return projects

        except Exception as e:
            self.logger.error(f"Unable to list projects: {e}")
            raise e

    def list_models(
        self,
        project_name: str
    ) -> list[str]:
        """
        List all trained models in CLU project.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/analyze-conversations/projects/",
            project_name,
            "/models"
        ])

        try:
            self.logger.info(f"Listing models for project {project_name}")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                query_parameters=self.query_parameters,
                method="get"
            )

            models = [m["label"] for m in result_json["value"]]
            return models

        except Exception as e:
            self.logger.error(f"Unable to list models: {e}")
            raise e

    def list_deployments(
        self,
        project_name: str
    ) -> list[str]:
        """
        List all model deployments in CLU project.
        """
        url = "".join([
            self.endpoint,
            "/language/authoring/analyze-conversations/projects/",
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
            self.logger.error(f"Unable to list deployments: {e}")
            raise e

    def import_project(
        self,
        import_json: dict,
        project_name: str = None,
    ) -> bool:
        """
        Import CLU project.

        Returns True if import succeeded, False if failed.
        """
        if not project_name:
            project_name = import_json["metadata"]["projectName"]
        else:
            import_json["metadata"]["projectName"] = project_name

        url = "".join([
            self.endpoint,
            "/language/authoring/analyze-conversations/projects/",
            project_name,
            "/:import"
        ])

        try:
            self.logger.info(f"Importing project {project_name}")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                json_obj=import_json,
                query_parameters=self.query_parameters,
                sync=False
            )

            return result_json["status"] == "succeeded"

        except Exception as e:
            self.logger.error(f"Unable to import project: {e}")
            raise e

    def train(
        self,
        project_name: str,
        model_name: str = None
    ) -> str:
        """
        Train new model in CLU project.

        Returns training job url.
        """
        if not model_name:
            model_name = "".join([
                project_name,
                "_model_",
                datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            ])

        url = "".join([
            self.endpoint,
            "/language/authoring/analyze-conversations/projects/",
            project_name,
            "/:train"
        ])

        train_request = {
            "modelLabel": model_name,
            "trainingMode": "standard",
            "trainingConfigVersion": "latest",
            "evaluationOptions": {
                "kind": "percentage",
                "testingSplitPercentage": 20,
                "trainingSplitPercentage": 80
            }
        }

        try:
            self.logger.info(f"Training model {model_name} in project {project_name}")
            train_job_url = run_language_api(
                url=url,
                api_key=self.api_key,
                json_obj=train_request,
                query_parameters=self.query_parameters,
                sync=False,
                async_polling=False
            )

            return train_job_url

        except Exception as e:
            self.logger.error(f"Unable to train model: {e}")
            raise e

    def get_training_status(
        self,
        train_job_url: str
    ) -> dict:
        """
        Get training status of model.
        """
        try:
            self.logger.info(f"Getting training status for {train_job_url}")
            train_status = run_language_api(
                url=train_job_url,
                api_key=self.api_key,
                method="get"
            )

            return train_status

        except Exception as e:
            self.logger.error(f"Unable to get training status: {e}")
            raise e

    def deploy(
        self,
        project_name: str,
        model_name: str,
        deployment_name: str = None
    ) -> bool:
        """
        Deploy trained model in CLU project.

        Returns True if deployment succeeded, False otherwise.
        """
        if not deployment_name:
            if "_model_" in model_name:
                deployment_name = model_name.replace("_model_", "_dep_")
            else:
                deployment_name = "".join([
                    project_name,
                    "_dep_",
                    datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
                ])

        url = "".join([
            self.endpoint,
            "/language/authoring/analyze-conversations/projects/",
            project_name,
            "/deployments/",
            deployment_name
        ])

        deployment_request = {
            "trainedModelLabel": model_name
        }

        try:
            self.logger.info(f"Deploying model {model_name} in project {project_name}")
            result_json = run_language_api(
                url=url,
                api_key=self.api_key,
                json_obj=deployment_request,
                query_parameters=self.query_parameters,
                sync=False,
                method="put"
            )

            return result_json["status"] == "succeeded"

        except Exception as e:
            self.logger.error(f"Unable to deploy model: {e}")
            raise e

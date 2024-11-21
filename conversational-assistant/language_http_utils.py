# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
import time
import logging
import requests

DEFAULT_TIMEOUT = int(os.environ.get("DEFAULT_HTTP_TIMEOUT", "60"))

_logger = logging.getLogger(__name__)


def run_sync_endpoint(
    url: str,
    headers: dict,
    json_obj: dict,
    query_parameters: dict,
    max_retries: int,
    max_wait: int,
    method: str = "post"
) -> dict:
    """
    Synchronous API request.
    """
    session = requests.Session()
    response = submit_request_expbo(
        request_func=lambda: session.request(
            method=method,
            url=url,
            params=query_parameters,
            headers=headers,
            json=json_obj
        ),
        max_retries=max_retries,
        max_wait=max_wait
    )

    return response.json() if response.status_code != 202 else None


def run_async_endpoint(
    url: str,
    headers: dict,
    json_obj: dict,
    query_parameters: dict,
    max_retries: int,
    max_wait: int,
    method: str = "post",
    async_polling: bool = True,
    timeout=DEFAULT_TIMEOUT,
    sleep_time=5
) -> dict:
    """
    Asynchronous API request.
    """
    session = requests.Session()
    response = submit_request_expbo(
        request_func=lambda: session.request(
            method=method,
            url=url,
            params=query_parameters,
            headers=headers,
            json=json_obj
        ),
        max_retries=max_retries,
        max_wait=max_wait
    )

    try:
        response.raise_for_status()
    except requests.HTTPError:
        return response

    status_url = response.headers["Operation-Location"]
    if not async_polling:
        return status_url

    # Poll until completion of job:
    start = time.time()
    while (True):
        if time.time() - start > timeout:
            raise TimeoutError("Async polling timed out")

        try:
            response = submit_request_expbo(
                request_func=lambda: session.get(
                    url=status_url,
                    headers=headers
                ),
                max_retries=max_retries,
                max_wait=max_wait)

            response_json = response.json()
            status = response_json["status"]
            if status == "succeeded" or status == "failed":
                break
        except requests.HTTPError:
            pass

        time.sleep(sleep_time)

    return response_json


def run_language_api(
    url: str,
    api_key: str,
    json_obj: dict = None,
    query_parameters: dict = None,
    sync: bool = True,
    method: str = "post",
    async_polling: bool = True,
    max_retries: int = 3,
    max_wait: int = 30
) -> dict:
    """
    Run either sync or async language API.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": "application/json"
    }
    if sync:
        return run_sync_endpoint(
            url=url,
            headers=headers,
            json_obj=json_obj,
            query_parameters=query_parameters,
            method=method,
            max_retries=max_retries,
            max_wait=max_wait
        )
    else:
        return run_async_endpoint(
            url=url,
            headers=headers,
            json_obj=json_obj,
            query_parameters=query_parameters,
            method=method,
            async_polling=async_polling,
            max_retries=max_retries,
            max_wait=max_wait
        )


def exponential_backoff_time(
    max_retries: int,
    max_wait: int,
    retry_count: int
) -> int:
    """
    Calculate exponential backoff wait time.
    """
    wait_time = max_wait ** (retry_count / max_retries)
    return wait_time


def submit_request_expbo(
    request_func,
    max_retries: int,
    max_wait: int
) -> requests.Response:
    """
    Submit HTTP request with exponential backoff logic.
    """
    retries = 0
    resp = None
    while (retries < max_retries):
        try:
            if retries != 0:
                _logger.warning("HTTP failure; retrying...")
                wait_time = exponential_backoff_time(
                    max_wait=max_wait,
                    max_retries=max_retries,
                    retry_count=retries
                )
                time.sleep(wait_time)
            resp = request_func()
            _logger.info(f"Status code: {resp.status_code}")
            retries += 1
            resp.raise_for_status()
            return resp
        except requests.HTTPError:
            pass

    _logger.error("Maximum number of retries reached.")
    _logger.error(f"Status code: {resp.status_code}")
    _logger.error(f"Response: {resp.json()}")
    resp.raise_for_status()

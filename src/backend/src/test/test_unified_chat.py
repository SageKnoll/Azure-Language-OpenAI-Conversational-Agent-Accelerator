# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# Modified for IRIS Symphony - OSHA Recordkeeping
import pytest
import os
import sys
import subprocess
import requests
import time
from typing import Generator

"""
This module contains test cases for the chat endpoint of the app with unified orchestration.
It includes single-turn and multi-turn interactions with parameterized test cases.
The tests are designed to validate the responses from the chat endpoint based on OSHA recordkeeping scenarios.

Test different routing strategies by setting the ROUTER_TYPE environment variable.
For example:
export ROUTER_TYPE=TRIAGE_AGENT
pytest test/test_unified_chat.py -s -v

Possible values for ROUTER_TYPE:
- BYPASS
- CLU
- CQA
- ORCHESTRATION
- FUNCTION_CALLING
- TRIAGE_AGENT
"""

# Test cases for the chat endpoint
SINGLE_TURN_TEST_CASES = [
    {
        "name": "first_aid_definition",
        "current_question": "What is considered first aid?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "29 CFR 1904.7(a)",
            "first aid"
        ]
    },
    {
        "name": "recordability_needlestick",
        "current_question": "Is a needlestick recordable?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "needlestick",
            "29 CFR"
        ]
    },
    {
        "name": "recordability_stitches",
        "current_question": "Employee got stitches, is that recordable?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "stitches",
            "medical treatment"
        ]
    },
    {
        "name": "days_away_counting",
        "current_question": "Do weekends count as days away?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "calendar days",
            "weekends"
        ]
    },
    {
        "name": "need_more_info_recordability",
        "current_question": "Is this recordable?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "information",
            "injury"
        ]
    },
    {
        "name": "need_more_info_industry",
        "current_question": "What are my industry's injury rates?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "NAICS"
        ]
    },
    {
        "name": "form_300a_posting",
        "current_question": "When do I post the annual summary?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "February 1",
            "April 30"
        ]
    },
    {
        "name": "record_retention",
        "current_question": "How long must I keep the 300 log?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "5 years"
        ]
    },
    {
        "name": "work_related_definition",
        "current_question": "What makes an injury work-related?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "work environment",
            "29 CFR 1904.5"
        ]
    }
]


# Launch the FastAPI server using uvicorn for testing purposes
@pytest.fixture(scope="session")
def uvicorn_server() -> Generator:
    """Start uvicorn server for testing"""
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    # Start server using python -m
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "unified_app:app",
        "--host", "127.0.0.1",
        "--port", "7000",
        "--reload"
    ], env=env)

    # Wait for server to start
    url = "http://127.0.0.1:7000"
    for _ in range(30):
        try:
            requests.get(url)
            break
        except requests.ConnectionError:
            time.sleep(1)

    yield url  # Return the server URL for tests to use

    # Cleanup
    process.terminate()
    process.wait()


# Test the chat endpoint with parameterized test cases for single turn interactions
@pytest.mark.parametrize("test_case", SINGLE_TURN_TEST_CASES, ids=lambda x: x["name"])
def test_single_turn(uvicorn_server: str, test_case: dict):
    """Test chat endpoint responses"""

    response = requests.post(
        f"{uvicorn_server}/chat",
        json={"message": test_case["current_question"], "history": test_case["history"]},
    )

    # Check response
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()

    # Verify response contains expected elements (not exact match for regulatory content)
    response_text = " ".join(data.get("messages", [])).lower()
    for expected in test_case["expected_response_contains"]:
        assert expected.lower() in response_text, (
            f"Response for test '{test_case['name']}' missing expected content: '{expected}'. "
            f"Actual response: {data.get('messages')}"
        )

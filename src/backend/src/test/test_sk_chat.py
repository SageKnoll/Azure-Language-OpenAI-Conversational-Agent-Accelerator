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
This module contains test cases for the chat endpoint of the app with Semantic Kernel orchestration.
It includes single-turn and multi-turn interactions with parameterized test cases.
The tests are designed to validate the responses from the chat endpoint based on OSHA recordkeeping scenarios.

Launch this test suite using pytest:
cd src/backend/src/
pytest test/test_sk_chat.py -s -v
"""

# Test cases for the chat endpoint
SINGLE_TURN_TEST_CASES = [
    {
        "name": "first_aid_definition",
        "current_question": "What is considered first aid under OSHA?",
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
        "name": "recordability_with_details",
        "current_question": "Employee got 3 stitches for a cut on their hand",
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
        "current_question": "How do I count days away from work?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "calendar days",
            "29 CFR 1904.7"
        ]
    },
    {
        "name": "industry_risk_with_naics",
        "current_question": "What are the injury rates for NAICS 238220?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "238220",
            "TCIR"
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
            "more information",
            "injury"
        ]
    },
    {
        "name": "need_more_info_industry",
        "current_question": "What are my industry injury rates?",
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
        "current_question": "When do I need to post the 300A?",
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
        "current_question": "How long do I keep OSHA records?",
        "history": [
            {
                "role": "",
                "content": ""
            }
        ],
        "expected_response_contains": [
            "5 years",
            "29 CFR 1904.33"
        ]
    }
]


MULTI_TURN_TEST_CASES = [
    {
        "name": "multi_turn_recordability",
        "sequence": [
            {
                "current_question": "Is this injury recordable?",
                "history": [
                    {
                        "role": "",
                        "content": ""
                    }
                ],
                "expected_response_contains": ["more information", "injury"]
            },
            {
                "current_question": "Employee cut their hand and received 4 stitches",
                "history": [
                    {
                        "role": "User",
                        "content": "Is this injury recordable?"
                    },
                    {
                        "role": "System",
                        "content": "To evaluate recordability criteria, I need more information about the incident. What type of injury or illness occurred, and what treatment was provided?"
                    }
                ],
                "expected_response_contains": ["stitches", "medical treatment", "29 CFR"]
            }
        ]
    },
    {
        "name": "multi_turn_industry_risk",
        "sequence": [
            {
                "current_question": "How does my industry compare for injuries?",
                "history": [
                    {
                        "role": "",
                        "content": ""
                    }
                ],
                "expected_response_contains": ["NAICS"]
            },
            {
                "current_question": "My NAICS code is 236220",
                "history": [
                    {
                        "role": "User",
                        "content": "How does my industry compare for injuries?"
                    },
                    {
                        "role": "System",
                        "content": "To provide industry risk data, I need your NAICS code."
                    }
                ],
                "expected_response_contains": ["236220", "TCIR"]
            }
        ]
    },
    {
        "name": "multi_turn_first_aid_clarification",
        "sequence": [
            {
                "current_question": "We gave the employee a bandage, is that first aid?",
                "history": [
                    {
                        "role": "",
                        "content": ""
                    }
                ],
                "expected_response_contains": ["first aid", "29 CFR 1904.7"]
            },
            {
                "current_question": "What if they also got a tetanus shot?",
                "history": [
                    {
                        "role": "User",
                        "content": "We gave the employee a bandage, is that first aid?"
                    },
                    {
                        "role": "System",
                        "content": "Bandages and wound coverings are listed as first aid treatments under 29 CFR 1904.7(a)."
                    }
                ],
                "expected_response_contains": ["tetanus", "first aid"]
            }
        ]
    },
    {
        "name": "multi_turn_form_generation",
        "sequence": [
            {
                "current_question": "I need to fill out the OSHA log",
                "history": [
                    {
                        "role": "",
                        "content": ""
                    }
                ],
                "expected_response_contains": ["Form 300"]
            },
            {
                "current_question": "Yes, I need Form 300 for 2025",
                "history": [
                    {
                        "role": "User",
                        "content": "I need to fill out the OSHA log"
                    },
                    {
                        "role": "System",
                        "content": "I can help with Form 300 (Log of Work-Related Injuries and Illnesses). Which year do you need?"
                    }
                ],
                "expected_response_contains": ["2025", "incident"]
            }
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
        "semantic_kernel_app:app",
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


# Test the chat endpoint with a multi-turn conversation
@pytest.mark.parametrize("test_case", MULTI_TURN_TEST_CASES, ids=lambda x: x["name"])
def test_multi_turn(uvicorn_server: str, test_case: dict):
    """Test multi-turn chat endpoint responses"""

    for step in test_case["sequence"]:
        response = requests.post(
            f"{uvicorn_server}/chat",
            json={"message": step["current_question"], "history": step["history"]},
            timeout=180
        )

        # Check response
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()

        # Verify response contains expected elements
        response_text = " ".join(data.get("messages", [])).lower()
        for expected in step["expected_response_contains"]:
            assert expected.lower() in response_text, (
                f"Response for test '{test_case['name']}' missing expected content: '{expected}'. "
                f"Actual response: {data.get('messages')}"
            )

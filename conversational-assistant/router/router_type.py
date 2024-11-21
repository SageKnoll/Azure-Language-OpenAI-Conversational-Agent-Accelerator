# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from enum import Enum


class RouterType(Enum):
    """
    Router implementation type.
    """
    # No routing (e.g. fallback only):
    BYPASS = "BYPASS"
    # CLU only:
    CLU = "CLU"
    # CQA only:
    CQA = "CQA"
    # Orchestration routes to either CLU or CQA:
    ORCHESTRATION = "ORCHESTRATION"

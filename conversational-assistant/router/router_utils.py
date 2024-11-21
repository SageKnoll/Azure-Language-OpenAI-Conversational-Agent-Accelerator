# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from typing import Callable
from router.router_type import RouterType
from router.router_settings import RouterSettings
from router.clu_router import create_clu_router
from router.cqa_router import create_cqa_router
from router.orchestration_router import create_orchestration_router


def create_router(
    router_settings: RouterSettings
) -> Callable[[str, str, str], dict]:
    """
    Create router based on settings.
    """
    router_type = router_settings.router_type
    if router_type == RouterType.BYPASS:
        return lambda x, y, z: None
    if router_type == RouterType.CLU:
        return create_clu_router(router_settings)
    elif router_type == RouterType.CQA:
        return create_cqa_router(router_settings)
    elif router_type == RouterType.ORCHESTRATION:
        return create_orchestration_router(router_settings)
    raise ValueError("Unsupported router type")

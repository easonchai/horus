"""
Re-exports from core.agent_kit for backward compatibility.

This module is maintained for backward compatibility with existing code.
New code should import directly from core.agent_kit instead.
"""

import warnings

# Issue a deprecation warning
warnings.warn(
    "Importing from tools.agent_kit is deprecated and will be removed in a future version. "
    "Import from core.agent_kit instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from core.agent_kit
from core.agent_kit import (
    AGENTKIT_AVAILABLE, ActionResult,
    ActionStatus, AgentKitManager,
    CdpActionProvider, CdpWalletProvider,
    agent_kit_manager, get_env_var,
    is_agentkit_available, read_wallet_data,
    save_wallet_data
)

__all__ = [
    'ActionResult',
    'ActionStatus',
    'AGENTKIT_AVAILABLE',
    'AgentKitManager',
    'CdpActionProvider',
    'CdpWalletProvider',
    'agent_kit_manager',
    'get_env_var',
    'is_agentkit_available',
    'read_wallet_data',
    'save_wallet_data',
]
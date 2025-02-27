"""
Mock implementation of AgentKit components for unit testing.

This module provides mock classes and utilities to simulate the behavior of
Coinbase AgentKit in test environments, allowing for isolated testing of
components that depend on AgentKit without requiring actual API access or
blockchain interaction.
"""
import importlib
import os
import sys
from unittest.mock import MagicMock, patch


# Mock class for ActionStatus
class ActionStatus:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

# Mock class for ActionResult
class ActionResult:
    def __init__(self, status, result=None, error=None):
        self.status = status
        self.result = result or {}
        if status == ActionStatus.SUCCESS and "transactionHash" not in self.result:
            self.result["transactionHash"] = "0xabcdef1234567890abcdef1234567890abcdef1234567890"
        self.error = error

# Mock class for CdpWalletProvider
class CdpWalletProvider:
    def __init__(self, private_key=None, api_key=None, api_secret=None):
        self.private_key = private_key
        self.api_key = api_key
        self.api_secret = api_secret
        self.wallet_address = "0x1234567890123456789012345678901234567890"
    
    def get_wallet(self):
        return MagicMock(address=self.wallet_address)
    
    def get_wallet_address(self):
        return self.wallet_address
    
    def get_default_account(self):
        return {
            "address": self.wallet_address,
            "chain_id": "84532"
        }

# Mock class for CdpActionProvider
class CdpActionProvider:
    def __init__(self, wallet=None, api_key=None, api_secret=None):
        self.wallet = wallet
        self.api_key = api_key
        self.api_secret = api_secret
    
    def execute_action(self, action):
        """Simulate executing an action."""
        # Default successful response
        if action["type"] == "revokeAllowance":
            return ActionResult(
                ActionStatus.SUCCESS,
                {"transactionHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890"}
            )
        elif action["type"] == "swap":
            return ActionResult(
                ActionStatus.SUCCESS,
                {"transactionHash": "0xfedcba0987654321fedcba0987654321fedcba0987654321"}
            )
        elif action["type"] == "withdraw":
            return ActionResult(
                ActionStatus.SUCCESS,
                {"transactionHash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef"}
            )
        else:
            return ActionResult(
                ActionStatus.ERROR,
                None,
                "Unsupported action type"
            )

def setup_mocks():
    """Set up mock environment for testing with AgentKit.
    
    Returns:
        list: A list of patch objects that should be teardown after testing.
    """
    patches = []
    
    # Patch the environment variables
    env_vars = {
        'PRIVATE_KEY': '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        'CDP_API_KEY': 'test_api_key',
        'CDP_API_SECRET': 'test_api_secret',
    }
    
    env_patcher = patch.dict('os.environ', env_vars)
    env_patcher.start()
    patches.append(env_patcher)
    
    # Create mock modules for AgentKit
    mock_types = MagicMock()
    mock_types.ActionStatus = ActionStatus
    mock_types.ActionResult = ActionResult
    
    mock_cdp_wallet = MagicMock()
    mock_cdp_wallet.CdpWalletProvider = CdpWalletProvider
    
    mock_cdp_action = MagicMock()
    mock_cdp_action.CdpActionProvider = CdpActionProvider
    
    # Add mock modules to sys.modules
    mock_modules = {
        'coinbase_agentkit.types': mock_types,
        'coinbase_agentkit.wallet_providers.cdp.cdp_wallet_provider': mock_cdp_wallet,
        'coinbase_agentkit.action_providers.cdp.cdp_action_provider': mock_cdp_action,
    }
    
    for module_name, mock_module in mock_modules.items():
        if module_name in sys.modules:
            original = sys.modules[module_name]
            sys.modules[module_name] = mock_module
            patches.append((module_name, original))
        else:
            sys.modules[module_name] = mock_module
            patches.append((module_name, None))
    
    # Set up direct patches for agent_kit
    agent_kit_patches = [
        patch('horus.tools.agent_kit._IMPORTS_AVAILABLE', True),
        patch('horus.tools.agent_kit.AGENTKIT_AVAILABLE', True),
        patch('horus.tools.agent_kit.CdpWalletProvider', CdpWalletProvider),
        patch('horus.tools.agent_kit.CdpActionProvider', CdpActionProvider),
        patch('horus.tools.agent_kit.ActionStatus', ActionStatus),
        patch('horus.tools.agent_kit.ActionResult', ActionResult),
    ]
    
    # Start the patches
    for p in agent_kit_patches:
        p.start()
        patches.append(p)
    
    # Try to force reload agent_kit if it's already imported
    try:
        if 'horus.tools.agent_kit' in sys.modules:
            importlib.reload(sys.modules['horus.tools.agent_kit'])
    except (ImportError, KeyError):
        pass
    
    return patches

def teardown_mocks(patches):
    """Clean up the mocks created by setup_mocks.
    
    Args:
        patches: The list of patch objects returned by setup_mocks.
    """
    for patch_item in patches:
        if hasattr(patch_item, 'stop'):  # Check if the item is a patch with a stop method
            patch_item.stop()
        elif isinstance(patch_item, tuple):  # Check if the item is a (module_name, original) tuple
            module_name, original = patch_item
            if original is None:
                if module_name in sys.modules:
                    del sys.modules[module_name]
            else:
                sys.modules[module_name] = original 
"""
Core components for the Horus security monitoring agent.

This package contains fundamental components that are used
across different parts of the application, including the
AgentKit manager for blockchain interactions.
"""

from core.agent_kit import AgentKitManager, agent_kit_manager

__all__ = ["agent_kit_manager", "AgentKitManager"] 

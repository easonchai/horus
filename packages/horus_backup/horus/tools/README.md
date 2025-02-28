# Horus Security Tools

This package contains security tools used by the Horus security agent to protect user funds.

## Overview

The tools in this package follow a functional programming approach, making them easy to test, compose, and extend.

## Tool Architecture

Each tool is created using a factory function that returns a callable function:

```
create_tool(name, execute_fn) -> tool_function
```

The factory function takes a name and an execution function, and returns a tool function that can be called with parameters.

## Available Tools

### Withdrawal Tool

The withdrawal tool is used to safely withdraw funds from compromised protocols.

```python
from horus.tools import create_withdrawal_tool

# Create a withdrawal tool with dependencies
withdrawal_tool = create_withdrawal_tool(dependency_graph, user_balances)

# Use the tool
result = withdrawal_tool({
    "token": "USDC",
    "amount": "ALL",
    "destination": "safe_wallet",
    "chain_id": "84532"
})
```

### Revoke Tool

The revoke tool is used to revoke permissions from compromised tokens or protocols.

```python
from horus.tools import create_revoke_tool

# Create a revoke tool with dependencies
revoke_tool = create_revoke_tool(tokens_config)

# Use the tool
result = revoke_tool({
    "token": "USDC",
    "protocol": "Compromised Protocol",
    "chain_id": "84532"
})
```

### Monitor Tool

The monitor tool is used to enhance monitoring of assets during suspicious activity. It allows for configuring alert thresholds, monitoring durations, and tracking active monitoring configurations.

```python
from horus.tools import create_monitor_tool

# Create a monitor tool with optional alert subscribers
subscribers = ["0x1234...", "alert@example.com"]
monitor_tool = create_monitor_tool(subscribers)

# Use the tool
result = monitor_tool.execute({
    "asset": "All Base Chain Positions",
    "duration": "48h",
    "threshold": "5%",
    "chain_id": "84532",
    "alert_type": "price",
    "notify": ["additional@example.com"]
})

# The tool can also be called directly
result = monitor_tool({
    "asset": "ETH",
    "duration": "24h",
    "threshold": "3%"
})

# Get all active monitoring configurations
active_monitors = monitor_tool.get_active_monitors()

# Filter monitors by chain
base_monitors = monitor_tool.get_active_monitors("84532")
```

#### Advanced Features

The MonitorTool class provides methods for managing subscribers and monitoring configurations:

```python
# Add a subscriber
monitor_tool.add_subscriber("new_alert@example.com")

# Remove a subscriber
monitor_tool.remove_subscriber("old_alert@example.com")

# Check active monitoring configurations
active_eth_monitor = monitor_tool.active_monitors.get("ETH:84532")
if active_eth_monitor:
    print(f"ETH monitoring active until {active_eth_monitor['duration']}")
```

## Creating Custom Tools

You can create custom tools by using the `create_tool` function:

```python
from horus.tools.base import create_tool

def execute_custom_action(parameters):
    # Implement your custom action here
    return "Custom action executed"

# Create a custom tool
custom_tool = create_tool("custom", execute_custom_action)

# Use the custom tool
result = custom_tool({"param1": "value1"})
```

## Testing

The tools can be tested using the test script in the `tests` directory:

```bash
python -m tests.test_security
```

This will run tests for all the tools and the security agent.

## Revoke Tool Details

The revoke tool is implemented in `revoke.py` and uses Coinbase's AgentKit to interact with the blockchain. It provides a way to revoke token approvals for potentially compromised protocols.

### Prerequisites

To use the revoke tool, you need to have the following:

1. A Coinbase Developer Platform (CDP) API key
2. The `coinbase-agentkit` and `coinbase-agentkit-langchain` packages installed
3. Environment variables set up for the CDP API key

### Environment Variables

The revoke tool requires the following environment variables:

```
CDP_API_KEY_NAME=your_cdp_api_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_api_key_private_key
```

### Usage

The revoke tool is created using the `create_revoke_tool` factory function:

```python
from horus.tools import create_revoke_tool

# Create the revoke tool with token configuration
revoke_tool = create_revoke_tool(tokens_config)

# Use the revoke tool
result = revoke_tool({
    "token_address": "0x...",  # The token contract address
    "spender_address": "0x...",  # The address that has permission to spend the token
    "protocol": "Uniswap V3",  # Optional: The protocol name for logging
    "chain_id": "84532"  # Optional: The chain ID (default: 84532 for Base Sepolia)
})

print(result)
```

Alternatively, you can provide a token symbol instead of a token address:

```python
result = revoke_tool({
    "token": "USDC",  # The token symbol
    "spender_address": "0x...",  # The address that has permission to spend the token
    "protocol": "Uniswap V3",  # Optional: The protocol name for logging
    "chain_id": "84532"  # Optional: The chain ID (default: 84532 for Base Sepolia)
})
```

### Supported Networks

The revoke tool supports all EVM networks, with block explorer links for the following networks:

- Ethereum Mainnet (chain_id: 1)
- Base Sepolia Testnet (chain_id: 84532)
- Base Mainnet (chain_id: 8453)
- Arbitrum One (chain_id: 42161)
- Optimism (chain_id: 10)
- Polygon (chain_id: 137)

### Error Handling

The revoke tool includes robust error handling for common issues:

- Missing token address or spender address
- Failed wallet initialization
- Failed transaction execution
- Network errors

### Integration with Security Agent

The revoke tool is integrated with the Horus security agent, which can automatically call the tool when a security threat is detected. The agent uses OpenAI to analyze security alerts and determine whether to call the revoke tool.

Example security alert that would trigger the revoke tool:

```
SECURITY ALERT: Suspicious approval detected for USDC token to spender 0x1234567890123456789012345678901234567890 on Base Sepolia (chain_id: 84532). This approval was made to a protocol that has been flagged for potential security issues. Consider revoking this approval immediately.
```

## Implementation Details

All tools follow a functional programming approach, using factory functions to create tool functions with closures to maintain state. This approach provides several benefits:

1. **Explicit Dependencies**: Dependencies are explicitly passed to the factory function
2. **Immutable State**: The tool functions are pure functions with no side effects
3. **Testability**: The tool functions are easy to test in isolation
4. **Composability**: The tool functions can be easily composed with other functions

The base implementation for all tools is in `base.py`, which provides the `create_tool` function that creates a tool function with metadata.

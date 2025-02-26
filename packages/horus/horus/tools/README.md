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

The monitor tool is used to enhance monitoring of assets during suspicious activity.

```python
from horus.tools import create_monitor_tool

# Create a monitor tool
monitor_tool = create_monitor_tool()

# Use the tool
result = monitor_tool({
    "asset": "All Base Chain Positions",
    "duration": "48h",
    "threshold": "5%"
})
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

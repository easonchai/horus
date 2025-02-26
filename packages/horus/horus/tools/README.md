# Horus Security Tools

This directory contains tools that can be used by the Horus security agent to perform various security actions.

## Overview

The tools in this directory are designed to be used by the Horus security agent to respond to security threats. Each tool implements a specific security action, such as withdrawing funds, revoking permissions, or monitoring assets.

## Tool Architecture

All tools inherit from the base `BaseTool` class, which defines a common interface for all tools. The `BaseTool` class requires all tools to implement an `execute` method, which takes a dictionary of parameters and returns a string describing the action taken.

## Available Tools

### WithdrawalTool

The `WithdrawalTool` is used to withdraw funds from protocols in case of a security threat. It takes the following parameters:

- `token`: The token to withdraw.
- `amount`: The amount to withdraw.
- `destination`: The destination for the withdrawn funds.
- `chain_id`: The chain ID.

### RevokeTool

The `RevokeTool` is used to revoke permissions from protocols in case of a security threat. It takes the following parameters:

- `token_address` or `token`: The token address or symbol to revoke permissions from.
- `protocol`: The protocol to revoke permissions from.
- `chain_id`: The chain ID.

### MonitorTool

The `MonitorTool` is used to monitor assets for suspicious activity in case of a security threat. It takes the following parameters:

- `asset`: The asset to monitor.
- `duration`: The duration to monitor for.

## Adding New Tools

To add a new tool, create a new file in this directory with a class that inherits from `BaseTool`. Implement the `execute` method to perform the desired action. Then, update the `__init__.py` file to import and expose your new tool.

Example:

```python
from .base import BaseTool

class MyNewTool(BaseTool):
    def execute(self, parameters):
        # Your implementation here
        return "Action completed successfully."
```

## Testing

You can test the tools using the `tests/test_security.py` script. Each tool has a dedicated test function that demonstrates how to use it.

To run the tests:

```bash
# Run from the project root
python -m tests.test_security
```

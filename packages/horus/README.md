# Horus - Crypto Security Monitoring Agent

Horus is a security monitoring agent for cryptocurrency wallets that protects users' funds by taking appropriate actions when security threats are detected.

## Features

- **Multi-Action Security Response**: Horus can execute multiple security actions in sequence based on the nature of the threat.
- **Intelligent Threat Analysis**: Uses OpenAI to analyze security alerts and determine the best course of action.
- **Twitter Security Monitoring**: Automatically monitors trusted Twitter accounts for cryptocurrency security threats and takes appropriate actions.
- **Dependency Graph Analysis**: Utilizes token dependency information to make intelligent decisions about protocol relationships.
- **User Balance Awareness**: Takes into account user's portfolio positions when making security decisions.
- **Dynamic Tool Calling**: Automatically selects appropriate tools for different security scenarios.
- **Flexible Operational Modes**: Supports multiple operational modes, including mock modes for testing and development.
- **Modular Tool Architecture**: Uses a modular tool architecture for easy extension with new security actions.
- **AgentKit Integration**: Leverages Coinbase's AgentKit for secure blockchain interactions, including token approval revocation.

## Overview

Horus is a cryptocurrency security monitoring agent designed to detect and respond to potential security threats through Twitter monitoring and AI-powered analysis.

## Key Features

- Real-time monitoring of trusted security Twitter accounts
- AI-powered analysis of security threats using OpenAI
- Customizable action plans for different threat scenarios
- Dependency-aware token and protocol management
- Position-aware security decision making
- Mock mode for testing without Twitter API credentials
- Interactive CLI for manual security alert processing

## How It Works

Horus uses a sophisticated approach to handle security threats:

1. **Alert Analysis**: When a security alert is received, Horus uses OpenAI to analyze the threat and determine the appropriate response.

2. **Action Plan Generation**: Instead of just taking a single action, Horus generates a complete action plan that may include multiple steps in the optimal sequence.

3. **Dependency Graph Analysis**: The system analyzes the dependency relationships between tokens and protocols to understand how security issues may propagate through the system.

4. **User Position Consideration**: Horus examines the user's current token positions to prioritize protecting the most at-risk assets.

5. **Sequential Execution**: The agent executes the action plan steps in sequence, with each step potentially modifying the plan based on results.

6. **AgentKit-Powered Operations**: For blockchain operations like token approval revocation, Horus uses Coinbase's AgentKit to securely interact with the blockchain.

## Configuration Files

Horus uses multiple configuration files to store important information:

1. **Dependency Graph** (`/config/dependency_graph.json`): Defines relationships between tokens and protocols, including:
   - Derivative tokens and their underlying assets
   - Chain IDs and protocol information
   - Exit functions with their contract types and function signatures

2. **User Balances** (`/user_data/user_balances.json`): Stores user portfolio information:
   - Wallet addresses
   - Token balances across different chains
   - Positions in various protocols with detailed share and liquidity information

3. **Tokens Configuration** (`/config/tokens.json`): Contains token metadata:
   - Token names, symbols, and decimals
   - Contract addresses for different networks

## Security Tools

Horus implements a modular tool architecture that allows it to respond to security threats in various ways. Each tool is responsible for executing a specific security action.

### Available Tools

- **WithdrawalTool**: Withdraws funds from compromised protocols to secure addresses
- **RevokeTool**: Revokes permissions for compromised tokens or protocols using AgentKit
- **MonitorTool**: Monitors assets for suspicious activity

The tools are implemented as Python classes that inherit from the base `BaseTool` class. Each tool implements an `execute` method that takes a dictionary of parameters and returns a string describing the action taken.

For more information about the tools, see the [tools README](/packages/horus/horus/tools/README.md).

## Getting Started

See the [Setup Instructions](./docs/setup_instructions.md) for detailed information on installation and configuration.

### Installation

1. Clone the repository
2. Install dependencies with Poetry:
   ```
   poetry install
   ```
3. Copy `.env.example` to `.env` and fill in your API keys

### Running Tests

To run the tests, use the following command:

```bash
# Run all tests
python -m pytest

# Run a specific test
python -m tests.test_security
python -m tests.test_twitter_monitor
python -m tests.test_agent_setup
```

### Quick Start

1. Clone the repository and navigate to the project directory
2. Create a `.env` file based on `.env.example`
3. Install dependencies: `poetry install`
4. Run Horus with mock Twitter data but real OpenAI: 
   ```
   poetry run python -m horus.cli.app
   ```

### Available Modes

Horus supports different operational modes:

1. **Full Mock Mode**: Uses mock Twitter data and mock OpenAI responses
   - No API keys required
   - Best for initial testing

2. **Mock Twitter + Real OpenAI Mode** (Default): Uses mock Twitter data but real OpenAI calls
   - Requires OPENAI_API_KEY in .env
   - Good for testing OpenAI integration without Twitter API setup

3. **Real Twitter + Real OpenAI Mode**: Uses real Twitter API and real OpenAI
   - Requires all Twitter API credentials and OPENAI_API_KEY in .env
   - For production use

### Command-Line Options

- `--interval <seconds>`: Set the Twitter monitoring interval (default: 300 seconds)
- `--test`: Run a test scenario with predefined security alerts

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd <repository-directory>/packages/horus

# Install dependencies using Poetry
poetry install
```

For detailed setup instructions, including prerequisites, environment configuration, and troubleshooting, see the [Setup Instructions](docs/setup_instructions.md).

## Usage

### Running the Agent

```bash
# Run the interactive agent
poetry run python horus/main.py
# Or use the script
poetry run dev
```

### Testing Multi-Action Scenarios

The agent includes a test function that demonstrates handling complex security scenarios requiring multiple actions in sequence:

```bash
# Run the test scenario
poetry run python horus/main.py --test
# Or use the dedicated test script
poetry run test
```

By default, the agent runs in interactive mode. You can use the `--test` flag to run the test scenario instead.

```bash
# Run in test mode
poetry run python horus/main.py --test

# Run in interactive mode
poetry run python horus/main.py

# Using scripts
poetry run dev  # Interactive mode
poetry run test # Test scenario
```

## Project Structure

The project is organized into the following directories:

- `horus/`: Main package directory
  - `agents/`: Security and Twitter monitoring agent modules
  - `cli/`: Command-line interface modules
  - `mock/`: Mock data and API client modules
  - `twitter_monitor.py`: Twitter monitoring functionality
  - `main.py`: Main entry point for the application
- `examples/`: Example scripts and usage demos
- `docs/`: Documentation for the project

## Environment Configuration

Create a `.env` file with the following variables:

```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Twitter API Keys (optional, only needed if not using mock mode)
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Coinbase Developer Platform API Keys (for AgentKit integration)
CDP_API_KEY_NAME=your_cdp_api_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_api_key_private_key

# Horus Configuration
USE_MOCK_DATA=true  # Controls Twitter data mocking
```

## Documentation

Detailed documentation for Horus features is available in the [docs](docs/) directory:

- [Twitter Monitoring Process Flow](docs/twitter_monitoring_flow.md) - Detailed explanation of the Twitter monitoring feature
- [Twitter Monitoring Diagram](docs/twitter_monitoring_diagram.md) - Visual diagram of the Twitter monitoring process flow

Example scripts demonstrating Horus features are available in the [examples](examples/) directory:

- [Twitter Monitor Demo](examples/twitter_monitor_demo.py) - Demonstrates the Twitter monitoring functionality

## Twitter Security Monitoring

Horus includes a Twitter monitoring feature that automatically scans tweets from trusted security accounts for cryptocurrency threats:

```bash
# Run with Twitter monitoring enabled
poetry run python horus/main.py --twitter

# Run with Twitter monitoring and custom check interval (in seconds)
poetry run python horus/main.py --twitter --interval 300
```

The Twitter monitor:
1. Fetches tweets from trusted security accounts
2. Filters tweets for security relevance using keyword matching
3. Analyzes filtered tweets with OpenAI to determine if they describe real security threats
4. Formats and sends alerts to the Horus security agent for processing

To use this feature, you need to set up Twitter API credentials in your `.env` file:
```
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

## Example Security Alert

```
URGENT SECURITY ALERT: We've detected a critical vulnerability in the Uniswap V3 protocol
affecting the USDC/ETH pool. The vulnerability allows attackers to drain funds from liquidity
providers. We've already seen multiple wallets being exploited. Your wallet has $50,000 USDC
in this pool that needs to be secured immediately. After withdrawing, you should convert to
a safer asset until the vulnerability is patched.

Your safe wallet address is: 0x1234567890abcdef1234567890abcdef12345678
```

## Response

Horus will analyze the alert and execute a sequence of actions:

1. **Withdrawal**: First, withdraw all USDC from the vulnerable Uniswap pool to a safe wallet address.
2. **Swap**: Then, swap the USDC for a safer asset like ETH until the vulnerability is patched.
3. **Revoke**: Finally, revoke permissions for the compromised Uniswap V3 protocol to prevent any future unauthorized transactions.

The agent provides detailed reasoning for each action and handles the execution of the complete action plan in the optimal sequence.

### Example Output

```
Reasoning: This alert indicates that the Uniswap V3 protocol, specifically the USDC/ETH pool, has a critical vulnerability that could allow attackers to drain funds. The wallet in question has significant funds (USDC worth $50,000) in this pool. To prevent potential loss, we need to withdraw the funds from the compromised protocol and then swap the tokens for a different, safer asset until the vulnerability is rectified.

Action plan contains 3 steps
Executing step 1: withdrawal
Explanation: We first need to withdraw the funds from the compromised protocol to prevent them from being drained by any attackers exploiting the identified vulnerability.
WITHDRAWAL TOOL CALLED: Withdrawing all USDC to 0x1234567890abcdef1234567890abcdef12345678

Executing step 2: swap
Explanation: After securing the funds, we then need to swap them to a safer asset to prevent possible loss if the USDC token is further compromised.
SWAP TOOL CALLED: Swapping all USDC to ETH

Executing step 3: revoke
Explanation: Lastly, we should revoke the permissions for the compromised protocol to prevent any future unauthorized transactions.
AGENTKIT REVOKE TOOL CALLED: Revoking permissions for token: None, protocol: Uniswap V3

Horus Response: Emergency withdrawal initiated: all USDC to 0x1234567890abcdef1234567890abcdef12345678.
Emergency swap initiated: all USDC to ETH.
Permission revocation initiated for protocol Uniswap V3.
```

## Contributing

We welcome contributions to the Horus security monitoring agent! Please see our [contributing guidelines](./docs/CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

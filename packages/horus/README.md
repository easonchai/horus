# Horus - Crypto Security Monitoring Agent

Horus is a security monitoring agent for cryptocurrency wallets that protects users' funds by taking appropriate actions when security threats are detected.

## Features

- **Multi-Action Security Response**: Horus can execute multiple security actions in sequence based on the nature of the threat.
- **Intelligent Threat Analysis**: Uses OpenAI to analyze security alerts and determine the best course of action.
- **Twitter Security Monitoring**: Automatically monitors trusted Twitter accounts for cryptocurrency security threats and takes appropriate actions.
- **Flexible Security Tools**:
  - **Revoke**: Revoke permissions for compromised tokens or protocols
  - **Swap**: Swap vulnerable tokens for safer alternatives
  - **Withdrawal**: Withdraw funds from compromised protocols to secure addresses

## Overview

Horus is a cryptocurrency security monitoring agent designed to detect and respond to potential security threats through Twitter monitoring and AI-powered analysis.

## Key Features

- Real-time monitoring of trusted security Twitter accounts
- AI-powered analysis of security threats using OpenAI
- Customizable action plans for different threat scenarios
- Mock mode for testing without Twitter API credentials
- Interactive CLI for manual security alert processing

## How It Works

Horus uses a sophisticated approach to handle security threats:

1. **Alert Analysis**: When a security alert is received, Horus uses OpenAI to analyze the threat and determine the appropriate response.

2. **Action Plan Generation**: Instead of just taking a single action, Horus generates a complete action plan that may include multiple steps in the optimal sequence.

3. **Sequential Execution**: The agent executes each action in the plan in order, with proper error handling between steps.

4. **Tool Composition**: The system can compose different tools together in various sequences depending on the specific security scenario. For example:
   - For a compromised token: Revoke permissions → Swap to a safer asset
   - For a vulnerable protocol: Withdraw funds → Swap to a safer asset → Revoke permissions
   - For a wallet compromise: Withdraw all funds → Revoke all permissions

This approach allows Horus to handle complex security scenarios that require multiple coordinated actions to fully secure the user's assets.

## Getting Started

See the [Setup Instructions](./docs/setup_instructions.md) for detailed information on installation and configuration.

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

Create a `.env` file based on `.env.example` with the following variables:

```
# Twitter API (Optional if USE_MOCK_DATA=true)
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# OpenAI API (Required for real OpenAI analysis)
OPENAI_API_KEY=your_openai_api_key

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
Reasoning: This alert indicates that the Uniswap V3 protocol, specifically the USDC/ETH pool, has a critical vulnerability that could allow attackers to drain funds. The wallet in question has significant funds (USDC worth $50,000) in this pool. To prevent potential loss, we need to withdraw the funds from the vulnerable protocol and then swap the tokens for a different, safer asset until the vulnerability is rectified.

Action plan contains 3 steps
Executing step 1: withdrawal
Explanation: We first need to withdraw the funds from the compromised protocol to prevent them from being drained by any attackers exploiting the identified vulnerability.
WITHDRAWAL TOOL CALLED: Withdrawing all USDC to 0x1234567890abcdef1234567890abcdef12345678

Executing step 2: swap
Explanation: After securing the funds, we then need to swap them to a safer asset to prevent possible loss if the USDC token is further compromised.
SWAP TOOL CALLED: Swapping all USDC to ETH

Executing step 3: revoke
Explanation: Lastly, we should revoke the permissions for the compromised protocol to prevent any future unauthorized transactions.
REVOKE TOOL CALLED: Revoking permissions for token: None, protocol: Uniswap V3

Horus Response: Emergency withdrawal initiated: all USDC to 0x1234567890abcdef1234567890abcdef12345678.
Emergency swap initiated: all USDC to ETH.
Permission revocation initiated for protocol Uniswap V3.
```

## Contributing

We welcome contributions to the Horus security monitoring agent! Please see our [contributing guidelines](./docs/CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

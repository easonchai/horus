# Horus Project Overview

## Project Purpose
Horus is a crypto security monitoring agent designed to protect users' funds by automatically detecting and responding to security threats in the cryptocurrency space. It continuously monitors trusted sources for security alerts and can take automated protective actions to secure user assets.

## Key Components

### 1. Security Agent (Core Component)
- Processes security alerts and determines appropriate actions
- Uses OpenAI's AI to analyze alerts and decide on actions
- Integrates with various security tools
- Handles mock responses for testing without API keys
- Implemented with a functional programming approach for better testability

### 2. Twitter Monitoring
- Scans tweets from trusted security accounts for potential threats
- Filters relevant tweets using security keywords
- Analyzes tweets with OpenAI to identify real threats
- Can run in mock mode for testing without Twitter API credentials
- Runs in a background thread for continuous monitoring

### 3. Tool Architecture
- Uses functional programming approach with higher-order functions and closures
- Each tool is created using a factory function that returns a callable function
- Replaces earlier class-based approach using a BaseTool abstract class
- Provides better modularity, testability, and composability
- Makes dependencies explicit and reduces coupling

### 4. Available Security Tools
- **WithdrawalTool**: Safely withdraws funds from compromised protocols
- **RevokeTool**: Revokes permissions from compromised tokens using Coinbase's AgentKit
- **MonitorTool**: Enhances monitoring of assets during suspicious activity
- **SwapTool**: Swaps tokens for safer assets in compromised situations

### 5. CLI Interface
- Provides a command-line interface for interacting with the agent
- Supports interactive mode for manually entering security alerts
- Can run in test mode with predefined alerts
- Starts Twitter monitoring in a background thread

## Technical Architecture

### OpenAI Integration
- Used for analyzing security alerts and Twitter content
- Generates appropriate security actions based on the context
- Supports mock mode for testing without API keys

### Coinbase AgentKit Integration
- Used for blockchain interactions, especially for the RevokeTool
- Provides wallet and action providers for executing transactions
- Supports multiple EVM networks including Ethereum, Base, Arbitrum, Optimism, and Polygon

### Configuration System
- Uses JSON configuration files for tokens, protocols, and dependency graphs
- Supports environment variables for API keys and other settings
- Provides mock data for testing without real APIs

## Operation Modes
1. **Full Mock Mode**: Uses mock data for both Twitter and OpenAI (no API keys needed)
2. **Default Mode**: Uses mock Twitter data but real OpenAI API (only OpenAI API key needed)
3. **Full Real Mode**: Uses real Twitter and OpenAI APIs (all API keys needed)

## Development Environment
- **Language**: Python
- **Dependency Management**: Poetry for Python dependencies
- **Runtime Management**: mise for managing Python and Node.js versions
- **Project Structure**: Monorepo with multiple packages

## Key Design Patterns
- Functional programming approach with higher-order functions
- Factory functions for creating tools with dependencies
- Closure pattern for maintaining state
- Mock implementations for testing without external dependencies
- Background thread for continuous monitoring

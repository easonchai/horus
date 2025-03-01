# Horus DeFi Protection System

Horus is an AI-powered security monitoring system for DeFi protocols, designed to detect and respond to potential threats in real-time. Named after the ancient Egyptian god of protection, Horus constantly watches over your blockchain assets and provides timely security interventions.

## 🚀 Features

- **Real-time Monitoring**: Scans Twitter and other sources for DeFi security threats
- **Threat Analysis**: Uses AI to assess potential risks and vulnerabilities
- **Automated Response**: Provides emergency actions for asset protection
- **Multi-Protocol Support**: Works with multiple DeFi protocols (Uniswap, Beefy, etc.)
- **Wallet Integration**: Connects directly to your wallet for immediate action

## 🔧 Core Components

The Horus system consists of several key components:

- **Signal Processor**: Monitors external sources for security alerts
- **Agent System**: AI-powered analysis and decision making
- **Action Providers**: Protocol-specific modules for executing protective measures
  - **Revoke Provider**: Revokes token approvals from suspicious contracts
  - **Swap Provider**: Executes emergency swaps to safer assets
  - **Withdrawal Provider**: Withdraws funds from protocols under threat

## 🛠 Setup

### Prerequisites

- Node.js >= 16.x
- Docker and Docker Compose (for containerized deployment)
- Ethereum wallet with Base Sepolia testnet access

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```
PRIVATE_KEY=your_wallet_private_key
LOG_LEVEL=1  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR
```

⚠️ **Security Note**: Never share your private key or commit it to version control.

### Installation

```bash
# Navigate to the project directory
cd packages/horus-final

# Install dependencies
npm install
```

### Running with Docker

```bash
# Build and start the container
docker-compose up --build
```

### Local Development

```bash
# Run in development mode with hot reloading
npm run dev

# Build and run for production
npm run build
npm start
```

## 📖 Usage

### Monitoring for Threats

Horus automatically monitors configured information sources for security threats. When running, it will:

1. Poll Twitter for relevant security alerts
2. Process and analyze signal content
3. Alert you of potential threats
4. Offer protective actions based on threat analysis

### Emergency Actions

When a threat is detected, you can use any of these protection mechanisms:

- **Token Revocation**: Revoke approvals from compromised contracts

  ```
  // Example of revoking a suspicious approval
  revoke-token-approval for USDC from 0x1234...5678
  ```

- **Emergency Withdrawal**: Pull funds from at-risk protocols
  ```
  // Example of emergency withdrawal
  emergency-withdraw-all with prioritizeSafety=true
  ```

## 🔍 Project Structure

```
src/
├── action-providers/          # Protocol-specific action providers
│   ├── revoke-provider.ts     # Token approval revocation
│   ├── swap-provider.ts       # Token swap functionality
│   └── withdrawal-provider.ts # Protocol withdrawal functionality
├── data/                      # Configuration data
│   ├── protocols.json         # Protocol addresses and ABIs
│   └── tokens.json            # Token configurations
├── utils/                     # Utility functions
│   └── logger.ts              # Logging utility
├── agent.ts                   # AI agent implementation
├── agentKit.ts                # AgentKit integration
├── index.ts                   # Application entry point
├── signal-processor.ts        # Signal processing system
├── tweet-generator.ts         # Twitter data source
├── types.ts                   # Type definitions
└── wallet.ts                  # Wallet connection utility
```

## 🧪 Testing

To run the test suite:

```bash
npm test
```

## 📝 Logging

Horus includes a comprehensive logging system with configurable log levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General information about system operation
- **WARN**: Warning conditions that might require attention
- **ERROR**: Error conditions that prevent normal operation

Configure the log level in your `.env` file or using the `setLogLevel` function.

## 🛡️ Security Considerations

- Always review permissions before approving transactions
- Regularly check token approvals and revoke unused permissions
- Keep your wallet's private key secure
- Run Horus continuously for maximum protection

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

For questions or support, please open an issue in the GitHub repository.

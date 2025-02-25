# Horus with Coinbase Agent Kit

Horus is an application that integrates with Coinbase Agent Kit to provide a simple interface for interacting with cryptocurrency wallets and blockchain operations.

## Features

- Create and manage cryptocurrency wallets
- Check wallet balances
- Send and receive cryptocurrency
- Interact with smart contracts
- And more!

## Prerequisites

- Python 3.10.12 or higher
- Poetry for dependency management
- Coinbase Developer Platform API credentials
- OpenAI API key

## Setup

1. Clone the repository
2. Navigate to the Horus package directory:
   ```
   cd packages/horus
   ```
3. Install dependencies:
   ```
   poetry install
   ```
4. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```
5. Edit the `.env` file and add your API credentials:
   - `CDP_API_KEY_NAME`: Your Coinbase Developer Platform API key name
   - `CDP_API_KEY_PRIVATE_KEY`: Your Coinbase Developer Platform API private key
   - `OPENAI_API_KEY`: Your OpenAI API key

## Usage

1. Run the application:
   ```
   poetry run dev
   ```
2. Interact with the application through the command line interface.
3. Type 'exit' to quit the application.

## Example Commands

Here are some example commands you can try:

- "Create a new wallet"
- "Check my wallet balance"
- "Send 0.01 ETH to 0x..."
- "Get the current price of ETH"

## API Keys

To obtain the necessary API keys:

1. **Coinbase Developer Platform API credentials**:

   - Sign up at [Coinbase Developer Platform](https://docs.cdp.coinbase.com/)
   - Create an API key in the dashboard

2. **OpenAI API key**:
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Create an API key in the dashboard

## Notes

- This application uses the Base Sepolia testnet by default. You can change this by setting the `CDP_NETWORK` environment variable.
- Be careful when using real cryptocurrency networks. Always test with testnets first.

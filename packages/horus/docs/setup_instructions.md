# Horus Setup Instructions

This document provides detailed instructions for setting up and developing the Horus security monitoring agent.

## Prerequisites

Before installing Horus, ensure you have the following prerequisites installed on your system:

- **Python**: Version 3.10 or higher
- **Poetry**: For dependency management
- **Git**: For version control
- **Node.js and npm**: For the turborepo monorepo setup
- **Fish shell**: Recommended for command line interaction (though not strictly required)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ethDenver2025.git
cd ethDenver2025
```

### 2. Install Root Dependencies

The project uses Turborepo for monorepo management. Install the root dependencies:

```bash
npm install
```

### 3. Install Horus Dependencies

Navigate to the Horus package directory and install its dependencies using Poetry:

```bash
cd packages/horus
poetry install
```

### 4. Set Up Environment Variables

Create a `.env` file in the Horus package directory:

```bash
cp .env.example .env  # If an example file exists
```

Then edit the `.env` file with the following variables:

```
# Twitter API (Only needed if not using mock mode)
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# OpenAI API (Optional if using mock mode)
OPENAI_API_KEY=your_openai_api_key

# Horus Configuration
USE_MOCK_DATA=true  # Set to false to use real API calls
```

## Development Workflow

### Running the Application

You can run the Horus agent in various modes:

```bash
# Run the interactive agent
poetry run python horus/main.py

# Run with Twitter monitoring enabled
poetry run python horus/main.py --twitter

# Run with Twitter monitoring and custom check interval (in seconds)
poetry run python horus/main.py --twitter --interval 300

# Run a test scenario
poetry run python horus/main.py --test
```

### Using NPM Scripts

The project provides npm scripts for common tasks:

```bash
# Run the development server
npm run dev -w packages/horus

# Run tests
npm run test -w packages/horus
```

### Using Poetry Scripts

If you prefer to use Poetry directly:

```bash
# Run the development server
poetry run dev

# Run tests
poetry run test
```

## Project Structure

The Horus project follows a modular architecture:

```
packages/horus/
├── horus/               # Main package
│   ├── agents/          # Agent implementations
│   │   ├── security_agent.py
│   │   └── twitter_agent.py
│   ├── cli/             # Command line interface
│   │   └── app.py
│   ├── mock/            # Mock implementations for testing
│   │   ├── openai_client.py
│   │   └── twitter_data.py
│   ├── utils/           # Utility functions
│   │   └── helpers.py
│   └── main.py          # Entry point
├── examples/            # Example scripts
│   └── twitter_monitor_demo.py
├── tests/               # Test suite
└── docs/                # Documentation
```

## Running in Mock Mode

By default, Horus runs in mock mode, which doesn't require any API credentials. This is useful for development and testing:

1. Ensure `USE_MOCK_DATA=true` is set in your `.env` file
2. Run the application normally using any of the commands above

Mock mode simulates:
- Twitter API responses with predefined tweets
- OpenAI API responses for security analysis
- Web3 interactions for executing security actions

## Running with Real APIs

To run Horus with real API calls:

1. Set `USE_MOCK_DATA=false` in your `.env` file
2. Ensure all API credentials are properly configured in the `.env` file
3. Run the application using any of the commands above

## Troubleshooting

### Common Issues

#### Poetry Installation Problems

If you encounter issues with Poetry:

```bash
# Update Poetry to the latest version
curl -sSL https://install.python-poetry.org | python3 -

# Ensure Poetry is using the correct Python version
poetry env use python3.10
```

#### Environment Variable Issues

If the application can't find your environment variables:

1. Make sure your `.env` file is in the correct location (packages/horus/.env)
2. Try loading the variables manually:

```bash
set -a
source .env
set +a
```

#### Git Issues

If you encounter Git issues with node_modules:

```bash
# Ensure node_modules are properly ignored
git rm -r --cached node_modules
git commit -m "Remove node_modules from git tracking"
```

## Additional Resources

- [Twitter Monitoring Process Flow](twitter_monitoring_flow.md)
- [Twitter Monitoring Diagram](twitter_monitoring_diagram.md)
- [Main README](../README.md) for general information about Horus

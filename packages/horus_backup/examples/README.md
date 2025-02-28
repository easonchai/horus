# Horus Examples

This directory contains example scripts that demonstrate various features of the Horus security agent.

## Installation

Before running the examples, make sure you have installed all required dependencies using Poetry:

```bash
# Navigate to the project root
cd /path/to/horus

# Install dependencies with Poetry
poetry install
```

If you're using mise for Python version management, it will automatically use the correct Python version as specified in the project configuration.

## Twitter Monitor Demo

This demo demonstrates the Twitter monitoring functionality of the Horus security agent. It fetches tweets from trusted security accounts, filters them for security relevance, analyzes them with OpenAI, and formats security alerts.

### Installation

Before running the demo, make sure you have installed the required dependencies using Poetry:

```bash
# Navigate to the project root
cd ..

# Install dependencies with Poetry
poetry install
```

If you're using mise for Python version management, it will automatically use the correct Python version as specified in the project configuration.

### Running the Demo

#### Mock Mode (Recommended for Testing)

The easiest way to run the demo is in mock mode, which uses pre-defined mock data instead of making actual API calls:

```bash
# Using Poetry
poetry run python examples/twitter_monitor_demo.py --mock

# Or if you're in the examples directory
cd examples
poetry run python twitter_monitor_demo.py --mock
```

This mode doesn't require any API credentials and is perfect for testing and demonstration purposes.

#### Live Mode

To run the demo with actual Twitter API calls, you need to set up the following environment variables:

1. Create a `.env` file in the root directory of the project with the following variables:

```
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
OPENAI_API_KEY=your_openai_api_key
```

2. Run the demo without the `--mock` flag:

```bash
# Using Poetry
poetry run python examples/twitter_monitor_demo.py

# Or if you're in the examples directory
cd examples
poetry run python twitter_monitor_demo.py
```

### Expected Output

The demo will output:

1. Tweets fetched from trusted sources
2. Security-relevant tweets after filtering
3. Analysis of each tweet for security threats
4. Formatted security alerts

### Troubleshooting

If you encounter any issues:

- Make sure you have installed all required dependencies using `poetry install`
- Check that your API credentials are correct (for live mode)
- Try running in mock mode with the `--mock` flag
- If you're still having issues, check the error messages for more information

## Integration with Horus

To integrate Twitter monitoring with the Horus security agent, use the `--twitter` flag when running the main application:

```bash
poetry run python horus/main.py --twitter
```

You can also specify a custom check interval in seconds:

```bash
poetry run python horus/main.py --twitter --interval 300
```

For more details, see the [Twitter Monitoring Process Flow](../docs/twitter_monitoring_flow.md) documentation.

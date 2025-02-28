# Uniswap Imbalance Detector

A monitoring tool that detects liquidity imbalances in Uniswap V3 pools. This tool continuously monitors specified trading pairs and alerts when the spot price deviates significantly from the expected value.

## Features

- Real-time monitoring of Uniswap V3 pools
- Configurable threshold for imbalance detection
- REST API for accessing detected imbalances

## Installation
1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

The application requires a Base Sepolia RPC URL to connect to the Base Sepolia testnet. Set this as an environment variable:

```bash
export BASE_SEPOLIA_RPC_URL="https://your-rpc-endpoint.com"
```

## Usage

Run the application with:

```bash
python main.py
```

This will:
1. Start a background thread that monitors the USDT/USDC pool for imbalances
2. Start a Flask API server on port 5005

### Configuration Parameters

You can modify the following parameters in `main.py`:

- `PAIR_NAME`: The trading pair to monitor (default: "USDT/USDC")
- `THRESHOLD`: The price deviation threshold to trigger alerts (default: 0.25)
- `CHECK_INTERVAL`: Time between checks in seconds (default: 10)
- `API_PORT`: The port for the API server (default: 5005)

## API Endpoints

The application provides the following REST API endpoints:

### Get All Imbalances

```
GET /api/imbalances
```

Returns a JSON array of all detected imbalances with the following structure:

```json
[
  {
    "timestamp": "2025-02-28T15:30:00.123456",
    "pair_name": "USDT/USDC",
    "spot_price": 1.26,
    "threshold": 0.25,
    "deviation": 0.26
  },
  ...
]
```

### Clear All Imbalances

```
POST /api/imbalances/clear
```

Clears all detected imbalances and returns:

```json
{
  "status": "cleared"
}
```

## How It Works
1. The application connects to the Uniswap V3 pool contract on the Base Sepolia testnet
2. It periodically fetches the current spot price from the pool
3. If the spot price deviates from 1.0 by more than the configured threshold, it records an imbalance
4. Detected imbalances can be accessed via the REST API
from monitor import start_monitoring_thread
from api import start_api_server

if __name__ == "__main__":
    # Configuration
    PAIR_NAME = "USDT/USDC"
    THRESHOLD = 0.25
    CHECK_INTERVAL = 10  # seconds
    API_PORT = 5005
    
    # Start monitoring in a background thread
    print(f"Starting liquidity imbalance detector for {PAIR_NAME}")
    monitor_thread = start_monitoring_thread(
        pair_name=PAIR_NAME,
        threshold=THRESHOLD,
        interval=CHECK_INTERVAL
    )
    
    # Start the API server (this will block until the server is stopped)
    print(f"Starting API server on port {API_PORT}")
    start_api_server(port=API_PORT)

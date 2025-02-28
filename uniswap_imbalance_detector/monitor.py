import time
import threading
from pool import get_pool_data
from imbalance_controller import record_imbalance

def monitor_liquidity(pair_name="USDT/USDC", threshold=0.25, interval=60):
    """
    Background thread function that monitors liquidity and detects imbalances.
    
    Args:
        pair_name (str): The trading pair to monitor (default: "USDT/USDC")
        threshold (float): The price deviation threshold to trigger alerts (default: 0.25)
        interval (int): Time between checks in seconds (default: 60)
    """
    print(f"Starting liquidity monitoring for {pair_name} with threshold {threshold}")
    
    while True:
        pool_data = get_pool_data(pair_name)
        if "error" in pool_data:
            print(f"Error fetching pool data for {pair_name}: {pool_data['error']}")
            time.sleep(interval)
            continue

        spot_price = pool_data["spot_price"]
        
        # Log monitoring activity
        print(f"📊 Pair: {pair_name}, Spot price: {spot_price:.8f}")
        
        # Check for imbalance
        deviation = abs(spot_price - 1.0)
        if deviation >= threshold:
            # Record the imbalance
            imbalance_event = record_imbalance(
                pair_name=pair_name,
                spot_price=spot_price,
                threshold=threshold,
                deviation=deviation
            )
            
            # Log the detected imbalance
            print(
                f"🚨 Liquidity Imbalance Detected! "
                f"Spot price ({spot_price:.4f}) deviates from 1.0 by ≥{threshold:.2f} (threshold)"
            )
        
        time.sleep(interval)

def start_monitoring_thread(pair_name="USDT/USDC", threshold=0.25, interval=1):
    """
    Starts the background monitoring thread.
    
    Args:
        pair_name (str): The trading pair to monitor (default: "USDT/USDC")
        threshold (float): The price deviation threshold to trigger alerts (default: 0.25)
        interval (int): Time between checks in seconds (default: 1)
        
    Returns:
        threading.Thread: The started monitoring thread
    """
    monitor_thread = threading.Thread(
        target=monitor_liquidity,
        args=(pair_name, threshold, interval),
        daemon=True
    )
    monitor_thread.start()
    
    return monitor_thread

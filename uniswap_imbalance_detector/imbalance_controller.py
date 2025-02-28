import threading
from datetime import datetime

# Global variables for background monitoring
detected_imbalances = []
monitoring_lock = threading.Lock()

def record_imbalance(pair_name, spot_price, threshold, deviation):
    """
    Records an imbalance event with thread safety.
    
    Args:
        pair_name (str): The trading pair name (e.g., "USDT/USDC")
        spot_price (float): The current spot price
        threshold (float): The threshold that was exceeded
        deviation (float): The amount of deviation from the expected price
    """
    imbalance_event = {
        "timestamp": datetime.now().isoformat(),
        "pair_name": pair_name,
        "spot_price": spot_price,
        "threshold": threshold,
        "deviation": deviation
    }
    
    with monitoring_lock:
        detected_imbalances.append(imbalance_event)
    
    return imbalance_event

def get_all_imbalances():
    """
    Returns a copy of all detected imbalances with thread safety.
    """
    with monitoring_lock:
        return list(detected_imbalances)

def clear_imbalances():
    """
    Clears all detected imbalances with thread safety.
    """
    global detected_imbalances
    
    with monitoring_lock:
        detected_imbalances = []

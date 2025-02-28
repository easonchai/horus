from flask import Flask, jsonify
from imbalance_controller import get_all_imbalances, clear_imbalances

# Initialize Flask app
app = Flask(__name__)

@app.route('/api/imbalances', methods=['GET'])
def get_imbalances():
    """
    Returns all detected imbalances.
    """
    return jsonify(get_all_imbalances())

@app.route('/api/imbalances/clear', methods=['POST'])
def clear_imbalances():
    """
    Clears all detected imbalances.
    """
    clear_imbalances()
    return jsonify({"status": "cleared"})

def start_api_server(host='0.0.0.0', port=5000, debug=False):
    """
    Starts the Flask API server.
    
    Args:
        host (str): The host to bind to (default: '0.0.0.0')
        port (int): The port to bind to (default: 5000)
        debug (bool): Whether to run in debug mode (default: False)
    """
    app.run(host=host, port=port, debug=debug)

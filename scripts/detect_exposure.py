#!/usr/bin/env python3
import json
import sys
from typing import Dict, List, Set

def load_json(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

def get_token_address(tokens: dict, symbol: str, chain_id: str) -> str:
    """Get token address from symbol and chain ID."""
    for token in tokens['tokens']:
        if token['symbol'] == symbol:
            return token['networks'].get(chain_id)
    return None

def build_dependency_map(dependency_graph: dict) -> Dict[str, dict]:
    """Build a map of derivative tokens to their underlying tokens."""
    dep_map = {}
    for dep in dependency_graph['dependencies']:
        key = f"{dep['derivativeSymbol']}_{dep['chainId']}"
        dep_map[key] = {
            'protocol': dep['protocol'],
            'underlyings': dep['underlyings'],  # Now just pass the underlyings array as is
            'exitFunctions': dep['exitFunctions']
        }
    return dep_map

def get_underlying_tokens(position_symbol: str, chain_id: str, dep_map: Dict[str, dict], visited: Set[str] = None) -> Set[str]:
    """Recursively get all underlying tokens for a position."""
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion
    if position_symbol in visited:
        return set()
    visited.add(position_symbol)
    
    position_key = f"{position_symbol}_{chain_id}"
    if position_key not in dep_map:
        # If not in dep_map, it's a base token
        return {position_symbol}
        
    underlying_tokens = set()
    for underlying in dep_map[position_key]['underlyings']:
        underlying_symbol = underlying['symbol'] if isinstance(underlying, dict) else underlying
        # Recursively get underlying tokens
        underlying_tokens.update(
            get_underlying_tokens(underlying_symbol, chain_id, dep_map, visited)
        )
    
    return underlying_tokens

def get_exit_path(position_symbol: str, chain_id: str, dep_map: Dict[str, dict], visited: Set[str] = None) -> List[dict]:
    """Get the sequence of transactions needed to fully exit a position."""
    if visited is None:
        visited = set()
    
    if position_symbol in visited:
        return []
    visited.add(position_symbol)
    
    position_key = f"{position_symbol}_{chain_id}"
    if position_key not in dep_map:
        return []
        
    exit_path = []
    # Add this position's exit functions
    exit_path.extend([
        {
            'symbol': position_symbol,
            'protocol': dep_map[position_key]['protocol'],
            'functions': dep_map[position_key]['exitFunctions']
        }
    ])
    
    # Recursively get exit paths for underlying tokens
    for underlying in dep_map[position_key]['underlyings']:
        underlying_symbol = underlying['symbol'] if isinstance(underlying, dict) else underlying
        exit_path.extend(
            get_exit_path(underlying_symbol, chain_id, dep_map, visited)
        )
    
    return exit_path

def find_exposed_positions(
    user_data: dict,
    dep_map: Dict[str, dict],
    compromised_token: str,
    chain_id: str
) -> List[dict]:
    """Find all positions that are exposed to the compromised token."""
    exposed_positions = []
    
    for user in user_data['users']:
        chain_balances = user['chainBalances'].get(chain_id)
        if not chain_balances:
            continue

        # Check direct exposure
        if compromised_token in chain_balances:
            exposed_positions.append({
                'user': user['address'],
                'type': 'direct',
                'token': compromised_token,
                'amount': chain_balances[compromised_token]
            })

        # Check position exposure
        for position in chain_balances.get('positions', []):
            position_key = f"{position['symbol']}_{chain_id}"
            underlying_tokens = get_underlying_tokens(position['symbol'], chain_id, dep_map)
            if compromised_token in underlying_tokens:
                    exposed_positions.append({
                        'user': user['address'],
                        'type': 'position',
                        'position': position,
                        'protocol': dep_map[position_key]['protocol'],
                        'exitFunctions': dep_map[position_key]['exitFunctions']
                    })

    return exposed_positions

def generate_exit_transactions(
    exposed_positions: List[dict],
    protocols: dict,
    dep_map: Dict[str, dict],
    chain_id: str
) -> List[dict]:    
    """Get the sequence of transactions needed to fully exit a position."""
    if visited is None:
        visited = set()
    
    if position_symbol in visited:
        return []
    visited.add(position_symbol)
    
    position_key = f"{position_symbol}_{chain_id}"
    if position_key not in dep_map:
        return []
        
    exit_path = []
    # Add this position's exit functions
    exit_path.extend([
        {
            'symbol': position_symbol,
            'protocol': dep_map[position_key]['protocol'],
            'functions': dep_map[position_key]['exitFunctions']
        }
    ])
    
    # Recursively get exit paths for underlying tokens
    for underlying in dep_map[position_key]['underlyings']:
        exit_path.extend(
            get_exit_path(underlying['symbol'], chain_id, dep_map, visited)
        )
    
    return exit_path

def generate_exit_transactions(
    exposed_positions: List[dict],
    protocols: dict,
    dep_map: Dict[str, dict],
    chain_id: str
) -> List[dict]:
    """Generate transaction data for exiting positions."""
    transactions = []
    
    for pos in exposed_positions:
        if pos['type'] == 'position':
            # Get the full exit path for this position
            exit_path = get_exit_path(pos['position']['symbol'], chain_id, dep_map)
            
            # Generate transactions for each step in the exit path
            for step in exit_path:
                protocol_data = next(
                    p for p in protocols['protocols']
                    if p['name'] == step['protocol']
                )
                
                if step['protocol'] == 'Beefy':
                    # Handle Beefy vault exit
                    vault_address = protocol_data['chains'][chain_id][f"{step['symbol']}-Vault"]
                    transactions.append({
                        'to': vault_address,
                        'function': 'withdraw',
                        'params': {
                            'tokenId': pos['position']['tokenId']
                        }
                    })
                elif step['protocol'] == 'UniswapV3':
                    # Handle Uniswap V3 position exit
                    contract_address = protocol_data['chains'][chain_id]['nonfungiblePositionManager']
                    
                    # Only generate decreaseLiquidity if this is a Uniswap position
                    if 'liquidity' in pos['position']:
                        transactions.append({
                            'to': contract_address,
                            'function': 'decreaseLiquidity',
                            'params': {
                                'tokenId': pos['position']['tokenId'],
                                'liquidity': pos['position']['liquidity'],
                                'amount0Min': 0,  # In production, calculate this from oracle
                                'amount1Min': 0,  # In production, calculate this from oracle
                                'deadline': 'DEADLINE'  # In production, current time + buffer
                            }
                        })
                    
                    # Generate collect transaction
                    transactions.append({
                        'to': contract_address,
                        'function': 'collect',
                        'params': {
                            'tokenId': pos['position']['tokenId'],
                            'recipient': pos['user'],
                            'amount0Max': 2**128 - 1,  # uint128 max
                            'amount1Max': 2**128 - 1   # uint128 max
                        }
                    })
            
    return transactions

def main():
    if len(sys.argv) != 3:
        print("Usage: python detect_exposure.py <token_symbol> <chain_id>")
        sys.exit(1)

    compromised_token = sys.argv[1]
    chain_id = sys.argv[2]

    # Load configuration files
    tokens = load_json("config/tokens.json")
    protocols = load_json("config/protocols.json")
    dependency_graph = load_json("config/dependency_graph.json")
    user_data = load_json("user_data/user_balances.json")

    # Build dependency map
    dep_map = build_dependency_map(dependency_graph)

    # Find exposed positions
    exposed_positions = find_exposed_positions(
        user_data, 
        dep_map, 
        compromised_token, 
        chain_id
    )

    if not exposed_positions:
        print(f"No exposure found to {compromised_token} on chain {chain_id}")
        return

    print(f"\nFound {len(exposed_positions)} exposed positions:")
    for pos in exposed_positions:
        if pos['type'] == 'direct':
            print(f"\nDirect exposure:")
            print(f"User: {pos['user']}")
            print(f"Amount: {pos['amount']} {pos['token']}")
        else:
            print(f"\nPosition exposure:")
            print(f"User: {pos['user']}")
            print(f"Position: {pos['position']['symbol']} (ID: {pos['position']['tokenId']})")
            print(f"Protocol: {pos['protocol']}")

    # Generate exit transactions
    transactions = generate_exit_transactions(
        exposed_positions,
        protocols,
        dep_map,
        chain_id
    )

    if transactions:
        print("\nGenerated exit transactions:")
        for tx in transactions:
            print(f"\nContract: {tx['to']}")
            print(f"Function: {tx['function']}")
            print("Parameters:", json.dumps(tx['params'], indent=2))

if __name__ == "__main__":
    main()

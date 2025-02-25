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
            'underlyings': [u['symbol'] for u in dep['underlyings']],
            'exitFunctions': dep['exitFunctions']
        }
    return dep_map

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
            if position_key in dep_map:
                if compromised_token in dep_map[position_key]['underlyings']:
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
    chain_id: str
) -> List[dict]:
    """Generate transaction data for exiting positions."""
    transactions = []
    
    for pos in exposed_positions:
        if pos['type'] == 'position':
            protocol_data = next(
                p for p in protocols['protocols'] 
                if p['name'] == pos['protocol']
            )
            
            contract_address = protocol_data['chains'][chain_id]['nonfungiblePositionManager']
            
            # Generate decreaseLiquidity transaction
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

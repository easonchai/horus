from web3 import Web3
import json
from typing import Dict, List
from eth_typing import Address
from eth_utils import to_checksum_address

# Initialize web3
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))

# Load configuration
with open('config/tokens.json', 'r') as f:
    tokens_config = json.load(f)

with open('config/protocols.json', 'r') as f:
    protocols_config = json.load(f)

# ABI for basic ERC20 and ERC721 functions
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

ERC721_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "tokensOfOwner",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_token_balances(address: str) -> Dict[str, int]:
    """Get all token balances for an address"""
    balances = {}
    chain_id = "84532"  # base-sepolia

    for token in tokens_config['tokens']:
        token_address = token['networks'].get(chain_id)
        if not token_address:
            continue

        contract = w3.eth.contract(
            address=to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        try:
            balance = contract.functions.balanceOf(
                to_checksum_address(address)
            ).call()
            
            balances[token['symbol']] = balance / (10 ** token['decimals'])
        except Exception as e:
            print(f"Error fetching balance for {token['symbol']}: {e}")
            balances[token['symbol']] = 0

    return balances

def get_uniswap_positions(address: str) -> List[int]:
    """Get all Uniswap V3 positions for an address"""
    chain_id = "84532"
    
    # Get NFT position manager address
    nft_manager_address = protocols_config['protocols'][1]['chains'][chain_id]['nonfungiblePositionManager']
    
    contract = w3.eth.contract(
        address=to_checksum_address(nft_manager_address),
        abi=ERC721_ABI
    )
    
    try:
        # Get all token IDs owned by the address
        token_ids = contract.functions.tokensOfOwner(
            to_checksum_address(address)
        ).call()
        return token_ids
    except Exception as e:
        print(f"Error fetching Uniswap positions: {e}")
        return []

def get_beefy_balances(address: str) -> Dict[str, float]:
    """Get all Beefy vault balances for an address"""
    balances = {}
    chain_id = "84532"
    
    # Get vault addresses
    vaults = protocols_config['protocols'][0]['chains'][chain_id]
    
    for vault_name, vault_address in vaults.items():
        contract = w3.eth.contract(
            address=to_checksum_address(vault_address),
            abi=ERC20_ABI  # BeefyVault implements ERC20
        )
        
        try:
            balance = contract.functions.balanceOf(
                to_checksum_address(address)
            ).call()
            balances[vault_name] = balance / (10 ** 18)  # Assuming 18 decimals
        except Exception as e:
            print(f"Error fetching balance for {vault_name}: {e}")
            balances[vault_name] = 0
    
    return balances

def update_user_balances(address: str):
    """Update balances for a user"""
    balances = {
        "tokens": get_token_balances(address),
        "uniswap_v3": {
            "positions": get_uniswap_positions(address)
        },
        "beefy": get_beefy_balances(address)
    }
    
    # Update user_balances.json
    try:
        with open('user_data/user_balances.json', 'r') as f:
            user_balances = json.load(f)
    except FileNotFoundError:
        user_balances = {"users": {}}
    
    user_balances["users"][address] = balances
    
    with open('user_data/user_balances.json', 'w') as f:
        json.dump(user_balances, f, indent=2)

if __name__ == "__main__":
    # Example usage
    address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Example address
    update_user_balances(address)

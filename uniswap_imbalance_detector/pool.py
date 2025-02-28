import os
import json
from web3 import Web3

# Uniswap V3 Pool Contract Addresses
# Obtained via Basescan after getting the fees from Position Manager
# then plugging in the fee tier and addresses into getPool from the uniswap v3 factory
POOL_CONTRACT_ADDRESSES = {
    "USDT/USDC": "0x6465b0631e999C7BD0C26e3F5DF56A414F0B7849"
}

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(os.environ.get("BASE_SEPOLIA_RPC_URL")))

# Load Uniswap V3 Pool Contract ABI
with open("abi/UniswapV3PoolABI.json", "r") as file:
    POOL_ABI = json.load(file)

def get_pool_contract(pair_name):
    """
    Returns a contract instance for the specified Uniswap V3 pool pair.
    """
    address = POOL_CONTRACT_ADDRESSES.get(pair_name)
    if not address:
        raise ValueError(f"Unrecognized pair name: {pair_name}")
    return web3.eth.contract(
        address=web3.to_checksum_address(address),
        abi=POOL_ABI["abi"]
    )

def get_pool_data(pair_name):
    """
    Fetches Uniswap V3 pool's tick price and total liquidity for the given pair.
    """
    pool_contract = get_pool_contract(pair_name)
    try:
        slot0 = pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]  # SqrtPriceX96
        current_tick = slot0[1]    # Tick
        liquidity = pool_contract.functions.liquidity().call()  # Total Liquidity
        return {
            "pair_name": pair_name,
            "sqrt_price_x96": sqrt_price_x96,
            "spot_price": (sqrt_price_x96 / 2**96) ** 2,
            "tick": current_tick,
            "liquidity": liquidity
        }
    except Exception as e:
        return {"pair_name": pair_name, "error": str(e)}

def get_tick_liquidity(pair_name, tick_index):
    """
    Fetches liquidity in a specific tick for the given pair.
    """
    pool_contract = get_pool_contract(pair_name)
    try:
        tick_data = pool_contract.functions.ticks(tick_index).call()
        # index: 0 = liquidityGross, 1 = liquidityNet, ...
        return tick_data[1]  # liquidityNet
    except Exception as e:
        return None

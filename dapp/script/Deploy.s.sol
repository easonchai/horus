// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;
pragma abicoder v2;

import {Script} from "forge-std/Script.sol";
import {console} from "forge-std/console.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {INonfungiblePositionManager} from "@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol";
import {BeefyVault} from "../src/BeefyVault.sol";

contract MockToken is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {
        _mint(msg.sender, 1_000_000 * 10**decimals());
    }

    function decimals() public pure override returns (uint8) {
        return 6;
    }
}

contract Deploy is Script {
    address constant POSITION_MANAGER = 0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2;
    uint24 constant FEE = 500;
    uint256 constant AMOUNT = 10000 * 10**6;
    int24 constant TICK_LOWER = -887270;
    int24 constant TICK_UPPER = 887270;

    function createPool(address token0, address token1) internal {
        INonfungiblePositionManager(POSITION_MANAGER).createAndInitializePoolIfNecessary(
            token0,
            token1,
            FEE,
            79228162514264337593543950336
        );

        ERC20(token0).approve(POSITION_MANAGER, type(uint256).max);
        ERC20(token1).approve(POSITION_MANAGER, type(uint256).max);
    }

    function mintPosition(
        address token0,
        address token1,
        address recipient
    ) internal returns (uint256 tokenId) {
        INonfungiblePositionManager.MintParams memory params = INonfungiblePositionManager.MintParams({
            token0: token0,
            token1: token1,
            fee: FEE,
            tickLower: TICK_LOWER,
            tickUpper: TICK_UPPER,
            amount0Desired: AMOUNT,
            amount1Desired: AMOUNT,
            amount0Min: 0,
            amount1Min: 0,
            recipient: recipient,
            deadline: block.timestamp + 60
        });

        (tokenId,,,) = INonfungiblePositionManager(POSITION_MANAGER).mint(params);
    }

    function run() public {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        address deployer = vm.addr(deployerPrivateKey);

        // Deploy tokens
        MockToken usdc = new MockToken("USD Coin", "USDC");
        MockToken usdt = new MockToken("USD Tether", "USDT");
        MockToken wbtc = new MockToken("Wrapped Bitcoin", "WBTC");
        MockToken eigen = new MockToken("Eigenlayer", "EIGEN");

        console.log("USDC: %s", address(usdc));
        console.log("USDT: %s", address(usdt));
        console.log("WBTC: %s", address(wbtc));
        console.log("EIGEN: %s", address(eigen));

        // Create USDC-USDT pool and position
        (address token0, address token1) = address(usdc) < address(usdt)
            ? (address(usdc), address(usdt))
            : (address(usdt), address(usdc));
        
        createPool(token0, token1);
        uint256 usdcUsdtTokenId = mintPosition(token0, token1, deployer);
        console.log("USDC-USDT Position TokenId: %s", usdcUsdtTokenId);

        // Create WBTC-EIGEN pool and position
        (token0, token1) = address(wbtc) < address(eigen)
            ? (address(wbtc), address(eigen))
            : (address(eigen), address(wbtc));
        
        createPool(token0, token1);
        uint256 wbtcEigenTokenId = mintPosition(token0, token1, deployer);
        console.log("WBTC-EIGEN Position TokenId: %s", wbtcEigenTokenId);

        // Create USDC-EIGEN pool and position
        (token0, token1) = address(usdc) < address(eigen)
            ? (address(usdc), address(eigen))
            : (address(eigen), address(usdc));
        
        createPool(token0, token1);
        uint256 usdcEigenTokenId = mintPosition(token0, token1, deployer);
        console.log("USDC-EIGEN Position TokenId: %s", usdcEigenTokenId);

        // Deploy vaults
        BeefyVault usdcUsdtVault = new BeefyVault(
            INonfungiblePositionManager(POSITION_MANAGER),
            "Beefy USDC-USDT LP",
            "beefyUSDC-USDT"
        );

        BeefyVault wbtcEigenVault = new BeefyVault(
            INonfungiblePositionManager(POSITION_MANAGER),
            "Beefy WBTC-EIGEN LP",
            "beefyWBTC-EIGEN"
        );

        BeefyVault usdcEigenVault = new BeefyVault(
            INonfungiblePositionManager(POSITION_MANAGER),
            "Beefy USDC-EIGEN LP",
            "beefyUSDC-EIGEN"
        );

        console.log("USDC-USDT Vault: %s", address(usdcUsdtVault));
        console.log("WBTC-EIGEN Vault: %s", address(wbtcEigenVault));
        console.log("USDC-EIGEN Vault: %s", address(usdcEigenVault));

        // Deposit positions
        INonfungiblePositionManager nftManager = INonfungiblePositionManager(POSITION_MANAGER);
        
        // nftManager.approve(address(usdcUsdtVault), usdcUsdtTokenId);
        // usdcUsdtVault.deposit(usdcUsdtTokenId);
        // console.log("Deposited USDC-USDT position %s", usdcUsdtTokenId);

        // nftManager.approve(address(wbtcEigenVault), wbtcEigenTokenId);
        // wbtcEigenVault.deposit(wbtcEigenTokenId);
        // console.log("Deposited WBTC-EIGEN position %s", wbtcEigenTokenId);

        // nftManager.approve(address(usdcEigenVault), usdcEigenTokenId);
        // usdcEigenVault.deposit(usdcEigenTokenId);
        // console.log("Deposited USDC-EIGEN position %s", usdcEigenTokenId);

        vm.stopBroadcast();
    }
}

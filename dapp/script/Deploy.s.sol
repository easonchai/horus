// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;
pragma abicoder v2;

import {Script} from "forge-std/Script.sol";
import {console} from "forge-std/console.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {INonfungiblePositionManager} from "@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol";

contract MockToken is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {
        _mint(msg.sender, 1_000_000 * 10**decimals());
    }

    function decimals() public pure override returns (uint8) {
        return 6; // Both USDC and USDT use 6 decimals
    }
}

contract Deploy is Script {

    function run() public {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        address deployer = vm.addr(deployerPrivateKey);
        // Deploy mock tokens
        MockToken usdc = new MockToken("USD Coin", "USDC");
        MockToken usdt = new MockToken("USD Tether", "USDT");
        MockToken wbtc = new MockToken("Wrapped Bitcoin", "WBTC");
        MockToken eigen = new MockToken("Eigenlayer", "EIGEN");

        // Print deployed token addresses
        console.log("USDC deployed at:", address(usdc));
        console.log("USDT deployed at:", address(usdt));
        console.log("WBTC deployed at:", address(wbtc));
        console.log("EIGEN deployed at:", address(eigen));

        // Determine token order
        (address token0, address token1) = address(usdc) < address(usdt)
            ? (address(usdc), address(usdt))
            : (address(usdt), address(usdc));

        INonfungiblePositionManager(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2).createAndInitializePoolIfNecessary(
            token0,
            token1,
            500,
            79228162514264337593543950336
        );

        ERC20(token0).approve(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2, type(uint256).max);
        ERC20(token1).approve(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2, type(uint256).max);

        INonfungiblePositionManager(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2).mint(INonfungiblePositionManager.MintParams({
            token0: token0,
            token1: token1,
            fee: 500, // Fee tier
            tickLower: -50,
            tickUpper: 50,
            amount0Desired: 10000 * 10**6, // amount0Desired
            amount1Desired: 10000 * 10**6, // amount1Desired
            amount0Min: 0, // amount0Min
            amount1Min: 0, // amount1Min
            recipient: deployer, // recipient
            deadline: block.timestamp + 60 // deadline
        }));

        (address token2, address token3) = address(wbtc) < address(eigen)
            ? (address(wbtc), address(eigen))
            : (address(eigen), address(wbtc));

        INonfungiblePositionManager(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2).createAndInitializePoolIfNecessary(
            token2,
            token3,
            500,
            79228162514264337593543950336
        );

        ERC20(token2).approve(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2, type(uint256).max);
        ERC20(token3).approve(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2, type(uint256).max);

        INonfungiblePositionManager(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2).mint(INonfungiblePositionManager.MintParams({
            token0: token2,
            token1: token3,
            fee: 500, // Fee tier
            tickLower: -50,
            tickUpper: 50,
            amount0Desired: 10000 * 10**6, // amount0Desired
            amount1Desired: 10000 * 10**6, // amount1Desired
            amount0Min: 0, // amount0Min
            amount1Min: 0, // amount1Min
            recipient: deployer, // recipient
            deadline: block.timestamp + 60 // deadline
        }));

        (address token4, address token5) = address(usdc) < address(eigen)
            ? (address(usdc), address(eigen))
            : (address(eigen), address(usdc));

        INonfungiblePositionManager(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2).createAndInitializePoolIfNecessary(
            token4,
            token5,
            500,
            79228162514264337593543950336
        );

        ERC20(token4).approve(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2, type(uint256).max);
        ERC20(token5).approve(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2, type(uint256).max);

        INonfungiblePositionManager(0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2).mint(INonfungiblePositionManager.MintParams({
            token0: token4,
            token1: token5,
            fee: 500, // Fee tier
            tickLower: -50,
            tickUpper: 50,
            amount0Desired: 10000 * 10**6, // amount0Desired
            amount1Desired: 10000 * 10**6, // amount1Desired
            amount0Min: 0, // amount0Min
            amount1Min: 0, // amount1Min
            recipient: deployer, // recipient
            deadline: block.timestamp + 60 // deadline
        }));

        vm.stopBroadcast();
    }
}

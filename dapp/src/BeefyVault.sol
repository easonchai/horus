// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;
pragma abicoder v2;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {INonfungiblePositionManager} from "@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol";

contract BeefyVault is ERC721 {
    INonfungiblePositionManager public immutable positionManager;

    constructor(
        INonfungiblePositionManager _positionManager,
        string memory name,
        string memory symbol
    ) ERC721(name, symbol) {
        positionManager = _positionManager;
    }

    function deposit(uint256 tokenId) external {
        // Transfer the Uniswap V3 position to this vault
        positionManager.transferFrom(msg.sender, address(this), tokenId);
        // Mint a receipt token to the user
        _mint(msg.sender, tokenId);
    }

    function withdraw(uint256 tokenId) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        // Burn the receipt token
        _burn(tokenId);
        // Transfer the Uniswap V3 position back to the user
        positionManager.transferFrom(address(this), msg.sender, tokenId);
    }

    function collectFees(uint256 tokenId) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        // Collect fees from the Uniswap V3 position
        positionManager.collect(
            INonfungiblePositionManager.CollectParams({
                tokenId: tokenId,
                recipient: msg.sender,
                amount0Max: type(uint128).max,
                amount1Max: type(uint128).max
            })
        );
    }
}

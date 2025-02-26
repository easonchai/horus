// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;
pragma abicoder v2;

import {IERC721} from "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {INonfungiblePositionManager} from "@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol";

contract BeefyVault is ERC20 {
    INonfungiblePositionManager public immutable nonfungiblePositionManager;
    address public immutable owner;
    mapping(uint256 => address) public tokenOwners;

    constructor(
        string memory name,
        string memory symbol,
        address _nonfungiblePositionManager
    ) ERC20(name, symbol) {
        nonfungiblePositionManager = INonfungiblePositionManager(_nonfungiblePositionManager);
        owner = msg.sender;
    }

    function stake(uint256 tokenId) external {
        // Transfer the NFT to this contract
        nonfungiblePositionManager.transferFrom(msg.sender, address(this), tokenId);
        
        // Store the original owner
        tokenOwners[tokenId] = msg.sender;
        
        // Mint vault tokens 1:1 (in production you'd calculate this based on the position's value)
        _mint(msg.sender, 1e18);
    }

    function withdraw(uint256 tokenId) external {
        require(tokenOwners[tokenId] == msg.sender, "Not token owner");
        
        // Burn vault tokens
        _burn(msg.sender, 1e18);
        
        // Transfer NFT back to owner
        nonfungiblePositionManager.transferFrom(address(this), msg.sender, tokenId);
        
        // Clear storage
        delete tokenOwners[tokenId];
    }

    // Emergency function to collect fees from positions
    function collectFees(uint256 tokenId) external {
        require(msg.sender == owner, "Not owner");
        nonfungiblePositionManager.collect(
            INonfungiblePositionManager.CollectParams({
                tokenId: tokenId,
                recipient: owner,
                amount0Max: type(uint128).max,
                amount1Max: type(uint128).max
            })
        );
    }
}

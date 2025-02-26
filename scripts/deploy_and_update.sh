#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting deployment...${NC}"

# Navigate to dapp directory
cd dapp || exit 1

# Run forge script and capture output
echo -e "${BLUE}Running forge script...${NC}"
OUTPUT=$(forge script script/Deploy.s.sol:Deploy --rpc-url base_sepolia --broadcast)

# Extract addresses using grep and sed
echo -e "${BLUE}Extracting addresses...${NC}"
USDC=$(echo "$OUTPUT" | grep "USDC deployed at:" | sed 's/.*USDC deployed at: \(0x[a-fA-F0-9]*\).*/\1/')
USDT=$(echo "$OUTPUT" | grep "USDT deployed at:" | sed 's/.*USDT deployed at: \(0x[a-fA-F0-9]*\).*/\1/')
WBTC=$(echo "$OUTPUT" | grep "WBTC deployed at:" | sed 's/.*WBTC deployed at: \(0x[a-fA-F0-9]*\).*/\1/')
EIGEN=$(echo "$OUTPUT" | grep "EIGEN deployed at:" | sed 's/.*EIGEN deployed at: \(0x[a-fA-F0-9]*\).*/\1/')

USDC_USDT_VAULT=$(echo "$OUTPUT" | grep "USDC-USDT Vault deployed at:" | sed 's/.*USDC-USDT Vault deployed at: \(0x[a-fA-F0-9]*\).*/\1/')
WBTC_EIGEN_VAULT=$(echo "$OUTPUT" | grep "WBTC-EIGEN Vault deployed at:" | sed 's/.*WBTC-EIGEN Vault deployed at: \(0x[a-fA-F0-9]*\).*/\1/')
USDC_EIGEN_VAULT=$(echo "$OUTPUT" | grep "USDC-EIGEN Vault deployed at:" | sed 's/.*USDC-EIGEN Vault deployed at: \(0x[a-fA-F0-9]*\).*/\1/')

# Print extracted addresses
echo -e "${GREEN}Extracted addresses:${NC}"
echo "USDC: $USDC"
echo "USDT: $USDT"
echo "WBTC: $WBTC"
echo "EIGEN: $EIGEN"
echo "USDC-USDT Vault: $USDC_USDT_VAULT"
echo "WBTC-EIGEN Vault: $WBTC_EIGEN_VAULT"
echo "USDC-EIGEN Vault: $USDC_EIGEN_VAULT"

# Navigate back to root
cd ..

# Update tokens.json
echo -e "${BLUE}Updating tokens.json...${NC}"
jq --arg usdc "$USDC" \
   --arg usdt "$USDT" \
   --arg wbtc "$WBTC" \
   --arg eigen "$EIGEN" \
   '(.tokens[] | select(.symbol == "USDC").networks["84532"]) = $usdc |
    (.tokens[] | select(.symbol == "USDT").networks["84532"]) = $usdt |
    (.tokens[] | select(.symbol == "WBTC").networks["84532"]) = $wbtc |
    (.tokens[] | select(.symbol == "EIGEN").networks["84532"]) = $eigen' \
    config/tokens.json > config/tokens.json.tmp && mv config/tokens.json.tmp config/tokens.json

# Update protocols.json
echo -e "${BLUE}Updating protocols.json...${NC}"
jq --arg usdc_usdt "$USDC_USDT_VAULT" \
   --arg wbtc_eigen "$WBTC_EIGEN_VAULT" \
   --arg usdc_eigen "$USDC_EIGEN_VAULT" \
   '(.protocols[] | select(.name == "Beefy").chains["84532"]) |= 
    (.["beefyUSDC-USDT-Vault"] = $usdc_usdt |
     .["beefyWBTC-EIGEN-Vault"] = $wbtc_eigen |
     .["beefyUSDC-EIGEN-Vault"] = $usdc_eigen)' \
    config/protocols.json > config/protocols.json.tmp && mv config/protocols.json.tmp config/protocols.json

echo -e "${GREEN}Deployment and configuration update complete!${NC}"

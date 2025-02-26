"""
Security agent for the Horus security monitoring system.
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple

from horus.tools import WithdrawalTool, RevokeTool, MonitorTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class SecurityAgent:
    """Security agent for processing security alerts and taking actions."""
    
    def __init__(self, openai_client):
        """Initialize the security agent with an OpenAI client."""
        self.openai_client = openai_client
        # Load configuration files
        self.dependency_graph = self._load_dependency_graph()
        self.user_balances = self._load_user_balances()
        self.tokens_config = self._load_tokens_config()
        
        # Initialize tools
        self.withdrawal_tool = WithdrawalTool(self.dependency_graph, self.user_balances)
        self.revoke_tool = RevokeTool(self.tokens_config)
        self.monitor_tool = MonitorTool()
        
    def _load_dependency_graph(self) -> Dict[str, Any]:
        """
        Load the dependency graph from the configuration file.
        
        Returns:
            Dictionary containing the dependency graph data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            graph_path = os.path.join(base_path, '..', '..', 'config', 'dependency_graph.json')
            
            with open(graph_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading dependency graph: {str(e)}")
            return {"dependencies": []}
            
    def _load_user_balances(self) -> Dict[str, Any]:
        """
        Load user balances from the data file.
        
        Returns:
            Dictionary containing user balance data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            balances_path = os.path.join(base_path, '..', '..', 'user_data', 'user_balances.json')
            
            with open(balances_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading user balances: {str(e)}")
            return {"users": []}
            
    def _load_tokens_config(self) -> Dict[str, Any]:
        """
        Load token configuration from the config file.
        
        Returns:
            Dictionary containing token configuration data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            tokens_path = os.path.join(base_path, '..', '..', 'config', 'tokens.json')
            
            with open(tokens_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading tokens config: {str(e)}")
            return {"tokens": []}
    
    # Helper methods that can be used by the tools
    def get_user_positions(self, user_address: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get positions for a user on a specific chain.
        
        Args:
            user_address: The user's address.
            chain_id: The chain ID.
            
        Returns:
            A list of user positions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not self.user_balances:
            logger.warning("User balances not loaded")
            return []
        
        user_data = self.user_balances.get(user_address, {})
        chain_data = user_data.get(chain_id, {})
        return chain_data.get("positions", [])
        
    def get_exit_functions_for_token(self, token: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get exit functions for a token on a specific chain.
        
        Args:
            token: The token symbol.
            chain_id: The chain ID.
            
        Returns:
            A list of exit functions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not self.dependency_graph:
            logger.warning("Dependency graph not loaded")
            return []
        
        # Find the token in the dependency graph
        for node in self.dependency_graph.get("nodes", []):
            if node.get("symbol") == token and str(node.get("chainId")) == chain_id:
                return node.get("exitFunctions", [])
        
        return []
    
    def get_token_address(self, token_symbol: str, chain_id: str) -> Optional[str]:
        """
        Get the contract address for a token on a specific chain.
        
        Args:
            token_symbol: The symbol of the token.
            chain_id: The chain ID.
            
        Returns:
            Token contract address or None if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        for token in self.tokens_config.get("tokens", []):
            if token.get("symbol") == token_symbol:
                networks = token.get("networks", {})
                return networks.get(chain_id)
        return None
        
    def get_token_dependencies(self, token_symbol: str) -> List[Dict[str, Any]]:
        """
        Get dependencies for a specific token.
        
        Args:
            token_symbol: The symbol of the token.
            
        Returns:
            List of underlying tokens and their information.
        """
        for dependency in self.dependency_graph.get("dependencies", []):
            if dependency.get("derivativeSymbol") == token_symbol:
                return dependency.get("underlyings", [])
        return []
    
    def _prepare_context_for_ai(self) -> str:
        """
        Prepare context information from dependency graph and user balances for the AI.
        
        Returns:
            A string containing formatted context information.
        """
        context = []
        
        # Add information about dependencies
        context.append("DEPENDENCY INFORMATION:")
        for dependency in self.dependency_graph.get("dependencies", [])[:5]:  # Limit to prevent token overflow
            derivative = dependency.get("derivativeSymbol", "unknown")
            protocol = dependency.get("protocol", "unknown")
            chain = dependency.get("chainId", "unknown")
            underlyings = dependency.get("underlyings", [])
            
            underlying_info = []
            for u in underlyings:
                if isinstance(u, dict):
                    underlying_info.append(f"{u.get('symbol', 'unknown')} (ratio: {u.get('ratio', 'unknown')})")
                else:
                    underlying_info.append(str(u))
            
            context.append(f"- {derivative} on {protocol} (Chain: {chain}) is based on: {', '.join(underlying_info)}")
        
        # Add user balance information
        context.append("\nUSER BALANCE INFORMATION:")
        for user in self.user_balances.get("users", []):
            address = user.get("address", "unknown")
            context.append(f"- User: {address}")
            
            for chain_id, balances in user.get("chainBalances", {}).items():
                context.append(f"  Chain {chain_id}:")
                
                # Add token balances
                for token, amount in balances.items():
                    if token != "positions":
                        context.append(f"  - {token}: {amount}")
                
                # Add positions
                if "positions" in balances:
                    context.append(f"  Positions:")
                    for position in balances["positions"]:
                        protocol = position.get("protocol", "")
                        symbol = position.get("symbol", "unknown")
                        token_id = position.get("tokenId", "unknown")
                        shares = position.get("shares", "")
                        liquidity = position.get("liquidity", "")
                        
                        position_info = f"  - {symbol} (ID: {token_id})"
                        if protocol:
                            position_info += f" on {protocol}"
                        if shares:
                            position_info += f", Shares: {shares}"
                        if liquidity:
                            position_info += f", Liquidity: {liquidity}"
                            
                        context.append(position_info)
        
        return "\n".join(context)
        
    def process_security_alert(self, alert_text: str) -> str:
        """
        Process a security alert and determine the appropriate action to take.
        
        Args:
            alert_text: The text of the security alert.
            
        Returns:
            A string describing the action taken.
        """
        try:
            # Prepare context information to include in the OpenAI request
            context = self._prepare_context_for_ai()
            
            # Analyze the security alert with OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are Horus, a security monitoring agent for cryptocurrency wallets and DeFi protocols.
                        Your task is to analyze security alerts and determine the appropriate action to take to protect user funds.
                        
                        You have access to the following information about the user's portfolio:
                        {context}
                        
                        You should understand the relationships between different tokens and protocols to make informed decisions.
                        
                        You should respond with a JSON object containing:
                        1. "reasoning": Your analysis of the security alert and why you're taking the action
                        2. "action_plan": An array of actions to take, each with:
                           - "action": The type of action (e.g., "withdrawal", "revoke", "monitor")
                           - "explanation": A brief explanation of the action
                           - "parameters": The parameters for the action
                        
                        For withdrawal actions, the parameters MUST include:
                        - "token": The exact token symbol to withdraw (must match exactly what's in the user portfolio)
                        - "amount": The amount to withdraw (use "ALL" for full withdrawal)
                        - "destination": The destination address for the withdrawn funds
                        - "chain_id": The chain ID where the token is located
                        
                        For revoke actions, the parameters MUST include:
                        - "token_address": The contract address of the token
                        - "protocol": The protocol to revoke permissions from
                        - "chain_id": The chain ID where the token is located
                        
                        For monitor actions, the parameters MUST include:
                        - "asset": The asset to monitor
                        - "duration": The duration to monitor (e.g., "24h")
                        
                        Only include actions that are necessary to protect user funds. If no action is needed, return an empty array for "action_plan".
                        """
                    },
                    {
                        "role": "user",
                        "content": alert_text
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            response_content = response.choices[0].message.content
            response_json = json.loads(response_content)
            
            # Extract the reasoning and action plan
            reasoning = response_json.get("reasoning", "No reasoning provided.")
            action_plan = response_json.get("action_plan", [])
            
            # Log the reasoning
            logger.info(f"Reasoning: {reasoning}")
            
            # Execute the action plan
            if not action_plan:
                return "No action needed."
            
            logger.info(f"Action plan contains {len(action_plan)} steps")
            result = []
            
            for i, action in enumerate(action_plan):
                action_type = action.get("action")
                explanation = action.get("explanation")
                parameters = action.get("parameters", {})
                
                logger.info(f"Executing step {i+1}: {action_type}")
                logger.info(f"Explanation: {explanation}")
                
                # Execute the action based on its type
                if action_type == "withdrawal":
                    token = parameters.get("token", "unknown")
                    amount = parameters.get("amount", "0")
                    destination = parameters.get("destination", "unknown")
                    
                    logger.info(f"Extracted withdrawal parameters - token: {token}, amount: {amount}, destination: {destination}")
                    logger.info(f"Full parameters from OpenAI: {parameters}")
                    
                    # Use the withdrawal tool to execute the exit function
                    exit_result = self.withdrawal_tool.execute(parameters)
                    result.append(exit_result)
                
                elif action_type == "revoke":
                    token_address = parameters.get("token_address", "unknown")
                    protocol = parameters.get("protocol", "unknown")
                    
                    # Use the revoke tool to execute the revoke function
                    revoke_result = self.revoke_tool.execute(parameters)
                    result.append(revoke_result)
                
                elif action_type == "monitor":
                    asset = parameters.get("asset", "unknown")
                    duration = parameters.get("duration", "24h")
                    
                    # Use the monitor tool to execute the monitoring function
                    monitor_result = self.monitor_tool.execute(parameters)
                    result.append(monitor_result)
                
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    result.append(f"Unknown action: {action_type}")
            
            return " ".join(result)
        
        except Exception as e:
            logger.error(f"Error processing security alert: {str(e)}")
            
            # For invalid API key or connection errors, use mock response
            if "invalid_api_key" in str(e) or "connection" in str(e).lower():
                logger.warning("Using mock response due to API key or connection issue (GPT-4o unavailable)")
                mock_response = {
                    "reasoning": "MOCK RESPONSE: This is a critical security vulnerability that requires immediate action.",
                    "action_plan": [
                        {
                            "action": "withdrawal",
                            "explanation": "Emergency withdrawal of funds to prevent loss",
                            "parameters": {
                                "token": "ETH",
                                "amount": "ALL",
                                "destination": "cold_wallet_1",
                                "chain_id": "1"
                            }
                        },
                        {
                            "action": "revoke",
                            "explanation": "Revoke permissions to prevent further access",
                            "parameters": {
                                "token_address": "0x123456789...",
                                "protocol": "Affected Protocol",
                                "chain_id": "1"
                            }
                        },
                        {
                            "action": "monitor",
                            "explanation": "Monitor for additional suspicious activity",
                            "parameters": {
                                "asset": "All connected wallets",
                                "duration": "72h"
                            }
                        }
                    ]
                }
                
                reasoning = mock_response.get("reasoning", "No reasoning provided.")
                action_plan = mock_response.get("action_plan", [])
                
                logger.info(f"Mock Reasoning: {reasoning}")
                
                if not action_plan:
                    return "No action needed (mock response)."
                
                logger.info(f"Mock Action plan contains {len(action_plan)} steps")
                result = []
                
                for i, action in enumerate(action_plan):
                    action_type = action.get("action")
                    explanation = action.get("explanation")
                    parameters = action.get("parameters", {})
                    
                    logger.info(f"Executing mock step {i+1}: {action_type}")
                    logger.info(f"Mock Explanation: {explanation}")
                    
                    if action_type == "withdrawal":
                        token = parameters.get("token", "unknown")
                        amount = parameters.get("amount", "0")
                        destination = parameters.get("destination", "unknown")
                        
                        # Use a mock version of the withdrawal tool
                        logger.info(f"MOCK WITHDRAWAL TOOL CALLED: Withdrawing {amount} {token} to {destination}")
                        mock_result = f"[MOCK] {self.withdrawal_tool.execute(parameters)}"
                        result.append(mock_result)
                    
                    elif action_type == "revoke":
                        token_address = parameters.get("token_address", "unknown")
                        protocol = parameters.get("protocol", "unknown")
                        
                        # Use a mock version of the revoke tool
                        logger.info(f"MOCK REVOKE TOOL CALLED: Revoking permissions for {token_address} on {protocol}")
                        mock_result = f"[MOCK] {self.revoke_tool.execute(parameters)}"
                        result.append(mock_result)
                    
                    elif action_type == "monitor":
                        asset = parameters.get("asset", "unknown")
                        duration = parameters.get("duration", "24h")
                        
                        # Use a mock version of the monitor tool
                        logger.info(f"MOCK MONITOR TOOL CALLED: Enhanced monitoring for {asset} for the next {duration}")
                        mock_result = f"[MOCK] {self.monitor_tool.execute(parameters)}"
                        result.append(mock_result)
                    
                    else:
                        logger.warning(f"Unknown mock action type: {action_type}")
                        result.append(f"[MOCK] Unknown action: {action_type}")
                
                return " ".join(result)
            
            return f"Error processing security alert: {str(e)}"

"""
Security agent for the Horus security monitoring system.
Class-based implementation.
"""
import json
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from tools import create_monitor_tool
from tools.revoke import RevokeTool
from tools.swap import SwapTool
from tools.withdrawal import WithdrawalTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class SecurityAgent:
    """
    Security agent that processes security alerts and takes appropriate actions.
    
    The SecurityAgent monitors for security threats and can respond with actions such as:
    - Withdrawing funds to a safe address
    - Revoking token permissions
    - Setting up monitoring for specific assets
    - Swapping tokens for safer assets
    
    It uses AI to determine the appropriate response to security alerts.
    """
    
    def __init__(self, openai_client, agent_kit_manager=None, mock_openai=False, mock_twitter=True):
        """
        Initialize the security agent.
    
    Args:
        openai_client: The OpenAI client.
        agent_kit_manager: The AgentKit manager for blockchain transactions. If None, uses global instance.
        mock_openai: Whether to mock OpenAI responses. Should always be False in production.
        mock_twitter: Whether to mock Twitter responses.
        """
        self.openai_client = openai_client
        self.mock_openai = False  # Always set to False to ensure real OpenAI is used
        self.mock_twitter = mock_twitter
        
        # Use the provided agent_kit_manager or the global instance
        from core.agent_kit import \
            agent_kit_manager as global_agent_kit_manager
        self.agent_kit_manager = agent_kit_manager or global_agent_kit_manager
        
        # Load configuration files
        self.dependency_graph = self._load_dependency_graph()
        self.user_balances = self._load_user_balances()
        self.tokens_config = self._load_tokens_config()
        self.protocols_config = self._load_protocols_config()
        
        # Initialize tools
        self.withdrawal_tool = WithdrawalTool(self.tokens_config, self.protocols_config)
        revoke_tool_instance = RevokeTool(self.tokens_config, self.protocols_config)
        self.revoke_tool = revoke_tool_instance.tool
        self.swap_tool = SwapTool(self.tokens_config, self.protocols_config, self.dependency_graph)
        self.monitor_tool = create_monitor_tool()
    
    def __call__(self, alert_text: str) -> str:
        """
        Process a security alert and take appropriate action.
        
        This makes the instance callable, maintaining compatibility with the functional approach.
        
        Args:
            alert_text: The text of the security alert.
            
        Returns:
            A string describing the action taken.
        """
        return self.process_alert(alert_text)
    
    # Configuration loading methods
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
    
    def _load_protocols_config(self) -> Dict[str, Any]:
        """
        Load protocols configuration from the config file.
        
        Returns:
            Dictionary containing protocols configuration data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            protocols_path = os.path.join(base_path, '..', '..', 'config', 'protocols.json')
            
            with open(protocols_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading protocols config: {str(e)}")
            return {"protocols": []}
    
    # Helper methods for data access
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
    
    # AI interaction methods
    def prepare_context_for_ai(self) -> str:
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
    
    def _extract_parameter(self, text: str, param_name: str, default_value: str) -> str:
        """
        Extract a parameter value from text.
        
        Args:
            text: The text to extract from.
            param_name: The name of the parameter.
            default_value: The default value if the parameter is not found.
            
        Returns:
            The extracted parameter value or the default value.
        """
        # Try to find the parameter in the text
        pattern = rf'{param_name}["\s:]+([^",\s]+|"[^"]+"|\'[^\']+\')'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            value = match.group(1).strip('"\'')
            return value
            
        return default_value
    
    def _get_default_monitor_action(self) -> Tuple[str, Dict[str, Any]]:
        """
        Get the default monitoring action parameters.
        
    Returns:
            A tuple of ("monitor", default_parameters).
        """
        parameters = {
            "asset": "All Positions",
            "duration": "24h",
            "threshold": "5%"
        }
        return "monitor", parameters
    
    def try_parse_json_response(self, response_text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Attempt to parse the response as JSON with an action_plan structure.
        
        Args:
            response_text: The response from the AI.
            
        Returns:
            A tuple of (action_type, parameters) if successful, None otherwise.
        """
        try:
            response_json = json.loads(response_text)
            
            # If the response is a JSON object with an action_plan field
            if "action_plan" in response_json:
                # Handle action_plan as a list (old format)
                if isinstance(response_json["action_plan"], list):
                    if response_json["action_plan"]:
                        action = response_json["action_plan"][0]
                        action_type = action.get("action", "unknown")
                        parameters = action.get("parameters", {})
                        return self._process_action_and_parameters(action_type, parameters)
                
                # Handle action_plan as an object (new format from OpenAI responses)
                elif isinstance(response_json["action_plan"], dict):
                    action_plan = response_json["action_plan"]
                    # Get action_type from either "action" or "action_type" field
                    action_type = action_plan.get("action") or action_plan.get("action_type", "unknown")
                    parameters = action_plan.get("parameters", {})
                    return self._process_action_and_parameters(action_type, parameters)
            
            # If we got here, JSON was valid but didn't have the expected structure
            return None
        except json.JSONDecodeError:
            # Not valid JSON
            return None
            
    def _parse_text_response(self, response_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse the response as plain text, looking for keywords and extracting parameters.
        
        Args:
            response_text: The response from the AI.
            
        Returns:
            A tuple containing the action type and parameters.
        """
        response_lower = response_text.lower()
        
        # Check for withdrawal action
        if "withdraw" in response_lower or "exit" in response_lower:
            token = self._extract_parameter(response_text, "token", "unknown")
            amount = self._extract_parameter(response_text, "amount", "all")
            chain_id = self._extract_parameter(response_text, "chain_id", "1")
            
            return "withdrawal", {
                "token": token,
                "amount": amount,
                "chain_id": chain_id
            }
        
        # Check for swap action
        elif "swap" in response_lower or "convert" in response_lower or "exchange" in response_lower:
            token_in = self._extract_parameter(response_text, "token_in", "unknown")
            token_out = self._extract_parameter(response_text, "token_out", "USDC")
            amount_in = self._extract_parameter(response_text, "amount_in", "all")
            chain_id = self._extract_parameter(response_text, "chain_id", "1")
            
            return "swap", {
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": amount_in,
                "chain_id": chain_id
            }
        
        # Check for revoke action
        elif "revoke" in response_lower or "permissions" in response_lower or "approval" in response_lower:
            token = self._extract_parameter(response_text, "token", "unknown")
            token_address = self._extract_parameter(response_text, "token_address", "unknown")
            protocol = self._extract_parameter(response_text, "protocol", "unknown")
            chain_id = self._extract_parameter(response_text, "chain_id", "1")
            spender_address = self._extract_parameter(response_text, "spender_address", "")
            
            return "revoke", {
                "token": token,
                "token_address": token_address,
                "protocol": protocol,
                "chain_id": chain_id,
                "spender_address": spender_address
            }
        
        # Default to monitor action
        else:
            return self._get_default_monitor_action()
    
    def parse_ai_response(self, response_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse the AI response to determine the action to take.
        
        This method attempts to parse the response in two ways:
        1. First as a structured JSON with an action_plan field
        2. If that fails, falls back to text-based keyword parsing
        
        Args:
            response_text: The response from the AI.
            
        Returns:
            A tuple containing the action type and parameters.
        """
        logger.info("Parsing AI response")
        
        try:
            # First try to parse as JSON
            json_result = self.try_parse_json_response(response_text)
            if json_result:
                return json_result
            
            # If JSON parsing fails or doesn't match expected format, 
            # fall back to text parsing
            return self._parse_text_response(response_text)
                
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            # Default to monitoring in case of error
            return self._get_default_monitor_action()
    
    def _process_action_and_parameters(self, action_type: str, parameters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process action type and parameters to ensure they are properly formatted.
        
        Args:
            action_type: The type of action to take.
            parameters: The parameters for the action.
            
        Returns:
            A tuple of (action_type, parameters) with any necessary defaults or transformations applied.
        """
        # Normalize action type
        if action_type.lower() in ["withdraw", "withdrawal"]:
            action_type = "withdrawal"
            
            # Get wallet address from AgentKit for destination_address
            try:
                # Initialize wallet if needed
                wallet_provider, _ = self.agent_kit_manager.initialize_providers()
                wallet_address = wallet_provider.get_wallet_address()
                
                # Set destination_address from wallet
                parameters["destination_address"] = wallet_address
                logger.info(f"Using wallet address as destination: {wallet_address}")
            except Exception as e:
                logger.error(f"Failed to get wallet address from AgentKit: {str(e)}")
                # Use a fallback address if AgentKit is not available
                parameters["destination_address"] = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
                logger.warning(f"Using fallback destination address: {parameters['destination_address']}")
            
            # Handle the case where token comes from a "tokens" array
            if "tokens" in parameters and not parameters.get("token"):
                tokens = parameters.get("tokens", [])
                if tokens:
                    # If tokens is a list of strings
                    if isinstance(tokens[0], str):
                        parameters["token"] = tokens[0]
                    # If tokens is a list of dicts
                    elif isinstance(tokens[0], dict) and "token" in tokens[0]:
                        parameters["token"] = tokens[0]["token"]
                    elif isinstance(tokens[0], dict) and "token_name" in tokens[0]:
                        parameters["token"] = tokens[0]["token_name"]
            
            # Set default amount if missing
            if "amount" not in parameters:
                parameters["amount"] = "all"
            
            # Set default chain_id if missing
            if "chain_id" not in parameters:
                parameters["chain_id"] = "1"  # Default to Ethereum mainnet
                
        elif action_type.lower() in ["revoke", "revocation"]:
            action_type = "revoke"
            
            # For revoke actions, we need a valid spender_address
            # This will usually come from the protocol configuration
            if "protocol" in parameters and "spender_address" not in parameters:
                protocol = parameters.get("protocol", "").lower()
                chain_id = parameters.get("chain_id", "1")
                
                # Try to find the protocol's router address in the configuration
                try:
                    protocol_data = None
                    for p in self.protocols_config.get("protocols", []):
                        if p["name"].lower() == protocol.lower():
                            protocol_data = p
                            break
                    
                    if protocol_data and "chains" in protocol_data:
                        chain_data = protocol_data["chains"].get(chain_id, {})
                        # Look for potential spender address keys
                        potential_keys = ["router", "swapRouter", "approvalAddress"]
                        for key in potential_keys:
                            if key in chain_data:
                                parameters["spender_address"] = chain_data[key]
                                logger.info(f"Using {protocol} {key} as spender address: {parameters['spender_address']}")
                                break
                except Exception as e:
                    logger.error(f"Error finding spender address for protocol {protocol}: {str(e)}")
            
            # If we still don't have a spender_address, and there's an approval_address parameter, use that
            if "spender_address" not in parameters and "approval_address" in parameters:
                parameters["spender_address"] = parameters["approval_address"]
                
            # If we still don't have a spender_address, use a known address for the specified protocol
            if "spender_address" not in parameters and "protocol" in parameters:
                protocol = parameters.get("protocol", "").lower()
                if "uniswap" in protocol:
                    parameters["spender_address"] = "0x8D71832C0Fb9Ef50A5bf57C50fd92b2516c1D574"  # Known Uniswap router
                    logger.info(f"Using known Uniswap router as spender address: {parameters['spender_address']}")
            
        elif action_type.lower() in ["swap", "exchange", "convert"]:
            action_type = "swap"
            
            # Handle token mapping
            if "tokens" in parameters:
                tokens = parameters.get("tokens", [])
                if tokens and isinstance(tokens, list) and len(tokens) >= 2:
                    if not parameters.get("token_in"):
                        parameters["token_in"] = tokens[0]
                    if not parameters.get("token_out"):
                        parameters["token_out"] = tokens[1]
                        
        elif action_type.lower() in ["monitor", "monitoring"]:
            action_type = "monitor"
            
            # Convert "asset" or "asset_to_monitor" to standard format
            if "asset_to_monitor" in parameters and "asset" not in parameters:
                parameters["asset"] = parameters["asset_to_monitor"]
                
            # Set default duration and threshold if missing
            if "duration" not in parameters:
                parameters["duration"] = "24h"
                
            if "threshold" not in parameters:
                parameters["threshold"] = "5%"
                
        return action_type, parameters
    
    def process_alert(self, alert_text: str) -> str:
        """
        Process a security alert and take appropriate action.
        
        Args:
            alert_text: The text of the security alert.
            
        Returns:
            A string describing the action taken.
        """
        print("\n" + "="*80)
        print("\033[1;36m🔍 SECURITY ALERT DETECTED 🔍\033[0m")
        print("="*80)
        print(f"\033[1;33mAlert:\033[0m {alert_text}")
        print("-"*80)
        
        # Prepare context information for OpenAI
        logger.info("\033[1;32m[ANALYSIS]\033[0m Preparing context for AI analysis...")
        context = self.prepare_context_for_ai()
        
        # Create a system prompt
        system_prompt = """
        You are a cryptocurrency security agent tasked with protecting user funds. Analyze the security alert and 
        determine the appropriate protective action to take. Your response should include a JSON object with an 
        "action_plan" field.
        
        Available actions:
        1. withdraw - Withdraw funds from a compromised protocol or token
           Required parameters: 
            - token: The token symbol to withdraw (e.g., "ETH", "USDC")
            - amount: The amount to withdraw (e.g., "all", "1.5")
            - chain_id: The blockchain ID (e.g., "1" for Ethereum, "84532" for Base)
            
        2. revoke - Revoke token approvals for a compromised or suspicious protocol
           Required parameters:
            - token: The token symbol (e.g., "USDC")
            - protocol: The protocol to revoke from (e.g., "UniswapV3") 
            - chain_id: The blockchain ID
            
        3. monitor - Set up enhanced monitoring for a specific asset
           Required parameters:
            - asset: The asset to monitor (e.g., "ETH", "All Positions")
            - duration: Monitoring duration (e.g., "24h", "3d")
            - threshold: Alert threshold (e.g., "5%")
            
        4. swap - Swap a vulnerable token for a safer asset
           Required parameters:
            - token_in: The input token symbol (e.g., "ETH")
            - token_out: The output token symbol (e.g., "USDC")
            - amount_in: The amount to swap (e.g., "all", "1.5")
            - chain_id: The blockchain ID
        
        IMPORTANT: DO NOT provide any addresses in your response. Addresses will be handled internally by the system.
        
        Return your response in this exact format:
        {
            "action_plan": {
                "action_type": "withdraw", // or "revoke", "monitor", "swap"
                "parameters": {
                    // Include ALL required parameters for the selected action
                }
            }
        }
        """
        
        # Create a user prompt
        user_prompt = f"""
        Security Alert: {alert_text}
        
        Context Information:
        {context}
        
        Based on this alert, what protective action should be taken? Return a JSON object with 
        an "action_plan" field that specifies the action type and ALL required parameters listed in my instructions.
        """
        
        try:
            logger.info("\033[1;32m[ANALYSIS]\033[0m Sending alert to OpenAI for analysis...")
            completion = self.openai_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-3.5-turbo",
            )
            response = completion.choices[0].message.content
            logger.info("\033[1;32m[ANALYSIS]\033[0m Received response from OpenAI")
        except Exception as e:
            logger.error(f"\033[1;31m[ERROR]\033[0m Failed to get OpenAI response: {str(e)}")
            # No fallback to mock response
            response = "Error processing security alert. Please check your OpenAI API key and try again."
        
        logger.info("\033[1;32m[RESPONSE]\033[0m AI response received:")
        # Print a truncated version of the response for demo purposes
        truncated_response = response[:200] + "..." if len(response) > 200 else response
        print(f"\033[1;37m{truncated_response}\033[0m")
        print("-"*80)
        
        # Parse the response to determine the action to take
        logger.info("\033[1;32m[PROCESSING]\033[0m Parsing AI response to determine action...")
        action, parameters = self.parse_ai_response(response)
        
        logger.info(f"\033[1;32m[ACTION]\033[0m Determined action: \033[1;36m{action.upper()}\033[0m")
        logger.info(f"\033[1;32m[PARAMETERS]\033[0m Action parameters: {parameters}")
        
        # Execute the appropriate action
        result = "No action taken."
        
        if action == "withdraw" or action == "withdrawal":
            print(f"\033[1;34m🔒 EXECUTING WITHDRAWAL ACTION 🔒\033[0m")
            result = self.withdrawal_tool(parameters)
        elif action == "revoke":
            print(f"\033[1;34m🔒 EXECUTING REVOCATION ACTION 🔒\033[0m")
            result = self.revoke_tool(parameters)
        elif action == "monitor":
            print(f"\033[1;34m🔎 EXECUTING MONITORING ACTION 🔎\033[0m")
            result = self.monitor_tool(parameters)
        elif action == "swap":
            print(f"\033[1;34m🔄 EXECUTING SWAP ACTION 🔄\033[0m")
            result = self.swap_tool(parameters)
        else:
            logger.warning(f"\033[1;33m[WARNING]\033[0m Unknown action: {action}")
            print(f"\033[1;33m⚠️ UNKNOWN ACTION: {action} ⚠️\033[0m")
        
        print("-"*80)
        print(f"\033[1;32m✅ RESULT:\033[0m {result}")
        print("="*80 + "\n")
        
        return result
    
    # Compatibility methods for backward compatibility
    def process_security_alert(self, alert_text: str) -> str:
        """Alias for process_alert for backward compatibility."""
        return self.process_alert(alert_text)
    
    def _prepare_context_for_ai(self) -> str:
        """Alias for prepare_context_for_ai for backward compatibility."""
        return self.prepare_context_for_ai()
    
    def _parse_ai_response(self, response_text: str) -> Tuple[str, Dict[str, Any]]:
        """Alias for parse_ai_response for backward compatibility."""
        return self.parse_ai_response(response_text)
    
    def _try_parse_json_response(self, response_text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Alias for try_parse_json_response for backward compatibility."""
        return self.try_parse_json_response(response_text)

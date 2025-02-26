"""
Security agent for the Horus security monitoring system.
"""
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class SecurityAgent:
    """Security agent for processing security alerts and taking actions."""
    
    def __init__(self, openai_client):
        """Initialize the security agent with an OpenAI client."""
        self.openai_client = openai_client
    
    def process_security_alert(self, alert_text: str) -> str:
        """
        Process a security alert and determine the appropriate action to take.
        
        Args:
            alert_text: The text of the security alert.
            
        Returns:
            A string describing the action taken.
        """
        try:
            # Analyze the security alert with OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Horus, a security monitoring agent for cryptocurrency wallets and DeFi protocols.
                        Your task is to analyze security alerts and determine the appropriate action to take to protect user funds.
                        You should respond with a JSON object containing:
                        1. "reasoning": Your analysis of the security alert and why you're taking the action
                        2. "action_plan": An array of actions to take, each with:
                           - "action": The type of action (e.g., "withdrawal", "revoke", "monitor")
                           - "explanation": A brief explanation of the action
                           - "parameters": The parameters for the action (e.g., token, amount, destination)
                        
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
                    
                    logger.info(f"WITHDRAWAL TOOL CALLED: Withdrawing {amount} {token} to {destination}")
                    result.append(f"Emergency withdrawal initiated: {amount} {token} to {destination}.")
                
                elif action_type == "revoke":
                    token_address = parameters.get("token_address", "unknown")
                    protocol = parameters.get("protocol", "unknown")
                    
                    logger.info(f"REVOKE TOOL CALLED: Revoking permissions for {token_address} on {protocol}")
                    result.append(f"Permissions revoked for {token_address} on {protocol}.")
                
                elif action_type == "monitor":
                    asset = parameters.get("asset", "unknown")
                    duration = parameters.get("duration", "24h")
                    
                    logger.info(f"MONITOR TOOL CALLED: Monitoring {asset} for {duration}")
                    result.append(f"Enhanced monitoring enabled for {asset} for the next {duration}.")
                
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    result.append(f"Unknown action: {action_type}")
            
            # Return the result
            return "Horus Response:\n" + "\n".join(result)
        
        except Exception as e:
            logger.error(f"Error processing security alert: {str(e)}")
            return f"Error processing security alert: {str(e)}"

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

def setup_agent():
    """Set up the Horus security monitoring agent with Coinbase Agent Kit."""
    
    # Check for required environment variables
    required_env_vars = ["CDP_API_KEY_NAME", "CDP_API_KEY_PRIVATE_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in a .env file or in your environment.")
        return None
    
    try:
        # Import Coinbase Agent Kit modules
        from coinbase_agentkit import AgentKit

        # Initialize OpenAI client
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize AgentKit
        agent_kit = AgentKit()
        
        return {
            "agent_kit": agent_kit,
            "openai_client": openai_client
        }
    except ImportError as e:
        print(f"Error importing required modules: {str(e)}")
        print("Please make sure all required packages are installed.")
        return None
    except Exception as e:
        print(f"Error setting up agent: {str(e)}")
        return None

def revoke_tool(agent_kit, token_address=None, protocol=None):
    """
    Tool to revoke permissions for a token or protocol.
    
    This would revoke approvals for a specific token or all approvals for a protocol.
    """
    print(f"REVOKE TOOL CALLED: Revoking permissions for token: {token_address}, protocol: {protocol}")
    
    # In a real implementation, this would use agent_kit to:
    # 1. Get the wallet
    # 2. Find the relevant approvals
    # 3. Send transactions to revoke them
    
    # For now, just simulate the action
    return f"Permission revocation initiated for {'token ' + token_address if token_address else 'protocol ' + protocol if protocol else 'all permissions'}."

def swap_tool(agent_kit, from_token=None, to_token=None, amount=None):
    """
    Tool to swap tokens in response to a security threat.
    
    This would swap one token for another to protect funds from a compromised contract.
    """
    print(f"SWAP TOOL CALLED: Swapping {amount} {from_token} to {to_token}")
    
    # In a real implementation, this would use agent_kit to:
    # 1. Get the wallet
    # 2. Check balances
    # 3. Execute a swap transaction
    
    # For now, just simulate the action
    return f"Emergency swap initiated: {amount} {from_token} to {to_token}."

def withdrawal_tool(agent_kit, token=None, amount=None, destination=None):
    """
    Tool to withdraw funds from a potentially compromised protocol.
    
    This would withdraw funds to a safe wallet address.
    """
    print(f"WITHDRAWAL TOOL CALLED: Withdrawing {amount} {token} to {destination}")
    
    # In a real implementation, this would use agent_kit to:
    # 1. Get the wallet
    # 2. Execute a withdrawal transaction
    
    # For now, just simulate the action
    return f"Emergency withdrawal initiated: {amount} {token} to {destination}."

def process_security_alert(alert_message, agent_data):
    """
    Process a security alert and determine the appropriate action.
    
    This function analyzes a security alert and decides whether to revoke permissions,
    swap tokens, or withdraw funds based on the nature of the threat.
    """
    agent_kit = agent_data["agent_kit"]
    openai_client = agent_data["openai_client"]
    
    # Use OpenAI to analyze the security alert and determine the best action
    system_message = """You are Horus, a security monitoring agent for cryptocurrency wallets.
    Your job is to protect users' funds by taking appropriate actions when security threats are detected.
    
    Based on the security alert, determine which action to take:
    1. revoke - Revoke permissions for a token or protocol that has been compromised
    2. swap - Swap vulnerable tokens for safer ones (e.g., swap a compromised token for ETH)
    3. withdrawal - Withdraw funds from a compromised protocol to a safe address
    4. none - If no immediate action is needed or if the alert doesn't contain enough information
    
    Return a JSON object with the following structure:
    {
        "action": "action_name",
        "reasoning": "explanation of why this action is appropriate",
        "parameters": {
            // For revoke:
            "token_address": "address of the token to revoke (optional)",
            "protocol": "name of the protocol (optional)",
            
            // For swap:
            "from_token": "token to swap from",
            "to_token": "token to swap to",
            "amount": "amount to swap (can be 'all')",
            
            // For withdrawal:
            "token": "token to withdraw",
            "amount": "amount to withdraw (can be 'all')",
            "destination": "address to withdraw to"
        }
    }
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": alert_message}
            ],
            response_format={"type": "json_object"}
        )
        
        decision = json.loads(response.choices[0].message.content)
        action = decision.get("action", "none")
        reasoning = decision.get("reasoning", "No reasoning provided")
        parameters = decision.get("parameters", {})
        
        print(f"Determined action: {action}")
        print(f"Reasoning: {reasoning}")
        
        # Execute the appropriate action
        if action == "revoke":
            token_address = parameters.get("token_address")
            protocol = parameters.get("protocol")
            return revoke_tool(agent_kit, token_address, protocol)
            
        elif action == "swap":
            from_token = parameters.get("from_token")
            to_token = parameters.get("to_token")
            amount = parameters.get("amount")
            return swap_tool(agent_kit, from_token, to_token, amount)
            
        elif action == "withdrawal":
            token = parameters.get("token")
            amount = parameters.get("amount")
            destination = parameters.get("destination")
            return withdrawal_tool(agent_kit, token, amount, destination)
            
        else:
            return "No immediate action taken. Continuing to monitor the situation."
    
    except Exception as e:
        return f"Error processing security alert: {str(e)}"

def main():
    """Main function to run the Horus security monitoring agent."""
    print("Welcome to Horus - Crypto Security Monitoring Agent!")
    
    # Set up the agent
    agent_data = setup_agent()
    
    if not agent_data:
        print("Failed to set up the agent. Exiting.")
        return
    
    print("Agent is ready. You can start sending security alerts.")
    print("Available actions: revoke, swap, withdrawal")
    print("Type 'exit' to quit.")
    
    # Simple chat loop
    while True:
        alert_message = input("\nSecurity Alert: ")
        
        if alert_message.lower() == 'exit':
            print("Shutting down security monitoring.")
            break
        
        try:
            response = process_security_alert(alert_message, agent_data)
            print(f"\nHorus Response: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()

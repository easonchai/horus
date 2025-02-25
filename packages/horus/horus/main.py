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

def execute_action(agent_kit, action):
    """
    Execute a single action based on its type and parameters.
    
    Args:
        agent_kit: The AgentKit instance
        action: A dictionary containing the action type and parameters
        
    Returns:
        The result of the action execution
    """
    action_type = action.get("action")
    parameters = action.get("parameters", {})
    
    if action_type == "revoke":
        return revoke_tool(
            agent_kit, 
            token_address=parameters.get("token_address"),
            protocol=parameters.get("protocol")
        )
    elif action_type == "swap":
        return swap_tool(
            agent_kit,
            from_token=parameters.get("from_token"),
            to_token=parameters.get("to_token"),
            amount=parameters.get("amount")
        )
    elif action_type == "withdrawal":
        return withdrawal_tool(
            agent_kit,
            token=parameters.get("token"),
            amount=parameters.get("amount"),
            destination=parameters.get("destination")
        )
    else:
        return f"Unknown action type: {action_type}"

def process_security_alert(alert_message, agent_data):
    """
    Process a security alert and determine the appropriate action plan.
    
    This function analyzes a security alert and decides on a sequence of actions
    to take (revoke permissions, swap tokens, withdraw funds) based on the nature
    of the threat.
    """
    agent_kit = agent_data["agent_kit"]
    openai_client = agent_data["openai_client"]
    
    # Use OpenAI to analyze the security alert and determine the best action plan
    system_message = """You are Horus, a security monitoring agent for cryptocurrency wallets.
    Your job is to protect users' funds by taking appropriate actions when security threats are detected.
    
    Based on the security alert, determine a sequence of actions to take. You can use the following tools:
    1. revoke - Revoke permissions for a token or protocol that has been compromised
    2. swap - Swap vulnerable tokens for safer ones (e.g., swap a compromised token for ETH)
    3. withdrawal - Withdraw funds from a compromised protocol to a safe address
    
    You can use these tools in any order, and you can use multiple tools if needed.
    For example, you might need to withdraw funds from a compromised protocol and then swap them to a safer asset.
    
    IMPORTANT: You MUST respond with a valid JSON object using the following structure:
    {
        "reasoning": "explanation of your analysis and why these actions are appropriate",
        "action_plan": [
            {
                "action": "action_name",
                "explanation": "why this specific action is needed",
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
            },
            // Additional actions in the sequence...
        ]
    }
    
    If no action is needed, return an empty action_plan array.
    
    DO NOT include any text outside of the JSON object. Your entire response must be valid JSON.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": alert_message}
            ]
        )
        
        # Parse the response content as JSON
        try:
            decision = json.loads(response.choices[0].message.content)
            reasoning = decision.get("reasoning", "No reasoning provided")
            action_plan = decision.get("action_plan", [])
        except json.JSONDecodeError:
            # If the response is not valid JSON, extract what we can
            content = response.choices[0].message.content
            print(f"Warning: Could not parse response as JSON. Raw response: {content}")
            return "Error: Could not parse AI response as JSON. Please try again."
        
        print(f"Reasoning: {reasoning}")
        print(f"Action plan contains {len(action_plan)} steps")
        
        if not action_plan:
            return "No immediate action taken. Continuing to monitor the situation."
        
        # Execute each action in the plan
        results = []
        for i, action in enumerate(action_plan):
            print(f"Executing step {i+1}: {action.get('action')}")
            print(f"Explanation: {action.get('explanation', 'No explanation provided')}")
            
            try:
                result = execute_action(agent_kit, action)
                results.append(result)
            except Exception as e:
                error_message = f"Error executing {action.get('action')}: {str(e)}"
                print(error_message)
                results.append(error_message)
        
        # Combine the results
        return "\n".join(results)
    
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

def test_multi_action_scenario():
    """
    Test function to demonstrate the agent handling a complex security scenario
    that requires multiple actions in sequence.
    """
    print("Running test for multi-action security scenario...")
    
    # Set up the agent
    agent_data = setup_agent()
    
    if not agent_data:
        print("Failed to set up the agent. Exiting test.")
        return
    
    # Test scenario that requires multiple actions
    test_alert = """
    URGENT SECURITY ALERT: We've detected a critical vulnerability in the Uniswap V3 protocol 
    affecting the USDC/ETH pool. The vulnerability allows attackers to drain funds from liquidity 
    providers. We've already seen multiple wallets being exploited. Your wallet has $50,000 USDC 
    in this pool that needs to be secured immediately. After withdrawing, you should convert to 
    a safer asset until the vulnerability is patched.
    
    Your safe wallet address is: 0x1234567890abcdef1234567890abcdef12345678
    """
    
    print("\nTest Security Alert:", test_alert)
    
    try:
        response = process_security_alert(test_alert, agent_data)
        print("\nHorus Response:", response)
    except Exception as e:
        print(f"\nError during test: {str(e)}")

if __name__ == "__main__":
    # Comment out the direct function calls
    # test_multi_action_scenario()
    # main()

    # Use command line arguments to choose the mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_multi_action_scenario()
    else:
        main()

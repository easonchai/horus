import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

def setup_agent():
    """Set up the Coinbase Agent Kit."""
    
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
        
        # Return the agent kit and OpenAI client
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

def get_wallet_details(agent_kit):
    """Get details about the MPC Wallet."""
    try:
        wallet = agent_kit.get_wallet()
        return {
            "address": wallet.address,
            "network": agent_kit.network_id
        }
    except Exception as e:
        return {"error": str(e)}

def get_balance(agent_kit, asset=None):
    """Get balance for specific assets."""
    try:
        wallet = agent_kit.get_wallet()
        balances = wallet.get_balances()
        
        if asset:
            for balance in balances:
                if balance.symbol.lower() == asset.lower():
                    return {
                        "asset": balance.symbol,
                        "balance": balance.amount,
                        "usd_value": balance.usd_value
                    }
            return {"error": f"Asset {asset} not found"}
        
        return [{
            "asset": balance.symbol,
            "balance": balance.amount,
            "usd_value": balance.usd_value
        } for balance in balances]
    except Exception as e:
        return {"error": str(e)}

def process_user_input(user_input, agent_data):
    """Process user input and return a response."""
    agent_kit = agent_data["agent_kit"]
    openai_client = agent_data["openai_client"]
    
    # Use OpenAI to determine the user's intent
    system_message = """You are a helpful assistant that can interact with the Coinbase Developer Platform.
    You can help users manage their crypto wallets, check balances, and perform transactions.
    Based on the user's input, determine which action they want to perform:
    1. get_wallet_details - Get details about the MPC Wallet
    2. get_balance - Get balance for specific assets (optionally specify an asset)
    3. general_question - Answer a general question about cryptocurrency
    
    Return a JSON object with the following structure:
    {
        "action": "action_name",
        "parameters": {
            "param1": "value1",
            "param2": "value2"
        }
    }
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"}
        )
        
        intent = json.loads(response.choices[0].message.content)
        
        # Execute the appropriate action
        if intent["action"] == "get_wallet_details":
            result = get_wallet_details(agent_kit)
            return f"Wallet details:\nAddress: {result['address']}\nNetwork: {result['network']}"
        
        elif intent["action"] == "get_balance":
            asset = intent.get("parameters", {}).get("asset")
            result = get_balance(agent_kit, asset)
            
            if isinstance(result, list):
                response_text = "Your wallet balances:\n"
                for balance in result:
                    response_text += f"{balance['asset']}: {balance['balance']} (${balance['usd_value']})\n"
                return response_text
            elif "error" in result:
                return f"Error: {result['error']}"
            else:
                return f"Balance for {result['asset']}: {result['balance']} (${result['usd_value']})"
        
        elif intent["action"] == "general_question":
            # Use OpenAI to answer general questions
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant with expertise in cryptocurrency."},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content
        
        else:
            return "I'm not sure how to help with that. You can ask about your wallet details, check balances, or ask general questions about cryptocurrency."
    
    except Exception as e:
        return f"Error processing your request: {str(e)}"

def main():
    """Main function to run the Horus application with Coinbase Agent Kit."""
    print("Welcome to Horus with Coinbase Agent Kit!")
    
    # Set up the agent
    agent_data = setup_agent()
    
    if not agent_data:
        print("Failed to set up the agent. Exiting.")
        return
    
    print("Agent is ready. You can start interacting with it.")
    print("Type 'exit' to quit.")
    
    # Simple chat loop
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        try:
            response = process_user_input(user_input, agent_data)
            print(f"\nHorus: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()

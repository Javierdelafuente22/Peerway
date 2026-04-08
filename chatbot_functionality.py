import json
from chatbot_API import EnergyChatbot
from chatbot_data import apply_lifestyle_update, get_plot_window, plot_demand_comparison

def main():
    # Initialize the class from our API file
    agent = EnergyChatbot()

    print("Chat to your Energy Agent")

    while True:
        user_text = input()
        
        # Request data from the API class
        result = agent.get_chat_response(user_text)

        # Handle API or Logic errors
        if result.get("category") == "Error":
            print(f"{result.get('mission_check')}")
            continue

        # Confirmation Step (Mission Check)
        print(f"\n{result.get('mission_check')} [Yes/No]")
        choice = input("> ").strip().lower()

        if choice in ['y', 'yes']:
            # Prepare clean data for the simulation backend
            payload = {k: v for k, v in result.items() if k != "mission_check"}
            print("\nChanges have been made")
            print(json.dumps(payload, indent=2))

            # 1. Update the Data
            modified_df = apply_lifestyle_update(json_payload=payload)
            
            if modified_df is not None:
                # 2. Extract the specific window to plot
                plot_data = get_plot_window(modified_df, payload)
                
                # 3. Show the graph!
                plot_demand_comparison(plot_data, payload['category'])

        else:
            print("\nCancelled. No changes were made.")

        # Reset line
        print("\n" + "="*50)
        print("Ready for your next request...")
        print("="*50 + "\n")

if __name__ == "__main__":
    main()
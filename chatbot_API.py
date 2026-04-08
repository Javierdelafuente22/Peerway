import json
import os
from dotenv import load_dotenv
from google import genai 

# Load environment variables from the .env file
load_dotenv()

class EnergyChatbot:
    def __init__(self, prompt_path="chatbot_instructions.txt"):
        """
        Initializes the chatbot by loading the secure API key, setting up the 
        Gemini client, and reading the baseline system instructions.
        """
        # Retrieve the API key securely from the environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API Key not found! Ensure it is in your .env file.")
            
        # Initialize the Google GenAI client
        self.client = genai.Client(api_key=api_key)
        
        # Load the system instructions from the external text file
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Missing {prompt_path} file!")
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_instructions = f.read()

    def get_instruction(self, user_input):
        """
        Takes a natural language input from the user, processes it through the LLM, 
        and returns a structured JSON object for the simulation backend.
        """
        # Combine the strict system rules with the specific user request
        full_prompt = f"{self.system_instructions}\n\nInput: \"{user_input}\""
        
        try:
            # Send the prompt to the Gemini model
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt
            )
            
            # Strip out any markdown formatting the model might add (like ```json ... ```)
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            
            # Convert the clean string back into a Python dictionary
            return json.loads(clean_text)
            
        except Exception as e:
            # Provide a fallback error dictionary if parsing fails or the API limits out
            raw_res = getattr(response, 'text', "No response generated") if 'response' in locals() else "N/A"
            return {"error": f"Failed to parse: {str(e)}", "raw_response": raw_res}

# --- Execution Block ---
if __name__ == "__main__":
    """
    Test block to verify the chatbot correctly parses a known input.
    This will only run if the script is executed directly.
    """
    chatbot = EnergyChatbot()

    # Test Case: Worker Status
    test_input = "I'm working from home every Monday and Wednesday"
    print(f"Testing input: {test_input}")
    
    # Process the text and print the resulting JSON nicely formatted
    result = chatbot.get_instruction(test_input)
    print(json.dumps(result, indent=2))
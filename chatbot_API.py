import google.generativeai as genai
import json
import os

class EnergyChatbot:
    def __init__(self, api_key, prompt_path="chatbot_instructions.txt"):
        # Setup API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load your system prompt
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_instructions = f.read()

    def get_instruction(self, user_input):
        # Combine the system instructions with the user's specific request
        full_prompt = f"{self.system_instructions}\n\nInput: \"{user_input}\""
        
        try:
            response = self.model.generate_content(full_prompt)
            # Remove any markdown code blocks (```json ... ```) if the model adds them
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
        except Exception as e:
            return {"error": f"Failed to parse: {str(e)}", "raw_response": response.text}

# --- Execution Block ---
if __name__ == "__main__":
    # Replace with your actual Gemini API Key
    YOUR_API_KEY = "PASTE_YOUR_API_KEY_HERE"
    
    chatbot = EnergyChatbot(api_key=YOUR_API_KEY)

    # Test Case: Worker Status
    test_input = "I'm working from home every Monday and Wednesday"
    print(f"Testing input: {test_input}")
    
    result = chatbot.get_instruction(test_input)
    print(json.dumps(result, indent=2))
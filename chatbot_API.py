import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class EnergyChatbot:
    def __init__(self, prompt_path="chatbot_instructions.txt"):
        """
        Sets up the API client and loads the static instructions.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API Key missing from .env")
        
        self.client = genai.Client(api_key=api_key)
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_instructions = f.read()

    def get_chat_response(self, user_input):
        """
        Fetches intent from the LLM. No retries, direct error messages.
        """
        full_prompt = f"{self.system_instructions}\n\nUser Input: \"{user_input}\""
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash-lite', 
                contents=full_prompt
            )
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
            
        except Exception as e:
            error_msg = str(e).lower()
            # Map Gemini specific codes to user-friendly explanations
            if "429" in error_msg:
                msg = "Too many requests have been sent. Please retry in a few minutes."
            elif "503" in error_msg or "unavailable" in error_msg:
                msg = "Servers are busy, try again in a few minutes. Sorry for the inconvenience."
            else:
                msg = "An issue has been encountered. Please retry in a few minutes."
            
            return {"category": "Error", "mission_check": msg}
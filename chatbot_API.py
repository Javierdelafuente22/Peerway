import google.generativeai as genai
import json

class EnergyIntentParser:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def get_json_instruction(self, user_prompt):
        # We define the context and examples here
        system_context = """
        CONTEXT:
You are the Chatbot for a Peer-to-Peer Energy Trading App. 
Users interact with you to update their lifestyle settings, which modifies 
their "Net Demand" data in our 2024-2025 simulation dataset.

RULES OF ENGAGEMENT:
1. Current Date: Monday, 01/01/2024.
2. Formats: Timestamps must be "DD/MM/YYYY HH:MM:SS". Days_of_week: [0=Mon, 6=Sun].
3. Logic: 
   - EV: type='scale', value=1.5, repeat='daily'.
   - Vacation: type='fixed', value=0.1, repeat='once'.
   - Worker (At Office): type='fixed', value=0.1, repeat='weekly'.
   - Worker (At Home): type='scale', value=1.5, repeat='weekly'.

---
EXAMPLES:

Input: "I'm going to Italy from Jan 10th to Jan 20th"
Output: {
  "category": "Vacation",
  "modification": {"type": "fixed", "value": 0.1},
  "timing": {"repeat": "once", "days_of_week": [0,1,2,3,4,5,6], "start_timestamp": "10/01/2024 00:00:00", "end_timestamp": "20/01/2024 23:59:59"}
}

Input: "I'll be working at the office every Tuesday and Friday"
Output: {
  "category": "Worker",
  "modification": {"type": "fixed", "value": 0.1},
  "timing": {"repeat": "weekly", "days_of_week": [1, 4], "start_timestamp": "01/01/2024 09:00:00", "end_timestamp": "31/12/2024 17:00:00"}
}

Input: "I just got an EV and will charge it every night"
Output: {
  "category": "EV",
  "modification": {"type": "scale", "value": 1.5},
  "timing": {"repeat": "daily", "days_of_week": [0,1,2,3,4,5,6], "start_timestamp": "01/01/2024 22:00:00", "end_timestamp": "31/12/2024 06:00:00"}
}
---
IMPORTANT: Return ONLY the JSON object. No conversational filler.
        """
        
        # Combine context with the actual user input
        full_query = f"{system_context}\n\nUser Input: {user_prompt}"
        
        try:
            response = self.model.generate_content(full_query)
            # Clean and parse
            clean_json = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(clean_json)
        except Exception as e:
            return {"error": f"Failed to parse: {str(e)}"}

# --- Isolated Testing ---
# parser = EnergyIntentParser(api_key="YOUR_KEY")
# result = parser.get_json_instruction("I'm working from home on Mondays and Wednesdays")
# print(json.dumps(result, indent=2))
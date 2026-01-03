import google.generativeai as genai
import os
import json
import logging

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self):
        self.api_key = os.getenv("GENAI_KEY")
        if not self.api_key:
            logger.warning("GENAI_KEY not found. Agent will not function correctly.")
            return
        
        genai.configure(api_key=self.api_key)
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Fallback to listing models to debug
            for m in genai.list_models():
                logger.info(f"Available model: {m.name}")
            raise e

    async def analyze_message(self, message_text: str, sender_info: str) -> dict:
        """
        Analyzes a message to determine importance and generate a summary.
        Returns a dictionary: { "priority": int (0-10), "summary": str, "action_required": bool }
        """
        if not self.api_key:
            return {"priority": 0, "summary": "No API Key", "action_required": False}

        prompt = f"""
        You are a personal assistant. Analyze the following Telegram message.
        
        Sender: {sender_info}
        Message: "{message_text}"
        
        Task:
        1. Rate urgency/importance from 0 to 10 (10 is critical emergency, 0 is spam).
        2. Summarize the content in one brief sentence.
        3. Decide if I need to reply or take action (True/False).
        4. Extract a deadline if present (e.g., "by 5pm", "tomorrow", "Friday"). Return null if no deadline.
        
        Output JSON only:
        {{
            "priority": <int>,
            "summary": "<string>",
            "action_required": <bool>,
            "deadline": "<string or null>"
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return {"priority": 0, "summary": "Analysis failed", "action_required": False}

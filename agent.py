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
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Fallback to listing models to debug
            for m in genai.list_models():
                logger.info(f"Available model: {m.name}")
            raise e

    async def analyze_message(self, message_text: str, sender_info: str, memory_text: str = "") -> dict:
        """
        Analyzes a message to determine importance and generate a summary.
        Returns a dictionary: { "priority": int (0-10), "summary": str, "action_required": bool }
        """
        if not self.api_key:
            return {"priority": 0, "summary": "No API Key", "action_required": False}

        # Load Prompt from File for easy management
        try:
            from jinja2 import Template
            with open("system_prompt.txt", "r") as f:
                template_str = f.read()
                template = Template(template_str)
                prompt = template.render(memory_text=memory_text, message_text=message_text)
        except Exception as e:
            logger.error(f"Failed to load system_prompt.txt: {e}")
            # Fallback (Generic)
            prompt = f"Analyze this chat: {message_text}. Memory: {memory_text}. Json output."
        
        try:
            response = await self.model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return {"priority": 0, "summary": "Analysis failed", "action_required": False}

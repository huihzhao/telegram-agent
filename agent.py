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

        prompt = f"""
        You are a personal assistant. Analyze the following Chat History.
        
        Recent Finished Tasks (Memory):
        {memory_text}
        
        Chat Context:
        {message_text}
        
        Task:
        1. Context: The last message in the history is the "Trigger".
        Task:
        1. Context: The last message in the history is the "Trigger".
        2. Memory Check:
           - DUPLICATES: If asking for the EXACT same thing as "Recent Finished Tasks" -> Priority 0, Action False.
           - LEARNING (Topics):
             - If the request is similar to "REJECTED Tasks" -> Priority 0, Action False.
             - If the request matches patterns in "ACCEPTED Tasks" -> High Priority.
           - LEARNING (People):
             - Check if the SENDER has a history of Rejected tasks in "REJECTED Tasks". If yes, be skeptical -> Priority < 5.
             - If SENDER is typically Accepted, trust them more.
        3. Relevance: Is this conversation directing a task, question, or important information specifically to ME (the owner)?
           - If it's a general group chat noise, greetings ("hi", "hello"), or irrelevant chatter -> Priority 0, Action False.
           - If it's a specific request, deadline, or urgent info for me -> High Priority.
        4. Rate urgency/importance from 0 to 10 (10 is critical, 0 is noise).
        3. Relevance: Is this conversation directing a task, question, or important information specifically to ME (the owner)?
           - If it's a general group chat noise, greetings ("hi", "hello"), or irrelevant chatter -> Priority 0, Action False.
           - If it's a specific request, deadline, or urgent info for me -> High Priority.
        4. Rate urgency/importance from 0 to 10 (10 is critical, 0 is noise).
        4. Summarize the request in one sentence.
        5. Decide if action is required (True/False). Mark "False" for noise.
        6. Extract deadline if present.
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

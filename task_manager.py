from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        # List of dictionaries: { "id": str, "priority": int, "summary": str, "sender": str, "link": str, "time": str }
        self.tasks = []

    def add_task(self, priority: int, summary: str, sender: str, link: str, deadline: str = None):
        """Adds a new task to the list and sorts by priority."""
        logger.info(f"Adding task: {summary}")
        task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
        new_task = {
            "id": task_id,
            "priority": priority,
            "summary": summary,
            "sender": sender,
            "link": link,
            "deadline": deadline,
            "time": datetime.now().strftime("%I:%M %p")
        }
        self.tasks.append(new_task)
        # Sort by priority (descending)
        self.tasks.sort(key=lambda x: x["priority"], reverse=True)
        return new_task

    def remove_task(self, task_id: str):
        """Removes a task by ID."""
        logger.info(f"Removing task: {task_id}")
        self.tasks = [t for t in self.tasks if t["id"] != task_id]

    # Web Dashboard handles rendering now
    def get_tasks(self):
        return self.tasks

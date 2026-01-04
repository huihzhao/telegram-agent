from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)

import json
import os

class TaskManager:
    def __init__(self, storage_file="tasks.json"):
        self.storage_file = storage_file
        # List of dictionaries: { "id": str, "priority": int, "summary": str, "sender": str, "link": str, "time": str }
        self.tasks = self.load_tasks()

    def load_tasks(self):
        """Loads tasks from the JSON file."""
        if not os.path.exists(self.storage_file):
            return []
        try:
            with open(self.storage_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            return []

    def save_tasks(self):
        """Saves current tasks to the JSON file."""
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self.tasks, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

    def add_task(self, priority: int, summary: str, sender: str, link: str, deadline: str = None, user_id: int = None):
        """Adds a new task to the list and sorts by priority."""
        logger.info(f"Adding task: {summary}")
        task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
        new_task = {
            "id": task_id,
            "priority": priority,
            "summary": summary,
            "sender": sender,
            "user_id": user_id,
            "link": link,
            "deadline": deadline,
            "status": "active",
            "time": datetime.now().strftime("%I:%M %p")
        }
        self.tasks.append(new_task)
        # Sort by priority (descending)
        self.tasks.sort(key=lambda x: x["priority"], reverse=True)
        self.save_tasks()
        return new_task

    def mark_done(self, task_id: str):
        """Marks a task as done instead of removing it."""
        logger.info(f"Marking task done: {task_id}")
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "done"
                break
        self.save_tasks()

    def reject_task(self, task_id: str):
        """Marks a task as rejected."""
        logger.info(f"Marking task rejected: {task_id}")
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "rejected"
                break
        self.save_tasks()

    def reopen_task(self, task_id: str):
        """Marks a task as active again."""
        logger.info(f"Reopening task: {task_id}")
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "active"
                break
        self.save_tasks()

    def remove_task(self, task_id: str):
         # Kept for compatibility but redirects to mark_done per user request
         self.mark_done(task_id)

    # Web Dashboard handles rendering now
    def get_tasks(self):
        return self.tasks

    def get_recent_done_tasks(self, limit: int = 5):
        """Returns the most recently completed tasks."""
        done_tasks = [t for t in self.tasks if t.get("status") == "done"]
        return done_tasks[-limit:]

    def get_preference_examples(self, limit: int = 5):
        """Returns lists of recent accepted vs rejected tasks for AI learning."""
        # Return dicts with summary and sender
        accepted = [{"summary": t['summary'], "sender": t.get("sender", "Unknown")} for t in self.tasks if t.get("status") == "done"][-limit:]
        rejected = [{"summary": t['summary'], "sender": t.get("sender", "Unknown")} for t in self.tasks if t.get("status") == "rejected"][-limit:]
        return {
            "accepted": accepted,
            "rejected": rejected
        }

from datetime import datetime
import logging
from notion_sync import NotionSync

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, storage_file="tasks.json"):
        # Storage file argument kept for compatibility but ignored
        self.notion_sync = NotionSync()
        
    async def add_task(self, priority: int, summary: str, sender: str, link: str, deadline: str = None, user_id: int = None):
        """Adds a new task directly to Notion."""
        logger.info(f"Adding task to Notion: {summary}")
        
        task_data = {
            "summary": summary,
            "priority": priority,
            "sender": sender,
            "link": link,
            "status": "active",
            "deadline": deadline # NotionSync needs to handle this if property exists
        }
        
        # Check if task already exists (Deduplication)
        if link:
            existing_id = await self.notion_sync.find_task_by_link(link)
            if existing_id:
                logger.info(f"Task already exists in Notion (ID: {existing_id}). Skipping addition.")
                return {
                    "id": existing_id,
                    "summary": summary,
                    "priority": priority,
                    "status": "active", # Assuming active if it exists, or whatever it is
                    "is_new": False
                }

        page_id = await self.notion_sync.create_task_page(task_data)
        
        # Return a mock task object for immediate UI feedback if needed, 
        # though the dashboard should re-fetch.
        return {
            "id": page_id,
            "summary": summary,
            "priority": priority,
            "status": "active",
            "is_new": True
        }

    async def mark_done(self, task_id: str):
        """Updates Notion status to Done."""
        logger.info(f"Marking task done: {task_id}")
        await self.notion_sync.update_task_status(task_id, 'done')

    async def reject_task(self, task_id: str):
        """Updates Notion status to Rejected."""
        logger.info(f"Marking task rejected: {task_id}")
        await self.notion_sync.update_task_status(task_id, 'rejected')

    async def reopen_task(self, task_id: str):
        """Updates Notion status to Active."""
        logger.info(f"Reopening task: {task_id}")
        await self.notion_sync.update_task_status(task_id, 'active')

    async def get_tasks(self):
        """Fetches tasks directly from Notion."""
        return await self.notion_sync.get_tasks()

    async def get_recent_done_tasks(self, limit: int = 5):
        """Returns most recently completed tasks from Notion."""
        all_tasks = await self.get_tasks()
        done_tasks = [t for t in all_tasks if t.get("status") == "done"]
        # Notion returns unsorted or sorted by priority? We requested sort by priority.
        # Ideally we sort by updated time but for now just slice.
        return done_tasks[:limit]

    async def get_preference_examples(self, limit: int = 5):
        """Returns lists of recent accepted vs rejected tasks for AI learning."""
        all_tasks = await self.get_tasks()
        accepted = [{"summary": t['summary'], "sender": t.get("sender", "Unknown")} for t in all_tasks if t.get("status") == "done"][:limit]
        rejected = [{"summary": t['summary'], "sender": t.get("sender", "Unknown")} for t in all_tasks if t.get("status") == "rejected"][:limit]
        return {
            "accepted": accepted,
            "rejected": rejected
        }


    async def get_daily_briefing_tasks(self):
        """Returns top priority tasks for daily digest."""
        all_tasks = await self.get_tasks()
        active_tasks = [t for t in all_tasks if t.get("status") == "active"]
        
        # Already sorted by priority in Notion query, but let's ensure
        sorted_tasks = sorted(active_tasks, key=lambda x: x.get("priority", 0), reverse=True)
        top_tasks = sorted_tasks[:3]
        
        # TODO: Implement proper deadline parsing later
        deadline_tasks = [t for t in active_tasks if t.get("deadline")]
        
        return {
            "top_tasks": top_tasks,
            "deadline_tasks": deadline_tasks
        }

    async def add_comment(self, task_id, text, sender):
        """Adds a comment to a task."""
        return await self.notion_sync.add_comment(task_id, text, sender)

    async def get_comments(self, task_id):
        """Fetches comments for a task."""
        return await self.notion_sync.get_comments(task_id)

    async def delete_comment(self, task_id, comment_id):
        """Deletes a comment from a task."""
        return await self.notion_sync.delete_comment(task_id, comment_id)

    async def update_priority(self, task_id, priority):
        """Updates the priority of a task."""
        return await self.notion_sync.update_task_priority(task_id, priority)

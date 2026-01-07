from notion_client import AsyncClient
import logging
import os

logger = logging.getLogger(__name__)

class NotionSync:
    def __init__(self):
        self.notion = None
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        
        # Auto-fix common copy-paste errors (remove ?v=... and full URL)
        if self.database_id:
            if "?" in self.database_id:
                self.database_id = self.database_id.split("?")[0]
            if "/" in self.database_id:
                self.database_id = self.database_id.split("/")[-1]
            
            # Format as UUID if it's a raw 32 char string
            if len(self.database_id) == 32 and "-" not in self.database_id:
                self.database_id = f"{self.database_id[:8]}-{self.database_id[8:12]}-{self.database_id[12:16]}-{self.database_id[16:20]}-{self.database_id[20:]}"
                
        self.token = os.getenv("NOTION_TOKEN")
        
    def _get_client(self):
        """Lazy initialization of AsyncClient to ensure it attaches to the current loop."""
        if not self.notion and self.token:
            self.notion = AsyncClient(auth=self.token)
            logger.info("Notion AsyncClient initialized (Lazy).")
        return self.notion

    async def create_task_page(self, task):
        """Creates a page in the database asynchronously."""
        if not self._get_client() or not self.database_id: return None

        try:
            priority_val = task.get('priority', 0)
            
            # Map Status
            status_map = {
                "active": "Active",
                "done": "Done",
                "rejected": "Rejected"
            }
            status_val = status_map.get(task.get("status", "active"), "Active")

            new_page = await self._get_client().pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [{"text": {"content": task['summary']}}]
                    },
                    "Status": {
                        "status": {"name": status_val}
                    },
                    "Priority": {
                        "number": priority_val
                    },
                    "Sender": {
                        "rich_text": [{"text": {"content": task.get('sender', 'Unknown')}}]
                    },
                    "Link": {
                        "url": task.get('link') if task.get('link') else None
                    }
                }
            )
            logger.info(f"Synced task to Notion: {new_page['id']}")
            return new_page['id']
            
        except Exception as e:
            logger.error(f"Failed to sync to Notion: {e}")
            return None

    async def update_task_status(self, page_id, status):
        """Updates the status select property asynchronously."""
        if not self.notion or not page_id: return

        try:
            status_map = {
                "active": "Active",
                "done": "Done",
                "rejected": "Rejected"
            }
            status_val = status_map.get(status, "Active")
            
            await self.notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "status": {"name": status_val}
                    }
                }
            )
            logger.info(f"Updated Notion Page {page_id} to {status_val}")
        except Exception as e:
            logger.error(f"Failed to update Notion Page: {e}")

    async def find_task_by_link(self, link):
        """Checks if a task with the given link already exists using search asynchronously."""
        if not self._get_client() or not self.database_id or not link: return None
        
        try:
            # Search for pages (recent typically appear first in search results)
            response = await self.notion.search(
                filter={"value": "page", "property": "object"},
                sort={"direction": "descending", "timestamp": "last_edited_time"}
            )
            
            # Verify the PROPERTY "Link"
            for page in response.get("results", []):
                # Verify DB ID
                page_db_id = page.get("parent", {}).get("database_id", "").replace("-", "")
                target_db_id = self.database_id.replace("-", "")
                if page_db_id != target_db_id: continue

                props = page.get("properties", {})
                page_link = props.get("Link", {}).get("url", "")
                
                if page_link == link:
                    return page['id']
                    
            return None
        except Exception as e:
            logger.error(f"Failed to check task existence via search: {e}")
            return None

    def _parse_comments_text(self, full_text):
        """Helper to parse raw comment text into structured list."""
        comments = []
        if full_text:
            lines = full_text.split("\n")
            import re
            for line in lines:
                if not line.strip(): continue
                # Format: [ID] YYYY-MM-DD HH:MM:SS Sender: Text
                match = re.match(r"\[(.*?)\] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*?): (.*)", line)
                if match:
                    comments.append({
                        "id": match.group(1),
                        "timestamp": match.group(2),
                        "sender": match.group(3),
                        "text": match.group(4)
                    })
                else:
                    comments.append({
                        "id": "unknown",
                        "timestamp": "",
                        "sender": "Unknown",
                        "text": line
                    })
        return comments[::-1] # Newest first

    async def get_tasks(self):
        """Fetches all tasks from Notion database using search asynchronously."""
        if not self._get_client() or not self.database_id: return []

        try:
            response = await self._get_client().search(
                filter={"value": "page", "property": "object"},
                sort={"direction": "descending", "timestamp": "last_edited_time"}
            )
            
            tasks = []
            for page in response.get("results", []):
                # Verify DB ID
                page_db_id = page.get("parent", {}).get("database_id", "").replace("-", "")
                target_db_id = self.database_id.replace("-", "")
                
                if page_db_id != target_db_id: continue

                props = page.get("properties", {})
                
                # Safe Extraction Helpers
                def get_title(p):
                    return p.get("title", [])[0].get("text", {}).get("content", "") if p.get("title") else "Untitled"
                
                def get_select(p):
                    # Handle both 'select' and 'status' types
                    if "select" in p: return p.get("select", {}).get("name", "") if p.get("select") else ""
                    if "status" in p: return p.get("status", {}).get("name", "") if p.get("status") else ""
                    return ""

                def get_number(p):
                    return p.get("number", 0)
                
                def get_rich_text(p):
                    return p.get("rich_text", [])[0].get("text", {}).get("content", "") if p.get("rich_text") else ""
                
                def get_url(p):
                    return p.get("url", "")

                status = get_select(props.get("Status", {})).lower()
                summary = get_title(props.get("Name", {}))
                
                # Parse comments directly here to avoid N+1 fetches
                comments_text = get_rich_text(props.get("AgentComments", {}))
                comments = self._parse_comments_text(comments_text)

                # Internal format
                task = {
                    "id": page["id"], # Use Notion Page ID as internal ID
                    "summary": summary,
                    "status": status if status else "active",
                    "priority": get_number(props.get("Priority", {})),
                    "sender": get_rich_text(props.get("Sender", {})),
                    "link": get_url(props.get("Link", {})),
                    "deadline": get_rich_text(props.get("Deadline", {})),
                    "comments": comments, # Include comments
                    "notion_page_id": page["id"]
                }
                tasks.append(task)
                
            return tasks
        except Exception as e:
            logger.error(f"Failed to fetch tasks from Notion: {e}")
            return []


    async def get_comments(self, page_id):
        """Fetches comments from the AgentComments text property."""
        if not self._get_client() or not page_id: return []

        try:
            page = await self._get_client().pages.retrieve(page_id)
            props = page.get("properties", {})
            rich_text = props.get("AgentComments", {}).get("rich_text", [])
            full_text = "".join([t.get("text", {}).get("content", "") for t in rich_text])
            
            return self._parse_comments_text(full_text)
            
        except Exception as e:
            logger.error(f"Failed to fetch comments: {e}")
            return []

    async def add_comment(self, page_id, text, sender="Unknown"):
        """Appends a comment to the AgentComments property."""
        if not self._get_client() or not page_id: return None
        
        try:
            import datetime
            import uuid
            
            # timestamp
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comment_id = str(uuid.uuid4())[:8] # Short ID
            
            new_line = f"[{comment_id}] {now} {sender}: {text}"
            
            # 1. Get existing text
            page = await self._get_client().pages.retrieve(page_id)
            props = page.get("properties", {})
            rich_text = props.get("AgentComments", {}).get("rich_text", [])
            current_text = "".join([t.get("text", {}).get("content", "") for t in rich_text])
            
            updated_text = current_text + ("\n" if current_text else "") + new_line
            
            # 3. Update
            await self._get_client().pages.update(
                page_id=page_id,
                properties={
                    "AgentComments": {
                        "rich_text": [{"text": {"content": updated_text[:2000]}}]
                    }
                }
            )
            logger.info(f"Added comment to {page_id}: {text}")
            return {
                "id": comment_id,
                "timestamp": now,
                "sender": sender,
                "text": text
            }
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return None

    async def delete_comment(self, page_id, comment_id):
        """Removes a comment line by ID."""
        if not self._get_client() or not page_id: return False
        
        try:
            # 1. Get existing text
            page = await self._get_client().pages.retrieve(page_id)
            props = page.get("properties", {})
            rich_text = props.get("AgentComments", {}).get("rich_text", [])
            current_text = "".join([t.get("text", {}).get("content", "") for t in rich_text])
            
            if not current_text: return False
            
            # 2. Filter lines
            lines = current_text.split("\n")
            new_lines = [line for line in lines if f"[{comment_id}]" not in line]
            
            if len(lines) == len(new_lines):
                logger.warning(f"Comment {comment_id} not found.")
                return False
                
            updated_text = "\n".join(new_lines)
            
            # 3. Update
            await self._get_client().pages.update(
                page_id=page_id,
                properties={
                    "AgentComments": {
                        "rich_text": [{"text": {"content": updated_text[:2000]}}]
                    }
                }
            )
            logger.info(f"Deleted comment {comment_id} from {page_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete comment: {e}")
            return False

    async def update_task_priority(self, page_id, priority):
        """Updates the Priority number property asynchronously."""
        if not self._get_client() or not page_id: return False

        try:
            await self._get_client().pages.update(
                page_id=page_id,
                properties={
                    "Priority": {
                        "number": int(priority)
                    }
                }
            )
            logger.info(f"Updated Notion Page {page_id} Priority to {priority}")
            return True
        except Exception as e:
            logger.error(f"Failed to update Notion Page Priority: {e}")
            return False

from notion_client import Client
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
                
        token = os.getenv("NOTION_TOKEN")
        
        if token and self.database_id:
            try:
                self.notion = Client(auth=token)
                logger.info("Notion Client initialized.")
            except Exception as e:
                logger.error(f"Failed to init Notion Client: {e}")
        else:
            logger.warning("NOTION_TOKEN or NOTION_DATABASE_ID missing. Sync disabled.")

    def create_task_page(self, task):
        """Creates a page in the database."""
        if not self.notion or not self.database_id: return None

        try:
            priority_val = task.get('priority', 0)
            
            # Map Status
            status_map = {
                "active": "Active",
                "done": "Done",
                "rejected": "Rejected"
            }
            status_val = status_map.get(task.get("status", "active"), "Active")

            new_page = self.notion.pages.create(
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

    def update_task_status(self, page_id, status):
        """Updates the status select property."""
        if not self.notion or not page_id: return

        try:
            status_map = {
                "active": "Active",
                "done": "Done",
                "rejected": "Rejected"
            }
            status_val = status_map.get(status, "Active")
            
            self.notion.pages.update(
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

    def get_tasks(self):
        """Fetches all tasks from Notion database."""
        if not self.notion or not self.database_id: return []

        try:
            # Fallback to search if query fails
            response = self.notion.search(
                filter={"value": "page", "property": "object"},
                sort={"direction": "descending", "timestamp": "last_edited_time"}
            )
            
            tasks = []
            for page in response.get("results", []):
                # Check IDs (handle dashes/no-dashes comparison)
                # Some pages return parent type as 'database_id', others as 'data_source_id'
                # Just check if 'database_id' key exists in parent and matches.
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
                
                # Internal format
                task = {
                    "id": page["id"], # Use Notion Page ID as internal ID
                    "summary": summary,
                    "status": status if status else "active",
                    "priority": get_number(props.get("Priority", {})),
                    "sender": get_rich_text(props.get("Sender", {})),
                    "link": get_url(props.get("Link", {})),
                    "deadline": get_rich_text(props.get("Deadline", {})), # Assuming Deadline is Text for now
                    "notion_page_id": page["id"]
                }
                tasks.append(task)
                
            return tasks
        except Exception as e:
            logger.error(f"Failed to fetch tasks from Notion: {e}")
            return []

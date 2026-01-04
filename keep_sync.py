import gkeepapi
import logging
import os

logger = logging.getLogger(__name__)

class KeepSync:
    def __init__(self):
        self.keep = gkeepapi.Keep()
        self.email = os.getenv("GOOGLE_EMAIL")
        raw_password = os.getenv("GOOGLE_APP_PASSWORD")
        self.password = raw_password.replace(" ", "") if raw_password else None
        self.initialized = False
        
    def login(self):
        if self.initialized:
            return True
            
        if not self.email or not self.password:
            logger.warning("GOOGLE_EMAIL or GOOGLE_APP_PASSWORD not set. Keep Sync disabled.")
            return False
            
        try:
            # Try to authenticate (handles some 2FA cases better than login)
            success = self.keep.authenticate(self.email, self.password)
            if success:
                logger.info("Successfully authenticated with Google Keep.")
                self.initialized = True
                return True
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Keep: {e}")
            
        return False

    def sync_task(self, task):
        """Creates a new note for the task."""
        if not self.login(): return

        try:
            # Create Note
            title = f"Task: {task['summary']}"
            text = f"Priority: {task['priority']}\nSender: {task['sender']}\nDeadline: {task.get('deadline', 'None')}\nLink: {task.get('link', '')}"
            
            note = self.keep.createNote(title, text)
            
            # Add Label
            label = self.keep.findLabel('TelegramAgent')
            if not label:
                label = self.keep.createLabel('TelegramAgent')
            note.labels.add(label)
            
            # Set Color based on Priority
            if task.get('priority', 0) >= 8:
                note.color = gkeepapi.node.ColorValue.Red
            elif task.get('priority', 0) >= 5:
                note.color = gkeepapi.node.ColorValue.Yellow
            else:
                note.color = gkeepapi.node.ColorValue.Blue
                
            self.keep.sync()
            
            # Store the Keep Note ID in the task (in memory/json) for future updates
            task['keep_id'] = note.id
            logger.info(f"Synced task to Keep: {note.id}")
            return note.id
            
        except Exception as e:
            logger.error(f"Failed to sync task to Keep: {e}")

    def update_status(self, keep_id, status):
        """Updates the status of an existing note."""
        if not self.login() or not keep_id: return

        try:
            note = self.keep.get(keep_id)
            if not note:
                logger.warning(f"Keep Note not found: {keep_id}")
                return

            if status == 'done':
                note.title = "[DONE] " + note.title.replace("[DONE] ", "").replace("[REJECTED] ", "")
                note.archived = True
                note.color = gkeepapi.node.ColorValue.Green
            elif status == 'rejected':
                note.title = "[REJECTED] " + note.title.replace("[DONE] ", "").replace("[REJECTED] ", "")
                note.archived = True
                note.color = gkeepapi.node.ColorValue.Gray
            elif status == 'active': # Reopen
                note.title = note.title.replace("[DONE] ", "").replace("[REJECTED] ", "")
                note.archived = False
                note.color = gkeepapi.node.ColorValue.Blue 
                
            self.keep.sync()
            logger.info(f"Updated Keep Note {keep_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update Keep Note: {e}")

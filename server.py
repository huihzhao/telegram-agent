from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

# We will inject the TaskManager instance from main.py
task_manager = None
notification_callback = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/tasks")
async def get_tasks():
    if not task_manager:
        return []
    return await task_manager.get_tasks()

@app.post("/api/done/{task_id}")
async def mark_done(task_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    # SSOT: Direct call
    await task_manager.mark_done(task_id)
    if notification_callback:
        # We might need to fetch the task to get the summary for the notification
        # For now, let's just notify generic success or skip summary
        await notification_callback(f"Task {task_id} marked as Done")
        
    return {"status": "success", "task": task_id}

@app.post("/api/reject/{task_id}")
async def reject_task(task_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    # SSOT: Direct call
    await task_manager.reject_task(task_id)
    return {"status": "success", "task": task_id}

@app.post("/api/reopen/{task_id}")
async def reopen_task(task_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    await task_manager.reopen_task(task_id)
    return {"status": "success", "task": task_id}

@app.get("/api/discussions/history")
async def get_discussion_history():
    from discussion_buffer import DiscussionBuffer
    db = DiscussionBuffer() # It loads from disk, so fresh instance is fine or can inject
    return db.get_history()

@app.get("/api/discussions/today")
async def get_today_discussion():
    from discussion_buffer import DiscussionBuffer
    db = DiscussionBuffer()
    return db.get_grouped_text() or "No discussions yet."

from pydantic import BaseModel
class CommentRequest(BaseModel):
    text: str
    sender: str = "User"

@app.get("/api/comments/{task_id}")
async def get_comments(task_id: str):
    if not task_manager: return []
    return await task_manager.get_comments(task_id)

@app.post("/api/comments/{task_id}")
async def add_comment(task_id: str, request: CommentRequest):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    result = await task_manager.add_comment(task_id, request.text, request.sender)
    if result:
        return result
    return JSONResponse(status_code=500, content={"error": "Failed to add comment"})

@app.delete("/api/comments/{task_id}/{comment_id}")
async def delete_comment(task_id: str, comment_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
        
    success = await task_manager.delete_comment(task_id, comment_id)
    if success:
        return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Comment not found or failed to delete"})


@app.post("/api/priority/{task_id}")
async def update_priority(task_id: str, request: dict):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    priority = request.get("priority")
    if priority is None:
        return JSONResponse(status_code=400, content={"error": "Priority missing"})
        
    success = await task_manager.update_priority(task_id, priority)
    if success:
        return {"status": "success", "task": task_id, "priority": priority}
    return JSONResponse(status_code=500, content={"error": "Failed to update priority"})


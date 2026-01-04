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
    return task_manager.get_tasks()

@app.post("/api/done/{task_id}")
async def mark_done(task_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    # Optional logic: Find the task first to log/notify about it
    task = next((t for t in task_manager.tasks if t["id"] == task_id), None)
    if task:
        task_manager.remove_task(task_id)
        if notification_callback:
            await notification_callback(task['summary'])
        return {"status": "success", "task": task['summary']}
    
    return JSONResponse(status_code=404, content={"error": "Task not found"})

@app.post("/api/reject/{task_id}")
async def reject_task(task_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    # Optional logic: Find the task first to log/notify about it
    task = next((t for t in task_manager.tasks if t["id"] == task_id), None)
    if task:
        task_manager.reject_task(task_id)
        # We might not want to notify for rejections, or maybe we do?
        # if notification_callback: await notification_callback(f"Rejected: {task['summary']}")
        return {"status": "success", "task": task['summary']}
    
    return JSONResponse(status_code=404, content={"error": "Task not found"})

@app.post("/api/reopen/{task_id}")
async def reopen_task(task_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    task = next((t for t in task_manager.tasks if t["id"] == task_id), None)
    if task:
        task_manager.reopen_task(task_id)
        return {"status": "success", "task": task['summary']}
    
    return JSONResponse(status_code=404, content={"error": "Task not found"})

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
    
    # SSOT: Direct call
    task_manager.mark_done(task_id)
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
    task_manager.reject_task(task_id)
    return {"status": "success", "task": task_id}

@app.post("/api/reopen/{task_id}")
async def reopen_task(task_id: str):
    if not task_manager:
        return JSONResponse(status_code=500, content={"error": "TaskManager not initialized"})
    
    # SSOT: Direct call
    task_manager.reopen_task(task_id)
    return {"status": "success", "task": task_id}

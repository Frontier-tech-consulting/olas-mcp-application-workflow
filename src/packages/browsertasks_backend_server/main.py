import os
import platform
import asyncio
from dotenv import load_dotenv
import dotenv
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime
import logging
import traceback
from langchain_openai import ChatOpenAI
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from dotenv import find_dotenv, load_dotenv
import tempfile
import shutil
import uuid
from mcp.server.fastmcp import FastMCP

# ----------------------------
# 1. Configure Logging
# ----------------------------



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# 2. Load Environment Variables
# ----------------------------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

# ----------------------------
# 3. Initialize FastAPI App
# ----------------------------
app = FastAPI(title="MCP powered browser", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# 4. Define Pydantic Models
# ----------------------------
class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    result: str

class TaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskRecord(BaseModel):
    id: int
    task: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # Duration in seconds
    result: Optional[str] = None
    error: Optional[str] = None

class BrowserSessionRequest(BaseModel):
    task: str
    headless: bool = True
    steps: Optional[str] = None
    context: Optional[str] = None
    persistent: bool = True

class BrowserSessionResponse(BaseModel):
    session_id: str
    message: str

# ----------------------------
# 5. Initialize Task Registry
# ----------------------------
task_records: List[TaskRecord] = []
task_id_counter: int = 0
task_lock = asyncio.Lock()  # To manage concurrent access to task_records

# ----------------------------
# 6. Chrome Path Utility
# ----------------------------
def get_chrome_path() -> str:
    system = platform.system()
    if system == "Windows":
        chrome_path = os.path.join(
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            "Google\\Chrome\\Application\\chrome.exe"
        )
    elif system == "Darwin":
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Linux":
        chrome_path = "/usr/bin/google-chrome"
    else:
        raise FileNotFoundError(f"Unsupported operating system: {system}")
    if not os.path.exists(chrome_path):
        raise FileNotFoundError(f"Google Chrome executable not found at: {chrome_path}")
    return chrome_path

# ----------------------------
# 7. Background Task Function
# ----------------------------
def filter_text_messages(messages):
    filtered = []
    for msg in messages:
        # If content is a list, filter out non-text types
        if isinstance(msg.get('content'), list):
            text_parts = [part for part in msg['content'] if isinstance(part, str)]
            if text_parts:
                msg['content'] = ' '.join(text_parts)
            else:
                continue  # skip if no text
        elif not isinstance(msg.get('content'), str):
            continue  # skip non-text
        filtered.append(msg)
    return filtered

async def execute_task(task_id: int, task: str, headless: bool = True, stream_callback=None):
    global task_records
    browser = None
    try:
        logger.info(f"Starting background task ID {task_id}: {task}")
        async with task_lock:
            task_record = TaskRecord(
                id=task_id,
                task=task,
                status=TaskStatus.RUNNING,
                start_time=datetime.utcnow()
            )
            task_records.append(task_record)
        browser = Browser(
            config=BrowserConfig(
                chrome_instance_path=get_chrome_path(),
                disable_security=True,
                headless=headless,
            )
        )
        agent = Agent(
            task=task,
            llm=ChatOpenAI(model="gpt-4o", api_key=api_key),
            browser=browser,
            
        )
        logger.info(f"Task ID {task_id}: Agent initialized. Running task.")
        if stream_callback:
            async for chunk in agent.run_stream():
                await stream_callback(chunk)
            result = "[streamed]"
        else:
            result = await agent.run()
        logger.info(f"Task ID {task_id}: Agent.run() completed successfully.")
        async with task_lock:
            for record in task_records:
                if record.id == task_id:
                    record.status = TaskStatus.COMPLETED
                    record.end_time = datetime.utcnow()
                    record.duration = (record.end_time - record.start_time).total_seconds()
                    record.result = result
                    break
    except Exception as e:
        logger.error(f"Error in background task ID {task_id}: {e}")
        logger.error(traceback.format_exc())
        async with task_lock:
            for record in task_records:
                if record.id == task_id:
                    record.status = TaskStatus.FAILED
                    record.end_time = datetime.utcnow()
                    record.duration = (record.end_time - record.start_time).total_seconds()
                    record.error = str(e)
                    break
    finally:
        if browser:
            try:
                logger.info(f"Task ID {task_id}: Closing browser instance.")
                await browser.close()
                logger.info(f"Task ID {task_id}: Browser instance closed successfully.")
            except Exception as close_e:
                logger.error(f"Task ID {task_id}: Error closing browser: {close_e}")
                logger.error(traceback.format_exc())

# ----------------------------
# 8. POST /run Endpoint
# ----------------------------
@app.post("/run", response_model=TaskResponse)
async def run_task_post(request: TaskRequest, background_tasks: BackgroundTasks, headless: bool = False):
    global task_id_counter
    task = request.task
    logger.info(f"Received task via POST: {task}")
    async with task_lock:
        task_id_counter += 1
        current_task_id = task_id_counter
    background_tasks.add_task(execute_task, current_task_id, task, headless)
    return TaskResponse(result="Task is being processed.")

# ----------------------------
# 9. GET /run Endpoint
# ----------------------------
@app.get("/run", response_model=TaskResponse)
async def run_task_get(task: str = Query(..., description="The task description for the AI agent."), background_tasks: BackgroundTasks = None, headless: bool = False):
    global task_id_counter
    logger.info(f"Received task via GET: {task}")
    async with task_lock:
        task_id_counter += 1
        current_task_id = task_id_counter
    if background_tasks:
        background_tasks.add_task(execute_task, current_task_id, task, headless)
    else:
        asyncio.create_task(execute_task(current_task_id, task, headless))
    return TaskResponse(result="Task is being processed.")

# ----------------------------
# 10. GET /lastResponses Endpoint
# ----------------------------
@app.get("/lastResponses", response_model=List[TaskRecord])
async def get_last_responses(limit: int = Query(100, description="Maximum number of task records to return"), status: Optional[TaskStatus] = Query(None, description="Filter by task status")):
    async with task_lock:
        filtered_tasks = task_records.copy()
        if status:
            filtered_tasks = [task for task in filtered_tasks if task.status == status]
        sorted_tasks = sorted(filtered_tasks, key=lambda x: x.id, reverse=True)[:limit]
        return sorted_tasks

# ----------------------------
# 11. Root Endpoint
# ----------------------------
@app.get("/")
def read_root():
    return {"message": "AI Agent API with BrowserUse is running. Use the /run endpoint with a 'task' field in the POST request body or as a query parameter in a GET request to execute tasks."}

# ----------------------------
# 12. Entry Point
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8888, reload=True, workers=1)

# Define the MCP server
mcp = FastMCP("Browser Automation MCP")

@mcp.tool()
async def browser_automation(
    task: str,
    headless: bool = True,
    steps: str = "",
    context: str = "",
    additional_details: str = ""
) -> str:
    from browser_use import Agent
    from browser_use.browser.browser import Browser, BrowserConfig
    from langchain_openai import ChatOpenAI
    import os
    api_key = os.environ.get("OPENAI_API_KEY") or globals().get("api_key")
    browser = Browser(
        config=BrowserConfig(
            chrome_instance_path=get_chrome_path(),
            disable_security=True,
            headless=headless,
        )
    )
    # Combine all context for the agent
    full_task = f"{task}\nSteps: {steps}\nContext: {context}\nDetails: {additional_details}"
    agent = Agent(
        task=full_task,
        llm=ChatOpenAI(model="gpt-4o", api_key=api_key),
        browser=browser,
    )
    result = await agent.run()
    await browser.close()
    return result

# Mount the MCP server as a sub-app in FastAPI
app.mount("/mcp", mcp.sse_app())

@app.post("/browser-automation-stream")
async def browser_automation_stream(request: Request):
    data = await request.json()
    async def event_stream():
        from browser_use import Agent
        from browser_use.browser.browser import Browser, BrowserConfig
        from langchain_openai import ChatOpenAI
        import os
        api_key = os.environ.get("OPENAI_API_KEY") or globals().get("api_key")
        browser = Browser(
            config=BrowserConfig(
                chrome_instance_path=get_chrome_path(),
                disable_security=True,
                headless=data.get("headless", True),
            )
        )
        full_task = f"{data.get('task', '')}\nSteps: {data.get('steps', '')}\nContext: {data.get('context', '')}\nDetails: {data.get('additional_details', '')}"
        agent = Agent(
            task=full_task,
            llm=ChatOpenAI(model="gpt-4o", api_key=api_key),
            browser=browser,
        )
        try:
            # agent.run() returns a string, so stream it line by line
            result = await agent.run()
            for line in str(result).splitlines():
                yield f"data: {json.dumps({'type': 'browser-use', 'output': line})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        finally:
            await browser.close()
    return StreamingResponse(event_stream(), media_type="text/event-stream")

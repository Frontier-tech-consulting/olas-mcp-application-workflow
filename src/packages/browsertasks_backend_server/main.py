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
from typing import List, Optional, Any
from enum import Enum
from datetime import datetime
import logging
import traceback
from langchain_openai import ChatOpenAI
from browser_use import Agent, AgentHistoryList
from browser_use.browser.browser import Browser, BrowserConfig
from dotenv import find_dotenv, load_dotenv
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
    import base64
    data = await request.json()
    from browser_use import Agent, AgentHistoryList
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
    # Only pass supported arguments to Agent
    # Concatenate steps/context/additional_details into the task string
    task_str = data.get('task', '')
    if data.get('steps'):
        task_str += f"\nSteps: {data['steps']}"
    if data.get('context'):
        task_str += f"\nContext: {data['context']}"
    if data.get('additional_details'):
        task_str += f"\nDetails: {data['additional_details']}"
    agent = Agent(
        task=task_str,
        llm=ChatOpenAI(model="gpt-4o", api_key=api_key),
        browser=browser,
    )
    try:
        result = await agent.run(max_steps=30)
        # Typecast to AgentHistoryList and use model_dump_json
        if isinstance(result, AgentHistoryList):
            result_json = result.model_dump_json()
        else:
            try:
                result_json = AgentHistoryList.model_validate(result).model_dump_json()
            except Exception:
                result_json = json.dumps(result, default=str)
        return StreamingResponse(
            (f"data: {json.dumps({'type': 'agent-result', 'result': json.loads(result_json)})}\n\n" for _ in range(1)),
            media_type="text/event-stream"
        )
    finally:
        await browser.close()

def run_mech_job_with_agent_history(
    agent_history_json,
    prompt=None,
    agent_id="6",
    tool=None,
    chain_config="gnosis",
    private_key_path="ethereum_private_key.txt",
    confirm_type="on-chain",
):
    """
    Run a Mech client job using the actual CLI, passing the extracted content from AgentHistoryList as the prompt.
    Returns the parsed output (dict or string).
    """
    import tempfile
    import os
    import shlex
    import subprocess
    # 1. Extract content from AgentHistoryList
    steps = agent_history_json
    extracted_contents = []
    # If steps is a dict with 'history', extract all 'extracted_content' fields
    if isinstance(steps, dict) and 'history' in steps:
        for step in steps['history']:
            if 'result' in step and step['result']:
                for r in step['result']:
                    if r.get('extracted_content'):
                        extracted_contents.append(str(r['extracted_content']))
    # If steps is a list, treat as already extracted
    elif isinstance(steps, list):
        extracted_contents = [str(s) for s in steps]
    browser_summary = "\n".join(extracted_contents)
    # 2. Use prompt if provided, else use browser_summary
    mech_prompt = prompt or browser_summary
    # 3. Build the mechx interact command
    cmd = f"mechx interact {shlex.quote(mech_prompt)} --agent_id {shlex.quote(str(agent_id))} --chain-config {shlex.quote(chain_config)} --key {shlex.quote(private_key_path)} --confirm {shlex.quote(confirm_type)}"
    if tool:
        cmd += f" --tool {shlex.quote(tool)}"
    # 4. Run the command and collect output
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    output_lines = []
    for line in process.stdout:
        output_lines.append(line.rstrip())
    process.stdout.close()
    process.wait()
    # 5. Try to parse the last JSON object in the output (if any)
    mech_result = None
    for line in reversed(output_lines):
        try:
            parsed = json.loads(line)
            mech_result = parsed
            break
        except Exception:
            continue
    return mech_result or output_lines

@app.post("/mech-job-stream")
async def mech_job_stream(request: Request):
    """
    FastAPI endpoint to run the Mech client job and stream output lines as SSE.
    Expects JSON body with keys: agent_history_json, prompt, agent_id, tool, chain_config, private_key_path, confirm_type
    """
    import shlex, subprocess, json
    data = await request.json()
    agent_history_json = data.get("agent_history_json")
    prompt = data.get("prompt")
    agent_id = data.get("agent_id", "6")
    tool = data.get("tool")
    chain_config = data.get("chain_config", "gnosis")
    private_key_path = data.get("private_key_path", "ethereum_private_key.txt")
    confirm_type = data.get("confirm_type", "on-chain")
    # Extract content from AgentHistoryList
    steps = agent_history_json
    extracted_contents = []
    if isinstance(steps, dict) and 'history' in steps:
        for step in steps['history']:
            if 'result' in step and step['result']:
                for r in step['result']:
                    if r.get('extracted_content'):
                        extracted_contents.append(str(r['extracted_content']))
    elif isinstance(steps, list):
        extracted_contents = [str(s) for s in steps]
    browser_summary = "\n".join(extracted_contents)
    mech_prompt = prompt or browser_summary
    cmd = f"mechx interact {shlex.quote(mech_prompt)} --agent_id {shlex.quote(str(agent_id))} --chain-config {shlex.quote(chain_config)} --key {shlex.quote(private_key_path)} --confirm {shlex.quote(confirm_type)}"
    if tool:
        cmd += f" --tool {shlex.quote(tool)}"
    def stream_lines():
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
        process.stdout.close()
        process.wait()
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(stream_lines(), media_type="text/event-stream")

async def run_mech_job_streaming(
    agent_history_json: Any,
    prompt: str = None,
    agent_id: str = "6",
    tool: str = None,
    chain_config: str = "gnosis",
    private_key_path: str = "ethereum_private_key.txt",
    confirm_type: str = "on-chain"
):
    """
    MCP tool to run the Mech client job and stream output lines.
    """
    import shlex, subprocess, json
    steps = agent_history_json
    extracted_contents = []
    if isinstance(steps, dict) and 'history' in steps:
        for step in steps['history']:
            if 'result' in step and step['result']:
                for r in step['result']:
                    if r.get('extracted_content'):
                        extracted_contents.append(str(r['extracted_content']))
    elif isinstance(steps, list):
        extracted_contents = [str(s) for s in steps]
    browser_summary = "\n".join(extracted_contents)
    mech_prompt = prompt or browser_summary
    cmd = f"mechx interact {shlex.quote(mech_prompt)} --agent_id {shlex.quote(str(agent_id))} --chain-config {shlex.quote(chain_config)} --key {shlex.quote(private_key_path)} --confirm {shlex.quote(confirm_type)}"
    if tool:
        cmd += f" --tool {shlex.quote(tool)}"
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        yield line.rstrip()
    process.stdout.close()
    process.wait()
    # Do not use 'return' with a value in an async generator
    # Just finish the generator

@app.post("/mech-job-stream-mock")
async def mech_job_stream_mock(request: Request):
    """
    Mock FastAPI endpoint to simulate the Mech client job and stream a hardcoded result as SSE.
    """
    import json
    import asyncio
    async def stream_lines():
        # Simulate streaming a few lines
        yield f"data: {json.dumps({'line': 'Running Mech job...'})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'line': 'Processing input...'})}\n\n"
        await asyncio.sleep(0.5)
        # Hardcoded mock result
        mock_result = {
            'result': 'This is a mock Mech client output. Your job ran successfully!',
            'status': 'success',
            'details': {
                'tool': 'mock-tool',
                'agent_id': '6',
                'chain': 'gnosis',
                'output': '42',
            }
        }
        yield f"data: {json.dumps({'line': json.dumps(mock_result)})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(stream_lines(), media_type="text/event-stream")

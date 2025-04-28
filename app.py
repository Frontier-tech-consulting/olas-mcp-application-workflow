from browser_use import AgentHistoryList
import mcp
import streamlit as st
import os
import time
import random
import json
import pandas as pd
import numpy as np
import hashlib
import threading
from dotenv import load_dotenv

from src.models.request import Request
from browser_use import AgentHistoryList
from src.components.request_form import RequestForm
from src.components.staking_info_rendering import render_account_and_staking_info
from src.components.privy_auth import display_mock_privy_login
from src.components.mech_client import (
    mech_client_workflow,
    mech_client_interact_ui,
    submit_mech_request_ui
)
from src.components.process_payment import (
    process_payment

)

from src.mcp_params import MCPService


from src.components.process_payment import process_payment
from src.components.mcp_app_list import app_storefront

from pathlib import Path
from dotenv import load_dotenv

from src.utils.supabase_utils import SupabaseObj


from src.pages.app_home_page import app_home
from src.pages.landing_page import display_landing_page
# from src.pages.login_page import app_login

from src.components.dashboard_page import (
    display_user_header,
    create_request as dashboard_create_request,
    execution_page as dashboard_execution_page,
    app_dashboard as dashboard_app
)
import subprocess
import shlex
import streamlit as st
from src.components.mech_client import mech_client_workflow, mech_client_interact_ui
from src.components.styling import (define_mainpage_styling, define_styling_app)


from src.utils.session_state import (
    init_session_state, save_session_state_if_authenticated
)

dotenv_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

from src.components.mech_client_components import run_mech_job_with_agent_history

def browseruse_to_mech_pipeline(agent_history_json, prompt=None):
    """
    Pipeline: Receives AgentHistoryList output, selects a Mech tool, runs the Mech job, and renders the filtered response.
    - agent_history_json: JSON/dict from browser-use AgentHistoryList
    - prompt: Optional, if you want to use the original user prompt
    """
    st.markdown("""
    <h3>BrowserUse → Mech Pipeline</h3>
    <p>This pipeline takes the output of the browser agent, selects a Mech tool, runs the Mech job, and displays the result.</p>
    """, unsafe_allow_html=True)

    # 1. Filter/Extract relevant info from AgentHistoryList
    steps = agent_history_json
    extracted_contents = []
    for step in steps:
        if 'extracted_content' in step and step['extracted_content']:
            extracted_contents.append(str(step['extracted_content']))
        elif 'model_outputs' in step and step['model_outputs']:
            extracted_contents.append(str(step['model_outputs']))
    browser_summary = "\n".join(extracted_contents)
    st.info("**Extracted Content from Browser Agent:**\n" + browser_summary)

    # 2. Use LLM to select the best Mech tool
    available_tools = [
        "prediction-request-rag",
        "prediction-request-reasoning",
        "superforcaster",
        "prediction-offline",
        "prediction-online",
        "prediction-offline-sme",
        "prediction-online-sme"
    ]
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    reasoning_prompt = ChatPromptTemplate.from_template(
        """You are an expert AI agent. Given the following extracted content and the available tools, select the best tool for the next step.\n\nExtracted Content: {content}\nAvailable Tools: {tools}\n\nRespond ONLY with the tool name from the list that is the best fit."""
    )
    chain = reasoning_prompt | llm
    tool_response = chain.invoke({"content": browser_summary, "tools": ", ".join(available_tools)})
    selected_tool = None
    for tool in available_tools:
        if tool in tool_response.content:
            selected_tool = tool
            break
    if not selected_tool:
        selected_tool = available_tools[0]
    st.success(f"Selected Mech Tool: {selected_tool}")

    # 3. Run the actual Mech job using the CLI
    mech_result = run_mech_job_with_agent_history(
        agent_history_json,
        prompt=prompt or browser_summary,
        agent_id="6",
        tool=selected_tool,
        chain_config="gnosis",
        confirm_type="on-chain",
    )
    return mech_result




# Import authentication components
from src.components.auth_page import (
    format_eth_address,
    generate_eth_address,
    display_verification_page
)

# Import dashboard page components
from src.components.dashboard_page import (
    display_user_header,
    create_request as dashboard_create_request,
    execution_page as dashboard_execution_page,
    app_dashboard as dashboard_app
)



mcp_service = MCPService()

# Page configuration
st.set_page_config(
    page_title="OLAS MCP Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load environment variables
load_dotenv()

# Initialize clients
supabase_client = SupabaseObj()

define_mainpage_styling()  # Define main page styling

def browser_extension_workflow():
    st.markdown("""
    <h2 style='text-align:center;'>MCP browser app</h2>
    <p style='text-align:center;'>Configure and run browser automation tasks using the MCP browser agent.</p>
    """, unsafe_allow_html=True)
    
    # Single input for automation command
    automation_command = st.text_area("Automation Command", placeholder="Describe the browser automation steps or context here...", height=120)
    # Dropdown for Mech tool/model type
    available_tools = [
        "prediction-request-rag",
        "prediction-request-reasoning",
        "superforcaster",
        "prediction-offline",
        "prediction-online",
        "prediction-offline-sme",
        "prediction-online-sme"
    ]
    selected_tool = st.selectbox("Select Mech Model/Tool", options=available_tools)
    headless = st.checkbox("Run in headless mode", value=False)
    
    # Streaming output containers
    scrollable_browser_output = st.empty()
    browser_output_placeholder = st.empty()
    gif_placeholder = st.empty()
    final_result_placeholder = st.empty()
    debug_placeholder = st.empty()
    
    if st.button("Run Automation & Mech", type="primary"):
        payload = {
            "task": automation_command or "Open google.com and search for OLAS.",
            "headless": headless,
            "steps": automation_command,
            "context": automation_command,
        }
        import requests
        import sseclient
        import base64
        debug_events = []
        agent_history_json = None
        extracted_content_json = None
        try:
            with requests.post("http://localhost:8888/browser-automation-stream", json=payload, stream=True, timeout=300) as resp:
                client = sseclient.SSEClient(resp)
                result = None
                for event in client.events():
                    debug_events.append(event.data)
                    debug_placeholder.code("\n".join(debug_events), language="json")
                    if event.data:
                        data = json.loads(event.data)
                        agent_history_json = data.get("result")
                        st.markdown("### Output Scraping Data")
                        if agent_history_json is not None:
                            st.json(agent_history_json)
                        else:
                            st.info("No extracted content found in AgentHistoryList.")
                        browser_chunks = getattr(st.session_state, 'browser_chunks', [])
                        browser_chunks.append(json.dumps(data, indent=2, ensure_ascii=False))
                        st.session_state.browser_chunks = browser_chunks
                        scrollable_browser_output.markdown(
                            f"<div style='max-height:400px;overflow-y:auto;'>{'<br><br>'.join(browser_chunks)}" + "</div>",
                            unsafe_allow_html=True
                        )
                    if event.data and data.get("type") == "done":
                        st.success("Automation complete.")
                        break
            # After streaming, if we have the agent history, call the /mech-job-stream endpoint and stream output
            if agent_history_json:
                st.markdown("### Mech Client Output (Streaming)")
                # Convert browseruse output to a string for the prompt
                browseruse_text = ""
                if isinstance(agent_history_json, dict) and 'history' in agent_history_json:
                    extracted_contents = []
                    for step in agent_history_json['history']:
                        if 'result' in step and step['result']:
                            for r in step['result']:
                                if r.get('extracted_content'):
                                    extracted_contents.append(str(r['extracted_content']))
                    browseruse_text = "\n".join(extracted_contents)
                elif isinstance(agent_history_json, str):
                    browseruse_text = agent_history_json
                else:
                    browseruse_text = str(agent_history_json)
                mech_payload = {
                    "agent_history_json": None,  # Not used as prompt, just pass as string
                    "prompt": browseruse_text or automation_command,
                    "agent_id": "6",
                    "tool": selected_tool,
                    "chain_config": "gnosis",
                    "private_key_path": os.path.abspath("ethereum_private_key.txt"),
                    "confirm_type": "on-chain"
                }
                try:
                    with requests.post("http://localhost:8888/mech-job-stream", json=mech_payload, stream=True, timeout=600) as mech_resp:
                        mech_client = sseclient.SSEClient(mech_resp)
                        mech_lines = []
                        for event in mech_client.events():
                            if event.data:
                                try:
                                    line_data = json.loads(event.data)
                                    if 'line' in line_data:
                                        mech_lines.append(line_data['line'])
                                        st.code("\n".join(mech_lines), language="bash")
                                    elif line_data.get('type') == 'done':
                                        st.success("Mech job complete.")
                                except Exception:
                                    continue
                except Exception as e:
                    st.error(f"Mech job streaming error: {e}")
        except Exception as e:
            browser_output_placeholder.error(f"Streaming error: {e}")

# ...existing code...

def main():
    # Initialize session state if needed
    if 'initialized' not in st.session_state:
        init_session_state()
        st.session_state.initialized = True
    
    # Set page configuration
    # st.set_page_config(
    #     page_title="Olas MCP Platform",
    #     page_icon="🧠",
    #     layout="wide",
    #     initial_sidebar_state="collapsed"
    # )
    
    # Custom CSS to ensure all buttons have white, bold text on black background
    define_styling_app()
        
    # Process payment if needed
    if st.session_state.get('payment_processing', False) and not st.session_state.get('payment_completed', False):
        process_payment(st.session_state.current_request)
    
    # Navigate to the correct page
    if st.session_state.page == 'landing':
        display_landing_page()
    elif st.session_state.page == 'home':
        app_home()
    elif st.session_state.page == 'login':
        if st.session_state.authenticated:
            st.session_state.page = 'app_storefront'
            st.rerun()
        else:
            display_mock_privy_login()
    elif st.session_state.page == 'app_storefront':
        app_storefront()
    elif st.session_state.page == 'verify':
        if st.session_state.authenticated:
            st.session_state.page = 'create_request'
            st.rerun()
        else:
            display_verification_page(supabase_client, save_session_state_if_authenticated)
    elif st.session_state.page == 'create_request':
        if not st.session_state.authenticated:
            st.session_state.page = 'login'
            st.rerun()
        else:
            dashboard_create_request(mcp_service, save_session_state_if_authenticated)
    elif st.session_state.page == 'execution':
        if not st.session_state.authenticated:
            st.session_state.page = 'login'
            st.rerun()
        else:
            dashboard_execution_page(mcp_service, process_payment)
    elif st.session_state.page == 'dashboard':
        if not st.session_state.authenticated:
            st.session_state.page = 'login'
            st.rerun()
        else:
            dashboard_app()
    elif st.session_state.page == 'browser_extension':
        browser_extension_workflow()
        return
    elif st.session_state.page == 'mech_request':
        submit_mech_request_ui()
        return
    elif st.session_state.page == 'mech_client_interact':
        mech_client_interact_ui()
        return
    elif st.session_state.page == 'mech_client':
        mech_client_workflow()
        return
    else:
        st.error(f"Unknown page: {st.session_state.page}")
        st.session_state.page = 'landing'
        st.rerun()

# Main navigation router
if __name__ == "__main__":
    # Initialize session state
    init_session_state()
    
    # Call main function with all app logic
    main()


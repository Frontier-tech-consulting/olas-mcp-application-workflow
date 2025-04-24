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
from src.utils.execution_status import ExecutionStatus

from pathlib import Path
from dotenv import load_dotenv

from src.utils.supabase_utils import SupabaseObj


from src.pages.app_home_page import app_home
from src.pages.landing_page import display_landing_page
from src.pages.login_page import app_login

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
    
    # User options
    col1, col2 = st.columns(2)
    with col1:
        headless = st.checkbox("Run in headless mode", value=True)
        additional_details = st.text_area("Additional Details", placeholder="Provide any extra details for the automation task...", height=80)
    with col2:
        steps = st.text_area("Automation Steps / Context", placeholder="Describe the browser automation steps or context here...", height=120)
    
    # Streaming output containers
    mech_output_placeholder = st.empty()
    browser_output_placeholder = st.empty()
    scrollable_browser_output = st.empty()
    
    # Run button
    if 'browser_streaming' not in st.session_state:
        st.session_state.browser_streaming = False
    if st.button("Run Automation (Stream Output)", type="primary") and not st.session_state.browser_streaming:
        st.session_state.browser_streaming = True
        st.session_state.browser_stream_chunks = []
        def stream_browser_output():
            import requests
            import sseclient
            payload = {
                "task": steps or "Open google.com and search for OLAS.",
                "headless": headless,
                "steps": steps,
                "context": steps,
                "additional_details": additional_details
            }
            try:
                # Use requests to get the SSE stream
                with requests.post("http://localhost:8888/browser-automation-stream", json=payload, stream=True, timeout=300) as resp:
                    client = sseclient.SSEClient(resp)
                    browser_chunks = []
                    for event in client.events():
                        if event.data:
                            data = json.loads(event.data)
                            if data.get("type") == "browser-use":
                                chunk = data.get("output")
                                browser_chunks.append(str(chunk))
                                # Update scrollable output
                                scrollable_browser_output.markdown(
                                    f"<div style='max-height:300px;overflow-y:auto;background:#f8f8f8;padding:10px;border-radius:6px;font-family:monospace;font-size:0.95em;'>{'<br>'.join(browser_chunks)}</div>",
                                    unsafe_allow_html=True
                                )
                            elif data.get("type") == "done":
                                st.session_state.browser_streaming = False
                                break
            except Exception as e:
                browser_output_placeholder.error(f"Streaming error: {e}")
                st.session_state.browser_streaming = False
        # Run streaming in a thread to avoid blocking Streamlit
        threading.Thread(target=stream_browser_output, daemon=True).start()
    elif st.session_state.get("browser_streaming"):
        st.info("Streaming browser-use output... (see below)")
    # Show static result if available
    if st.session_state.get("browser_mcp_result"):
        st.markdown("---")
        st.markdown("**Automation Result:**")
        st.text_area("Result", st.session_state.browser_mcp_result, height=200)

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
            app_login()
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
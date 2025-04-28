import streamlit as st
import time
from datetime import datetime
from src.components.request_form import RequestForm
from src.components.execution_status import ExecutionStatus
from src.models.request import Request

def format_eth_address(address):
    """Format an Ethereum address for display with ellipsis in the middle"""
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"

def display_user_header():
    """Display the user header with account information"""
    if st.session_state.authenticated and 'account_info' in st.session_state:
        account_info = st.session_state.account_info
        address = account_info.get('wallet_address', '')
        display_address = account_info.get('display_address', format_eth_address(address))
        
        # Create columns for layout
        _, col_header = st.columns([0.7, 0.3])
        
        with col_header:
            st.markdown(f"""
            <div style="text-align: right; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                <span style="font-weight: bold;">{account_info.get('email')}</span><br>
                <span style="font-family: monospace; font-size: 0.9em;">
                    {display_address} <span style="background-color: #e6e6e6; padding: 2px 5px; border-radius: 3px; font-size: 0.8em;">Gnosis Chain</span>
                </span>
            </div>
            """, unsafe_allow_html=True)

def dashboard():
    """Display task history and chat sidebar"""
    # Display task history header
    st.markdown("<h2>Task History</h2>", unsafe_allow_html=True)
    
    # Create mock task history data
    if 'task_history' not in st.session_state:
        # Initialize with some mock history data
        st.session_state.task_history = [
            {
                "id": "tx-001",
                "date": "2023-09-15",
                "prompt": "Analyze APY rates for Uniswap pools",
                "services": ["1815", "1966"],
                "status": "completed"
            },
            {
                "id": "tx-002",
                "date": "2023-09-20",
                "prompt": "Compare gas fees across different L2 solutions",
                "services": ["1722", "1999"],
                "status": "completed"
            },
            {
                "id": "tx-003",
                "date": "2023-09-27",
                "prompt": "Find arbitrage opportunities between DEXs",
                "services": ["1983", "2010"],
                "status": "error"
            }
        ]
    
    # Display task history in a table with styled cards
    if not st.session_state.task_history:
        st.info("You don't have any task history yet. Create a new request to get started.")
    else:
        for task in st.session_state.task_history:
            # Determine the status color
            status_color = "#4CAF50" if task["status"] == "completed" else "#F44336"
            
            # Create a styled card for each task
            st.markdown(f"""
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: white;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 0.9rem; color: #555;">{task["date"]}</span>
                    <span style="background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem;">{task["status"].title()}</span>
                </div>
                <h4 style="margin-top: 0; margin-bottom: 10px;">{task["prompt"]}</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px;">
                    {' '.join([f'<span style="background-color: #f0f0f0; color: #333; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">Service {service_id}</span>' for service_id in task["services"]])}
                </div>
                <div style="font-family: monospace; font-size: 0.85rem; color: #666; margin-bottom: 10px;">Transaction ID: {task["id"]}</div>
            </div>
            """, unsafe_allow_html=True)

    # Button to create a new request
    if st.button("Create New Request"):
        st.session_state.page = 'create_request'
        st.rerun()
    
    # Sidebar for chats
    st.sidebar.markdown("<h3>Chats</h3>", unsafe_allow_html=True)
    st.sidebar.write("Chat history will be displayed here.")

def create_request(mcp_service, save_session_state_callback):
    """Create a new request"""
    # Display user header
    display_user_header()
    
    def handle_submit(request: Request):
        # Submit request to MCP service
        try:
            transaction_id = mcp_service.submit_request(request)
            # Ensure we got a valid transaction ID
            if transaction_id and isinstance(transaction_id, str):
                request.transaction_id = transaction_id
                st.session_state.current_request = request
                st.session_state.page = 'execution'
                # Clear any reasoning and service selection session state
                if 'reasoning_complete' in st.session_state:
                    st.session_state.reasoning_complete = False
                if 'reasoning_response' in st.session_state:
                    st.session_state.reasoning_response = ""
                if 'selected_services' in st.session_state:
                    st.session_state.selected_services = []
                save_session_state_callback()
                st.rerun()
            else:
                st.error(f"Failed to submit request: Invalid transaction ID format ({type(transaction_id)})")
        except Exception as e:
            st.error(f"Failed to submit request: {str(e)}")
    
    # Initialize request form with user email
    user_email = st.session_state.account_info['email'] if st.session_state.authenticated else "guest@example.com"
    request_form = RequestForm(handle_submit, user_email)
    request_form.render()
    
    # Back button
    if st.button("Back to Dashboard"):
        # Clear any reasoning and service selection session state
        if 'reasoning_complete' in st.session_state:
            st.session_state.reasoning_complete = False
        if 'reasoning_response' in st.session_state:
            st.session_state.reasoning_response = ""
        if 'selected_services' in st.session_state:
            st.session_state.selected_services = []
        st.session_state.page = 'dashboard'
        st.rerun()

def execution_page(mcp_service, process_payment_function):
    """
    Application execution page showing service execution status
    """
    # Display user header
    display_user_header()
    
    # Check if we're in payment processing mode
    if st.session_state.get('payment_processing', False) and not st.session_state.get('payment_completed', False):
        # Show payment processing UI
        process_payment_function(st.session_state.current_request)
        return
    
    # Ensure the request is properly stored in session state
    if 'current_request' in st.session_state and st.session_state.current_request:
        # Also store in the standard 'request' key that ExecutionStatus expects
        st.session_state.request = st.session_state.current_request
        
        # Initialize execution status component with current request and render it
        execution_status = ExecutionStatus()
        execution_status.render()
    else:
        st.error("No active request found. Please create a request first.")
        if st.button("Back to Request Form", key="back_to_request_nodata"):
            st.session_state.page = "create_request"
            st.rerun()

def app_dashboard():
    """Application dashboard page showing user's requests and status"""
    # Display user information in header
    display_user_header()
    
    # Display dashboard title
    st.markdown("""
    <div class="dashboard-header">
        <h2>Task Dashboard</h2>
        <p>View and manage your service requests</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create request button at top
    if st.button("Create New Request", key="new_request_button"):
        st.session_state.page = 'create_request'
        st.rerun()
    
    # Show submitted requests
    st.markdown("### Your Tasks")
    
    # Get submitted requests from session_state
    submitted_requests = st.session_state.get('submitted_requests', [])
    
    if not submitted_requests:
        st.info("You haven't submitted any requests yet.")
        
        # Show dummy requests for demo purposes
        st.markdown("### Demo Tasks")
        
        # Create some mock historical tasks
        demo_tasks = [
            {
                "id": "task-001",
                "prompt": "Analyze market trends for DeFi protocols",
                "submitted_at": "2023-11-01T14:30:00",
                "status": "completed",
                "services": [
                    {"name": "Market Analysis", "id": "service-001"},
                    {"name": "Trend Prediction", "id": "service-002"}
                ],
                "total_cost": 45.0
            },
            {
                "id": "task-002",
                "prompt": "Generate smart contract audit report",
                "submitted_at": "2023-11-05T09:15:00",
                "status": "completed",
                "services": [
                    {"name": "Smart Contract Audit", "id": "service-003"}
                ],
                "total_cost": 30.0
            }
        ]
        
        # Display mock tasks
        for task in demo_tasks:
            with st.expander(f"{task['prompt'][:50]}...", expanded=False):
                st.markdown(f"**ID:** {task['id']}")
                st.markdown(f"**Submitted:** {task['submitted_at']}")
                st.markdown(f"**Status:** {task['status'].upper()}")
                
                # Show services
                st.markdown("**Services:**")
                for service in task['services']:
                    st.markdown(f"- {service['name']} (ID: {service['id']})")
                
                st.markdown(f"**Total Cost:** {task['total_cost']} OLAS")
                
                # Show demo button
                st.button("View Details", key=f"view_{task['id']}", disabled=True)
    else:
        # Display actual submitted requests
        for i, request in enumerate(submitted_requests):
            # Extract data safely
            prompt = request.get('prompt', 'No description')
            submitted_at = request.get('submitted_at', 'Unknown date')
            tx_id = request.get('transaction_id', 'No transaction ID')
            status = "Completed"  # For demo purposes
            
            # Format date for display if it's an ISO string
            try:
                if isinstance(submitted_at, str) and 'T' in submitted_at:
                    dt = datetime.fromisoformat(submitted_at)
                    submitted_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass  # Keep original format if parsing fails
            
            # Create a card for each request
            with st.expander(f"{prompt[:50]}...", expanded=i==0):
                st.markdown(f"**Submitted:** {submitted_at}")
                st.markdown(f"**Transaction ID:** [{tx_id[:10]}...{tx_id[-6:]}](https://gnosisscan.io/tx/{tx_id})")
                st.markdown(f"**Status:** {status}")
                
                # Show services
                if 'selected_services' in request:
                    st.markdown("**Services:**")
                    for service in request.get('selected_services', []):
                        service_name = service.get('name', 'Unknown service')
                        service_id = service.get('id', 'N/A')
                        st.markdown(f"- {service_name} (ID: {service_id})")
                
                # Show total cost
                st.markdown(f"**Total Cost:** {request.get('total_cost', 0)} OLAS")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View Execution", key=f"view_exec_{i}"):
                        st.session_state.current_request = request
                        st.session_state.page = 'execution'
                        st.rerun()
                with col2:
                    if st.button("New Similar Request", key=f"similar_{i}"):
                        st.session_state.request_text = prompt
                        st.session_state.page = 'create_request'
                        st.rerun()

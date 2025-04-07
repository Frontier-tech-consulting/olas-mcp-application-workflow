import streamlit as st
import os
from src.models.request import Request
from src.services.mcp_service import MCPService
from src.components.request_form import RequestForm
from src.components.execution_status import ExecutionStatus
import time
import random
import json

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "page": "home",
        "authenticated": False,
        "account_info": None,
        "selected_app": None,
        "show_login": True,
        "show_signup": False,
        "current_request": None,
        "transaction_id": None,
        "chain": "Gnosis Chain",  # Default chain
        "payment_processing": False,
        "payment_completed": False,
        "submitted_requests": [],
        "services": []  # Initialize empty services list
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Load services data from JSON file if not already in session state
    if not st.session_state.get("services"):
        try:
            with open('enriched_services_data.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "services" in data:
                    st.session_state.services = data["services"]
                    print(f"Loaded {len(data['services'])} services into session state")
                elif isinstance(data, list):
                    st.session_state.services = data
                    print(f"Loaded {len(data)} services into session state")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading services data: {str(e)}")
            # Use default services if file not found
            st.session_state.services = []

# Initialize MCP service
try:
    server_url = os.getenv("MCP_SERVER_URL")
    if server_url:
        print(f"Initializing MCP service with server URL: {server_url}")
        mcp_service = MCPService(server_url)
    else:
        print("Initializing MCP service with mock profile")
        mcp_service = MCPService("mock")
except Exception as e:
    print(f"Error initializing MCP service: {str(e)}")
    # Fallback to mock service
    mcp_service = MCPService("mock")

def app_home():
    """Home page with app selection"""
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; margin-bottom: 3rem;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">Pearl App Store</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # If already authenticated, show quick access to last used app
    if st.session_state.authenticated:
        st.markdown("### Welcome Back!")
        st.markdown(f"Continue working with {st.session_state.selected_app.replace('_', ' ').title() if st.session_state.selected_app else 'Olas apps'}:")
        
        # Create three columns for quick access options
        col1, col2, col3 = st.columns(3)
    
        with col1:
            if st.button("Continue Last App", key="home_continue", use_container_width=True):
                if st.session_state.selected_app == "olas_mcp":
                    st.session_state.page = 'create_request'
                else:
                    st.session_state.page = 'dashboard'
                st.rerun()
    
        with col2:
            if st.button("Browse All Apps", key="home_browse", use_container_width=True):
                # This will show the app listings below
                pass
        
        with col3:
            if st.button("Logout", key="home_logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.account_info = {}
                st.rerun()
    
    # Display available apps
    st.markdown("### Available Applications")
    
    # Create a 2x2 grid of app cards
    col1, col2 = st.columns(2)
    
    with col1:
        # MCP App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://assets.website-files.com/625a1e828031aa55b8e0c4b2/6498b97f7c82d53a6e38065d_olas-icon-p-500.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
                </div>
            <h3 style="text-align: center; margin-bottom: 8px;">Olas MCP</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Access AI services through the Multi-Chain Protocol
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> AI Task Processing<br>
                    <span style="color: #4CAF50;">✓</span> On-chain Payment<br>
                    <span style="color: #4CAF50;">✓</span> Gnosis Chain Integration
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
        if st.button("Open Olas MCP", key="open_mcp", use_container_width=True):
            st.session_state.selected_app = "olas_mcp"
            if st.session_state.authenticated:
                st.session_state.page = 'create_request'
            else:
                st.session_state.page = 'login'
            st.rerun()
    
    with col2:
        # Pearl Store App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://static.wixstatic.com/media/e52fa3_6e54262068914db7bfaebe3f37d0b5f7~mv2.png/v1/crop/x_131,y_0,w_639,h_800/fill/w_120,h_150,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/intro-pearl-store.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
            </div>
            <h3 style="text-align: center; margin-bottom: 8px;">Pearl Store</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Decentralized marketplace for digital assets
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> NFT Marketplace<br>
                    <span style="color: #4CAF50;">✓</span> Creator Economy<br>
                    <span style="color: #4CAF50;">✓</span> Multi-chain Support
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
        if st.button("Open Pearl Store", key="open_pearl", use_container_width=True):
            st.session_state.selected_app = "pearl_store"
            if st.session_state.authenticated:
                st.session_state.page = 'dashboard'
            else:
                st.session_state.page = 'login'
            st.rerun()

    # Second row of apps
    col3, col4 = st.columns(2)
    
    with col3:
        # DeFi Dashboard App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://cdn-icons-png.flaticon.com/512/5726/5726778.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
            </div>
            <h3 style="text-align: center; margin-bottom: 8px;">DeFi Dashboard</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Analytics and management for DeFi protocols
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> Portfolio Tracking<br>
                    <span style="color: #4CAF50;">✓</span> Yield Optimization<br>
                    <span style="color: #4CAF50;">✓</span> Risk Management
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open DeFi Dashboard", key="open_defi", use_container_width=True, disabled=True):
            st.session_state.selected_app = "defi_dashboard"
            st.info("Coming soon! This app is under development.")
    
    with col4:
        # Governance Portal App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://cdn-icons-png.flaticon.com/512/5372/5372785.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
            </div>
            <h3 style="text-align: center; margin-bottom: 8px;">Governance Portal</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Participate in DAO governance and voting
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> Proposal Creation<br>
                    <span style="color: #4CAF50;">✓</span> Voting Interface<br>
                    <span style="color: #4CAF50;">✓</span> Delegation Tools
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Governance Portal", key="open_gov", use_container_width=True, disabled=True):
            st.session_state.selected_app = "governance_portal"
            st.info("Coming soon! This app is under development.")

def generate_eth_address(seed):
    """Generate a mock Ethereum address from a seed string"""
    import hashlib
    # Create a hash from the seed to generate a deterministic but random-looking result
    h = hashlib.sha256(seed.encode()).hexdigest()
    # Ethereum addresses are 40 hex chars (20 bytes) prefixed with 0x
    return f"0x{h[:40]}"

def generate_gnosis_safe_address(owner_address):
    """
    Generate a mock Gnosis Safe address based on an owner address
    This simulates a deployed Safe smart contract wallet
    
    Args:
        owner_address: The address of the Safe owner
    
    Returns:
        A mock Gnosis Safe address
    """
    import hashlib
    import time
    
    # Use owner address, current time and a salt to generate a unique address
    salt = str(int(time.time()))
    safe_creation_data = f"{owner_address}{salt}safe"
    
    # Use SHA256 to create a deterministic hash
    h = hashlib.sha256(safe_creation_data.encode()).hexdigest()
    
    # Return a formatted Ethereum address that looks like a Safe address
    # Gnosis Safe addresses on Gnosis Chain often have a specific pattern
    return f"0x{h[:40]}"

def app_login():
    """Application login page with mock authentication"""
    # Create a header for the login page
    st.markdown(f"""
    <div class="header">
        <h1>{st.session_state.selected_app.replace('_', ' ').title()}</h1>
        <p>Sign in to access the application dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # Show authentication form
    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        # Center the login button and control its width
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button("Login")
            
        if submit:
            # Login logic
            if email and password:
                # Create a mock owner wallet address
                owner_address = generate_eth_address(email.lower())
                
                # Create a mock Gnosis Safe address based on the owner address
                safe_address = generate_gnosis_safe_address(owner_address)
                
                # Store formatted address for display
                display_address = format_eth_address(safe_address)
                
                st.session_state.authenticated = True
                st.session_state.account_info = {
                    "email": email,
                    "user_id": "mock_user_id",
                    "wallet_address": safe_address,
                    "owner_address": owner_address,
                    "display_address": display_address
                }
                st.success("Login successful!")
                st.session_state.page = 'create_request'
                st.rerun()
            else:
                st.error("Please enter both email and password")
    
    # Back button
    if st.button("Back to App Store"):
        st.session_state.page = 'home'
        st.rerun()

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
    
def format_eth_address(address):
    """Format an Ethereum address for display with ellipsis in the middle"""
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"

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

def create_request():
    """Create a new request"""
    # We no longer need to call user_profile_card() here
    
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

def app_execution_page():
    """
    Application execution page showing service execution status
    """
    # Display user header
    display_user_header()
    
    # Check if we're in payment processing mode
    if st.session_state.get('payment_processing', False) and not st.session_state.get('payment_completed', False):
        # Show payment processing UI
        process_payment(st.session_state.current_request)
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

# Process payment and show status
def process_payment(request):
    """
    Process payment for a service request
    
    This function simulates a blockchain transaction with progress updates
    
    Args:
        request: The request object containing services and cost
    """
    # Set initial payment state if not already done
    if 'payment_step' not in st.session_state:
        st.session_state.payment_step = 0
    
    if 'payment_messages' not in st.session_state:
        st.session_state.payment_messages = []
    
    # Steps in payment process
    steps = [
        "Creating transaction...",
        "Submitting to Gnosis Safe...",
        "Broadcasting to blockchain network...",
        "Waiting for block inclusion...",
        "Transaction confirmed!"
    ]
    
    # Get current step
    current_step = st.session_state.payment_step
    
    # Display payment processing UI
    st.markdown("### Processing Payment")
    
    # Show progress bar
    if current_step < len(steps) - 1:
        progress = (current_step + 1) / len(steps)
        st.progress(progress)
    else:
        st.progress(1.0)
    
    # Display current step
    if current_step < len(steps):
        st.markdown(f"**Status:** {steps[current_step]}")
    
    # Log message for this step if new
    if len(st.session_state.payment_messages) <= current_step:
        if current_step == 0:
            message = f"Creating transaction to send {request.get('total_cost', 0)} OLAS from your Gnosis Safe"
        elif current_step == 1:
            message = "Requesting signature from Gnosis Safe wallet"
        elif current_step == 2:
            message = f"Transaction hash: {request.get('transaction_id', '0xdd9b42c0f72fbda6b01746b10e2e2bd4506819c65b156e2817f0b9c0e5f5d86a')}"
        elif current_step == 3:
            message = "Estimated confirmation time: 15-30 seconds"
        else:
            message = "Payment successful! Your request is now being processed."
        
        st.session_state.payment_messages.append(message)
    
    # Show all messages so far
    for msg in st.session_state.payment_messages:
        st.info(msg)
    
    # Advance to next step after delay
    if current_step < len(steps) - 1:
        # Simulate blockchain confirmation times with appropriate delays
        if current_step == 3:  # Waiting for block inclusion is longest step
            time.sleep(10)  # 10 seconds for block confirmation
        else:
            time.sleep(3)  # 3 seconds for other steps
        
        st.session_state.payment_step += 1
        st.rerun()
    else:
        # Payment complete, wait briefly then set payment completed
        time.sleep(3)
        st.session_state.payment_processing = False
        st.session_state.payment_completed = True
        st.session_state.payment_step = 0
        st.session_state.payment_messages = []
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
                    from datetime import datetime
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

def main():
    # Initialize session state if needed
    if 'initialized' not in st.session_state:
        init_session_state()
    
    # Set page configuration
    st.set_page_config(
        page_title="Olas MCP",
        page_icon="🔄",
        layout="wide"
    )
    
    # Custom CSS to ensure all buttons have white, bold text on black background
    st.markdown("""
    <style>
    /* Style for all standard Streamlit buttons */
    .stButton button {
        color: white !important;
        background-color: black !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    /* Style for navigation buttons */
    .stButton button[data-testid="baseButton-secondary"] {
        color: white !important;
        background-color: black !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    /* Style for form submit buttons */
    button[type="submit"] {
        color: white !important;
        background-color: black !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 10px !important;
        border: none !important;
    }
    
    /* Hover state */
    .stButton button:hover {
        color: white !important;
        background-color: #333 !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
            
    # Process payment if needed
    if st.session_state.get('payment_processing', False) and not st.session_state.get('payment_completed', False):
        process_payment(st.session_state.current_request)
    
    # Navigate to the correct page
    if st.session_state.page == 'home':
        app_home()
    elif st.session_state.page == 'login':
        if st.session_state.authenticated:
            st.session_state.page = 'create_request'
            st.rerun()
        else:
            app_login()
    elif st.session_state.page == 'create_request':
        if not st.session_state.authenticated:
            st.session_state.page = 'login'
            st.rerun()
        else:
            # Instantiate request form with submit callback
            submit_callback = lambda request: None  # Replace with actual callback if needed
            request_form = RequestForm(submit_callback=submit_callback, user_email=st.session_state.account_info.get("email", ""))
            request_form.render()
    elif st.session_state.page == 'execution':
        if not st.session_state.authenticated:
            st.session_state.page = 'login'
            st.rerun()
        else:
            app_execution_page()
    elif st.session_state.page == 'dashboard':
        if not st.session_state.authenticated:
            st.session_state.page = 'login'
            st.rerun()
        else:
            app_dashboard()
    else:
        st.error(f"Unknown page: {st.session_state.page}")
        st.session_state.page = 'home'
        st.rerun()

# Main navigation router
if __name__ == "__main__":
    # Initialize session state
    init_session_state()
    
    # Call main function with all app logic
    main()
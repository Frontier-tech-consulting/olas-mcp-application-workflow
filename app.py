import streamlit as st
import os
from src.models.request import Request
from src.services.mcp_service import MCPService
from src.components.request_form import RequestForm
from src.components.execution_status import ExecutionStatus
import time

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
        "payment_completed": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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

def home():
    """Home page with Pearl App Store layout"""
    st.markdown("""
    <div class="header-container">
        <h1>Pearl App Store</h1>
        <p>Discover and use powerful decentralized applications</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display available apps in a horizontal stack
    st.markdown("""
    <div class="info-box">
        <h3>Featured Applications</h3>
        <p>Select an application to get started</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a horizontal stack of app cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h4>OLAS MCP</h4>
            <p>Build and deploy MCP services on top of OLAS mech services architecture</p>
            <div class="app-meta">
                <span class="tag">Featured</span>
                <span class="tag">New</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Select", key="olas_mcp"):
            st.session_state.selected_app = "olas_mcp"
            st.session_state.page = 'app_login'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="card">
            <h4>Prediction Agent</h4>
            <p>AI-powered prediction engine for market trends and asset performance</p>
            <div class="app-meta">
                <span class="tag">Popular</span>
                <span class="tag">AI</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
        if st.button("Select", key="prediction_agent"):
            st.session_state.selected_app = "prediction_agent"
            st.session_state.page = 'app_login'
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="card">
            <h4>Agents.fun</h4>
            <p>Base platform for creating and managing autonomous agent networks</p>
            <div class="app-meta">
                <span class="tag">Base</span>
                <span class="tag">Beta</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Select", key="agents_fun"):
            st.session_state.selected_app = "agents_fun"
            st.session_state.page = 'app_login'
            st.rerun()

def app_login():
    """Application login/signup page with mock authentication"""
    # Create a header for the login page
    st.markdown(f"""
    <div class="header">
        <h1>{st.session_state.selected_app.replace('_', ' ').title()}</h1>
        <p>Sign in to access the application dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # Show single authentication form
    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        # Only show confirm password if in signup mode
        if not st.session_state.show_login:
            confirm_password = st.text_input("Confirm Password", type="password")
        
        # Using columns to center the submit button and control its width
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Change button text based on mode
            button_text = "Login" if st.session_state.show_login else "Sign Up"
            submit = st.form_submit_button(button_text)
            
        if submit:
            if st.session_state.show_login:
                # Login logic
                if email and password:
                    # Create a mock wallet address
                    wallet_address = f"0x{email.lower().replace('@', '').replace('.', '')[:8]}...{email.lower().replace('@', '').replace('.', '')[-4:]}"
                    st.session_state.authenticated = True
                    st.session_state.account_info = {
                        "email": email,
                        "user_id": "mock_user_id",
                        "wallet_address": wallet_address
                    }
                    st.success("Login successful!")
                    st.session_state.page = 'create_request'
                    st.rerun()
                else:
                    st.error("Please enter both email and password")
            else:
                # Signup logic
                if email and password and 'confirm_password' in locals() and confirm_password:
                    if password == confirm_password:
                        # Create a mock wallet address
                        wallet_address = f"0x{email.lower().replace('@', '').replace('.', '')[:8]}...{email.lower().replace('@', '').replace('.', '')[-4:]}"
                        st.session_state.authenticated = True
                        st.session_state.account_info = {
                            "email": email,
                            "user_id": "mock_user_id", 
                            "wallet_address": wallet_address
                        }
                        st.success("Signup successful!")
                        st.session_state.page = 'create_request'
                        st.rerun()
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")
    
    # Toggle between login and signup modes
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login Mode" if not st.session_state.show_login else "Already have an account", key="switch_to_login"):
            st.session_state.show_login = True
            st.rerun()
    with col2:
        if st.button("Signup Mode" if st.session_state.show_login else "Need an account?", key="switch_to_signup"):
            st.session_state.show_login = False
            st.rerun()
    
    # Back button
    if st.button("Back to App Store"):
        st.session_state.page = 'home'
        st.rerun()

def display_user_header():
    """Display the user info in the header if authenticated"""
    if st.session_state.authenticated and st.session_state.account_info:
        # Get user info
        user_email = st.session_state.account_info.get("email", "Anonymous")
        wallet_address = st.session_state.account_info.get("wallet_address", "")
        formatted_address = format_eth_address(wallet_address)
        chain = st.session_state.chain
        
        # Display user account info in the top right corner
        st.markdown(f"""
        <div style="position: absolute; top: 20px; right: 20px; text-align: right; z-index: 1000;">
            <div style="font-size: 0.9rem; margin-bottom: 5px;">{user_email}</div>
            <div style="background-color: #000; color: white; padding: 5px 10px; border-radius: 20px; 
                     font-family: monospace; font-size: 0.85rem; display: inline-block;">
                {formatted_address} | {chain}
            </div>
        </div>
        """, unsafe_allow_html=True)

def format_eth_address(address):
    """Format an Ethereum address for display (shorten with ellipsis)"""
    if not address or len(address) < 10:
        return address
    # Display first 6 and last 4 characters
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

def execution():
    """Display execution status"""
    # We no longer need to call user_profile_card() here
    
    # Check for active request
    if not st.session_state.current_request:
        st.error("No active request found")
        # Give user options instead of automatically redirecting
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Create New Request", key="create_request_from_exec"):
                st.session_state.page = 'create_request'
                st.rerun()
        with col2:
            if st.button("Return to Home", key="return_home_from_exec"):
                st.session_state.page = 'home'
                st.rerun()
        return
    
    # Display the execution status
    execution_status = ExecutionStatus(st.session_state.current_request)
    execution_status.render()

# Process payment and show status
def process_payment():
    """Simulate payment processing with a mock blockchain transaction"""
    if not st.session_state.payment_processing:
        return
        
    # If payment is already completed, do nothing
    if st.session_state.payment_completed:
        return
        
    # Add a progress bar for payment processing
    st.markdown("### Processing Payment")
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Simulate waiting for payment confirmation (takes 20 seconds)
    total_time = 20  # 20 seconds wait time
    for i in range(total_time + 1):
        # Calculate progress percentage
        progress = i / total_time
        
        # Update progress bar
        progress_placeholder.progress(progress)
        
        # Update status message based on progress
        if progress < 0.3:
            status_placeholder.info("Initiating blockchain transaction...")
        elif progress < 0.6:
            status_placeholder.info("Waiting for network confirmation...")
        elif progress < 0.9:
            status_placeholder.info("Validating payment on Gnosis Chain...")
        else:
            status_placeholder.info("Finalizing transaction...")
            
        # Sleep for a short interval
        time.sleep(1)
    
    # Mark payment as completed
    st.session_state.payment_completed = True
    st.session_state.payment_processing = False
    
    # Show success message
    status_placeholder.success("Payment confirmed! Your services are now being processed.")
    time.sleep(2)
    
    # Rerun the app to refresh the state
    st.rerun()

def main():
    init_session_state()
    
    # Set page config for a cleaner layout
    st.set_page_config(
        page_title="Pearl App Store",
        page_icon="🔮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply custom styling
    st.markdown("""
    <style>
        /* General styling */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
        }
        
        /* Header styling */
        .header-container {
            margin-bottom: 2rem;
            text-align: center;
        }
        
        /* Card styling */
        .card {
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            background-color: #fff;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        /* Button styling */
        .stButton button {
            background-color: #000000 !important; 
            color: #ffffff !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            border-radius: 4px !important;
            transition: all 0.3s;
            font-weight: 600 !important;
            width: 100%;
        }
        .stButton button:hover {
            background-color: #333333 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Button text styling - comprehensive selectors */
        .stButton button p, 
        .stButton button span,
        div[data-testid="StyledLinkIconContainer"] p,
        div[data-testid="StyledLinkIconContainer"] span,
        button[kind="primary"] p,
        button[kind="secondary"] p,
        div[data-baseweb="button"] p,
        div[data-baseweb="button"] span {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Aggressive button text fixing - target all button children */
        button *, button p, button span, button div {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Fix for Streamlit button text */
        button[kind="primaryFormSubmit"] p,
        button[kind="secondaryFormSubmit"] p,
        button[data-baseweb="button"] p,
        [data-testid="baseButton-secondary"] p,
        [data-testid="baseButton-primary"] p,
        [data-testid="StyledFullScreenButton"] span,
        button[data-testid*="StyledButton"] span {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Additional selector for any remaining buttons */
        div[role="button"] p, 
        div[role="button"] span {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Make sure task history button is styled properly */
        button[key="task_history_button"] {
            background-color: #333333 !important;
            border: 1px solid #000000 !important;
        }
        
        button[key="task_history_button"] p,
        button[key="task_history_button"] span {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* App metadata styling */
        .app-meta {
            margin-top: 1rem;
        }
        .tag {
            display: inline-block;
            background-color: #f0f0f0;
            color: #555;
            padding: 0.2rem 0.5rem;
            border-radius: 10px;
            font-size: 0.8rem;
            margin-right: 0.5rem;
        }
        
        /* Info box styling */
        .info-box {
            margin-bottom: 2rem;
            padding: 1rem;
            border-radius: 8px;
            background-color: #f7f7f7;
        }
        
        /* Improve form spacing */
        [data-testid="stForm"] {
            background-color: #f9f9f9;
            padding: 2rem;
            border-radius: 8px;
            max-width: 500px;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Display user info in header if authenticated
    display_user_header()
    
    # Process payment if needed
    if 'payment_processing' in st.session_state and st.session_state.payment_processing and 'payment_completed' in st.session_state and not st.session_state.payment_completed:
        process_payment()
    
    # Navigate to the correct page
    if st.session_state.page == "home":
        home()
    elif st.session_state.page == "app_login":
        app_login()
    elif st.session_state.page == "create_request":
        if not st.session_state.authenticated:
            st.warning("Please login to access this page")
            st.session_state.page = "app_login"
            st.rerun()
        else:
            create_request()
    elif st.session_state.page == "execution":
        if not st.session_state.authenticated:
            st.warning("Please login to access this page")
            st.session_state.page = "app_login"
            st.rerun()
        elif 'current_request' not in st.session_state or not st.session_state.current_request:
            st.error("No active request found. Please create a new request.")
            st.session_state.page = "create_request"
            st.rerun()
        else:
            execution()
    elif st.session_state.page == "dashboard":
        if not st.session_state.authenticated:
            st.warning("Please login to access this page")
            st.session_state.page = "app_login"
            st.rerun()
        else:
            dashboard()
    elif st.session_state.page == "view_execution_status":
        if not st.session_state.authenticated:
            st.warning("Please login to access this page")
            st.session_state.page = "app_login"
            st.rerun()
        elif 'transaction_id' not in st.session_state:
            st.error("No transaction ID found. Please submit a request first.")
            st.session_state.page = 'create_request'
            st.rerun()
        else:
            display_execution_status(st.session_state.transaction_id)
    else:
        home()  # Default to home page

# Main navigation router
if __name__ == "__main__":
    # Initialize session state
    init_session_state()
    
    # Call main function with all app logic
    main()
import streamlit as st
import os
from src.models.request import Request
from src.services.mcp_service import MCPService
from src.components.request_form import RequestForm
from src.components.execution_status import ExecutionStatus

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
        "transaction_id": None
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
    
    # Use columns to make the login/signup toggle buttons side by side
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Login", key="login_toggle", use_container_width=True):
            st.session_state.show_login = True
            st.session_state.show_signup = False
            st.rerun()
            
    with col2:
        if st.button("Sign Up", key="signup_toggle", use_container_width=True):
            st.session_state.show_login = False
            st.session_state.show_signup = True
            st.rerun()

    # Show login form
    if st.session_state.show_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            # Using columns to center the submit button and control its width
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit = st.form_submit_button("Login")
                
                # Apply custom styling to the form submit button
                st.markdown("""
                <style>
                div[data-testid="stForm"] button[kind="formSubmit"] {
                    background-color: #6200ee;
                    color: white;
                    border: none;
                }
                div[data-testid="stForm"] button[kind="formSubmit"]:hover {
                    background-color: #7722ff;
                }
                </style>
                """, unsafe_allow_html=True)
                
            if submit:
                # Mock authentication
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.account_info = {
                        "email": email,
                        "user_id": "mock_user_id"
                    }
                    st.success("Login successful!")
                    st.session_state.page = 'create_request'
                    st.rerun()
                else:
                    st.error("Please enter both email and password")

    # Show signup form
    if st.session_state.show_signup:
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # Using columns to center the submit button and control its width
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit = st.form_submit_button("Sign Up")
                
                # Apply custom styling to the form submit button
                st.markdown("""
                <style>
                div[data-testid="stForm"] button[kind="formSubmit"] {
                    background-color: #6200ee;
                    color: white;
                    border: none;
                }
                div[data-testid="stForm"] button[kind="formSubmit"]:hover {
                    background-color: #7722ff;
                }
                </style>
                """, unsafe_allow_html=True)
                
            if submit:
                # Mock signup
                if email and password and confirm_password:
                    if password == confirm_password:
                        st.session_state.authenticated = True
                        st.session_state.account_info = {
                            "email": email,
                            "user_id": "mock_user_id"
                        }
                        st.success("Signup successful!")
                        st.session_state.page = 'create_request'
                        st.rerun()
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")
    
    # Back button
    if st.button("Back to App Store"):
        st.session_state.page = 'home'
        st.rerun()

def user_profile_card():
    """Display user profile card with name and web address"""
    if st.session_state.authenticated:
        user_info = st.session_state.account_info
        st.markdown(f"""
        <div class="user-profile-card">
            <h3>{user_info['email']}</h3>
            <p>Web Address: <a href="https://example.com/{user_info['user_id']}">https://example.com/{user_info['user_id']}</a></p>
            <p>Safe Address: {user_info['user_id']}</p>
        </div>
        """, unsafe_allow_html=True)

def create_request():
    """Create a new request"""
    # Removed user_profile_card() call
    
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
    
    # Initialize execution status component
    status_component = ExecutionStatus(mcp_service)
    status_component.render(st.session_state.current_request)
    
    # Note: The back button is now in the ExecutionStatus component with a unique key

# Add a new dashboard page
def dashboard():
    """Display task history and chat sidebar"""
    st.markdown("<h2>Task History</h2>", unsafe_allow_html=True)
    # Placeholder for task history
    st.write("Task history will be displayed here.")
    
    # Sidebar for chats
    st.sidebar.markdown("<h3>Chats</h3>", unsafe_allow_html=True)
    st.sidebar.write("Chat history will be displayed here.")

def main():
    init_session_state()
    
    # Global CSS Styles
    st.markdown("""
    <style>
    /* Hide Streamlit UI elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* General Styles */
    .stApp {
        background-color: #fafafa;
        color: #2e2e2e;
    }
    
    /* Text color */
    p, h1, h2, h3, h4, h5, h6, div, span, label {
        color: #2e2e2e !important;
    }
    
    /* Button Styles - Purple with white text */
    div.stButton > button {
        background-color: #6200ee !important;
        color: white !important;
        border: none !important;
    }
    
    div.stButton > button:hover {
        background-color: #7722ff !important;
    }
    
    /* Login/Signup Toggle Buttons */
    div.stButton > button[data-testid*="login_toggle"],
    div.stButton > button[data-testid*="signup_toggle"] {
        background-color: #6200ee !important;
        color: white !important;
        border: none !important;
        border-radius: 4px;
        padding: 0.375rem 0.75rem;
        width: 100%;
        margin: 0;
    }
    
    div.stButton > button[data-testid*="login_toggle"]:hover,
    div.stButton > button[data-testid*="signup_toggle"]:hover {
        background-color: #7722ff !important;
        color: white !important;
    }
    
    div.stButton > button[data-testid*="login_toggle"]:focus,
    div.stButton > button[data-testid*="signup_toggle"]:focus {
        box-shadow: none;
        outline: none;
    }
    
    /* Form Submit Buttons */
    div[data-testid="stForm"] button[kind="formSubmit"] {
        background-color: #6200ee !important;
        color: white !important;
        border: none !important;
    }
    
    div[data-testid="stForm"] button[kind="formSubmit"]:hover {
        background-color: #7722ff !important;
    }
    
    /* Card Styles */
    .card {
        border-radius: 5px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Header Styles */
    .header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* User Profile */
    .user-profile {
        display: flex;
        align-items: center;
        background-color: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .user-profile-email {
        margin-left: 10px;
        font-weight: 500;
    }
    
    /* App Card Styles */
    .card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e6e9ed;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    .card h4 {
        color: #1a1a1a;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .card p {
        color: #666;
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 1.5rem;
        flex-grow: 1;
    }
    
    /* Header Container Style */
    .header-container {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
    }
    .header-container h1 {
        color: #1a1a1a;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .header-container p {
        color: #666;
        font-size: 1.2rem;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Info Box Style */
    .info-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 3rem;
        text-align: center;
    }
    .info-box h3 {
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        font-size: 1.8rem;
    }
    .info-box p {
        color: #666;
        font-size: 1.1rem;
    }
    
    /* Tag styles */
    .app-meta {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .tag {
        background-color: #e6f3ff;
        color: #0066cc;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Route to the appropriate page
    if st.session_state.page == 'home':
        home()
    elif st.session_state.page == 'app_login':
        app_login()
    elif st.session_state.page == 'create_request':
        create_request()
    elif st.session_state.page == 'execution':
        execution()
    elif st.session_state.page == 'dashboard':
        dashboard()
    elif st.session_state.page == 'view_execution_status':
        if 'transaction_id' in st.session_state:
            display_execution_status(st.session_state.transaction_id)
        else:
            st.error("No transaction ID found. Please submit a request first.")
            st.session_state.page = 'create_request'
            st.rerun()
    else:
        home()  # Default to home page

# Main navigation router
if __name__ == "__main__":
    # Initialize session state
    init_session_state()
    
    # Call main function with all app logic
    main()
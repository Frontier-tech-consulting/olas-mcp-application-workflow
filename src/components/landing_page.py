import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os
import time
import json
from dotenv import load_dotenv
from src.utils.supabase_utils import SupabaseObj
from src.utils.privy_rest_api import PrivyRestAPI
import requests

# Load environment variables
load_dotenv()

# Initialize clients
supabase_client = SupabaseObj()
privy_api = PrivyRestAPI()

# Page configuration
st.set_page_config(
    page_title="OLAS MCP Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .title-container {
        text-align: center;
        padding: 2rem 0;
    }
    .logo-image {
        width: 150px;
        margin-bottom: 1rem;
    }
    .chart-container {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin: 20px 0;
    }
    .hero-section {
        background-color: #4e6ef2;
        color: white;
        padding: 3rem 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    .feature-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin: 10px 0;
        height: 100%;
    }
    .cta-button {
        background-color: #4e6ef2;
        color: white;
        border-radius: 5px;
        padding: 0.75rem 1.5rem;
        font-weight: bold;
        text-align: center;
        display: inline-block;
        margin: 1rem 0;
        border: none;
    }
    .auth-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    .wallet-info {
        background-color: #e6f7ff;
        padding: 15px; 
        border-radius: 5px;
        margin-top: 20px;
    }
    .privy-input {
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ccc;
        margin-bottom: 15px;
        width: 100%;
    }
    .verification-code-input {
        letter-spacing: 0.5em;
        font-size: 24px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        "page": "landing",  # landing, login, verify, dashboard
        "authenticated": False,
        "login_email": "",
        "verification_id": "",
        "account_info": None,
        "selected_app": None,
        "wallet_address": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_session_state_if_authenticated():
    """Save session state to Supabase if user is authenticated"""
    if st.session_state.get("authenticated") and st.session_state.get("account_info"):
        user_id = st.session_state.account_info.get("user_id")
        if user_id:
            # Only save serializable keys
            state_to_save = {k: v for k, v in st.session_state.items() if k != "_callbacks"}
            supabase_client.save_session_state(user_id, state_to_save)

def generate_mock_agent_data():
    """Generate mock data for agent operations chart"""
    # Create date range for the last 6 months
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=180)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate increasing values with some randomness
    base_operations = np.linspace(100, 1000, len(date_range))
    agent_operations = base_operations + np.random.normal(0, base_operations * 0.1, len(date_range))
    agent_operations = np.maximum(agent_operations, 0)  # Ensure no negative values
    
    # Create dataframe
    df = pd.DataFrame({
        'date': date_range,
        'operations': agent_operations
    })
    
    return df

def generate_mock_usecase_data():
    """Generate mock data for agent usecase pie chart"""
    use_cases = [
        "DeFi Analytics", 
        "Token Price Analysis", 
        "Yield Farming Optimization", 
        "Risk Assessment", 
        "NFT Market Analysis"
    ]
    
    proportions = np.array([0.35, 0.25, 0.20, 0.12, 0.08])
    
    df = pd.DataFrame({
        'use_case': use_cases,
        'proportion': proportions
    })
    
    return df

def format_eth_address(address):
    """Format an Ethereum address for display with ellipsis in the middle"""
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"

def generate_eth_address(seed):
    """Generate a mock Ethereum address from a seed string"""
    import hashlib
    # Create a hash from the seed to generate a deterministic but random-looking result
    h = hashlib.sha256(seed.encode()).hexdigest()
    # Ethereum addresses are 40 hex chars (20 bytes) prefixed with 0x
    return f"0x{h[:40]}"

def display_landing_page():
    """Display the landing page content"""
    # Hero section
    st.markdown("""
    <div class="title-container">
        <img src="https://autonolas.network/images/logos/olas-logo.svg" class="logo-image" alt="OLAS Logo">
        <h1 style="font-size: 3rem;">OLAS MCP Platform</h1>
        <p style="font-size: 1.2rem; color: #666;">The gateway to AI agent services powered by Olas and the Model Context Protocol</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Hero call-to-action
    st.markdown("""
    <div class="hero-section">
        <h2>Connect, Interact, and Deploy AI Services</h2>
        <p style="font-size: 1.1rem; margin: 1rem 0;">
            Access a wide range of AI agents and services through the Model Context Protocol.
            Submit requests, track execution, and analyze results - all in one platform.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login button
    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    with login_col2:
        if st.button("Login with Privy", key="login_button", use_container_width=True, type="primary"):
            st.session_state.page = "login"
            st.rerun()
    
    # Agent Operations chart
    st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Agent Operations Growth</h2>", unsafe_allow_html=True)
    
    agent_data = generate_mock_agent_data()
    
    # Create line chart for agent operations
    operations_chart = alt.Chart(agent_data).mark_line(color='#4e6ef2').encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('operations:Q', title='Number of Operations'),
        tooltip=['date:T', alt.Tooltip('operations:Q', format='.0f')]
    ).properties(
        height=400
    ).interactive()
    
    st.altair_chart(operations_chart, use_container_width=True)
    
    # Use Case Distribution chart
    st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Agent Use Case Distribution</h2>", unsafe_allow_html=True)
    
    usecase_data = generate_mock_usecase_data()
    
    # Create pie chart for use case distribution
    usecase_chart = alt.Chart(usecase_data).mark_arc().encode(
        theta=alt.Theta('proportion:Q'),
        color=alt.Color('use_case:N', scale=alt.Scale(scheme='category10')),
        tooltip=['use_case:N', alt.Tooltip('proportion:Q', format='.1%')]
    ).properties(
        height=400
    )
    
    # Add text labels
    text = alt.Chart(usecase_data).mark_text(radiusOffset=15).encode(
        theta=alt.Theta('proportion:Q', stack=True),
        radius=alt.value(100),
        text=alt.Text('use_case:N')
    )
    
    st.altair_chart(usecase_chart + text, use_container_width=True)
    
    # Features section
    st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Key Features</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3 style='color: #4e6ef2;'>On-Chain AI Processing</h3>
            <p>Submit AI tasks on Gnosis Chain and get verifiable results delivered directly to you</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3 style='color: #4e6ef2;'>Web2 & Web3 Integration</h3>
            <p>Seamless login with email or social accounts, with embedded wallet creation for all users</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3 style='color: #4e6ef2;'>Multi-Agent Execution</h3>
            <p>Complex tasks are broken down and executed by specialized AI agents for optimal results</p>
        </div>
        """, unsafe_allow_html=True)

def display_email_login_page():
    """Display the Privy email login page"""
    st.markdown("""
    <div class="title-container">
        <img src="https://autonolas.network/images/logos/olas-logo.svg" class="logo-image" alt="OLAS Logo">
        <h1>Log in to OLAS MCP Platform</h1>
        <p>Enter your email to receive a one-time verification code</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a container for the login form
    login_container = st.container()
    
    with login_container:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # Email input form
        email = st.text_input("Email", key="email_input", placeholder="Enter your email address")
        
        if st.button("Continue", key="email_submit", use_container_width=True):
            if email:
                with st.spinner("Sending verification code..."):
                    try:
                        # Check if user exists
                        user_check = privy_api.get_user_by_email(email)
                        
                        # Create verification code
                        verification_response = privy_api.create_verification_code(email)
                        
                        if "error" in verification_response:
                            st.error(f"Failed to send verification code: {verification_response['error']}")
                        else:
                            st.success("Verification code sent! Check your email.")
                            st.session_state.login_email = email
                            st.session_state.page = "verify"
                            st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter your email address")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Back button
        if st.button("← Back to Home", key="back_to_home"):
            st.session_state.page = "landing"
            st.rerun()

def display_verification_page():
    """Display the verification code input page"""
    st.markdown("""
    <div class="title-container">
        <img src="https://autonolas.network/images/logos/olas-logo.svg" class="logo-image" alt="OLAS Logo">
        <h1>Verify Your Email</h1>
        <p>Enter the verification code sent to {}</p>
    </div>
    """.format(st.session_state.login_email), unsafe_allow_html=True)
    
    # Create a container for the verification form
    verify_container = st.container()
    
    with verify_container:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # Verification code input
        verification_code = st.text_input(
            "Verification Code", 
            key="verification_code_input",
            max_chars=6,
            placeholder="Enter 6-digit code"
        )
        
        if st.button("Verify", key="verify_submit", use_container_width=True):
            if verification_code:
                with st.spinner("Verifying code..."):
                    try:
                        # Verify the code
                        verification_result = privy_api.verify_code(
                            st.session_state.login_email, 
                            verification_code
                        )
                        
                        if "error" in verification_result:
                            st.error(f"Verification failed: {verification_result['error']}")
                        else:
                            # Code is valid, check if user exists or create one
                            try:
                                user_data = privy_api.get_user_by_email(st.session_state.login_email)
                                if "error" in user_data or not user_data.get("id"):
                                    # Need to create user
                                    user_data = privy_api.create_user(st.session_state.login_email)
                            except:
                                # User doesn't exist, create one
                                user_data = privy_api.create_user(st.session_state.login_email)
                            
                            if "error" in user_data:
                                st.error(f"Failed to access user account: {user_data['error']}")
                                return
                            
                            # Get user ID
                            user_id = user_data.get("id")
                            
                            # Check if user has a wallet
                            wallet_data = privy_api.get_user_wallets(user_id)
                            
                            wallet_address = None
                            if "linked_accounts" in wallet_data and wallet_data["linked_accounts"]:
                                for account in wallet_data["linked_accounts"]:
                                    if account.get("type") == "wallet":
                                        wallet_address = account.get("address")
                                        break
                            
                            # If no wallet, create one
                            if not wallet_address:
                                # For demo purposes, we'll generate a mock wallet address
                                # In a production app, you'd use privy_api.create_embedded_wallet(user_id)
                                wallet_address = generate_eth_address(st.session_state.login_email)
                            
                            # Store user info in session state
                            st.session_state.authenticated = True
                            st.session_state.account_info = {
                                "user_id": user_id,
                                "email": st.session_state.login_email,
                                "wallet_address": wallet_address
                            }
                            
                            # Create or get user in Supabase
                            try:
                                supabase_user = supabase_client.create_or_get_user(
                                    privy_user_id=user_id,
                                    email=st.session_state.login_email,
                                    wallet_address=wallet_address
                                )
                            except Exception as e:
                                st.warning(f"Could not create Supabase user: {e}")
                            
                            # Success - save session state and redirect
                            save_session_state_if_authenticated()
                            st.session_state.page = "dashboard"
                            st.success("Verification successful! Redirecting to dashboard...")
                            st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter the verification code")
        
        # Resend code
        if st.button("Resend Code", key="resend_code", use_container_width=False):
            with st.spinner("Sending new verification code..."):
                try:
                    verification_response = privy_api.create_verification_code(st.session_state.login_email)
                    if "error" in verification_response:
                        st.error(f"Failed to resend verification code: {verification_response['error']}")
                    else:
                        st.success("New verification code sent!")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Back button
        if st.button("← Change Email", key="back_to_login"):
            st.session_state.page = "login"
            st.rerun()

def display_dashboard():
    """Display the app dashboard with user information"""
    # Import the app.py dashboard code
    import app
    
    # Display user information in header
    if st.session_state.authenticated and 'account_info' in st.session_state:
        account_info = st.session_state.account_info
        address = account_info.get('wallet_address', '')
        display_address = format_eth_address(address)
        
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
    
    # Run the app's main function
    app.app_home()
    
    # Add a logout button
    if st.sidebar.button("Logout", key="dashboard_logout"):
        st.session_state.authenticated = False
        st.session_state.account_info = None
        st.session_state.page = "landing"
        st.rerun()

def main():
    """Main function to run the application"""
    # Initialize session state
    initialize_session_state()
    
    # Determine which page to show
    if st.session_state.page == "landing":
        display_landing_page()
    elif st.session_state.page == "login":
        display_email_login_page()
    elif st.session_state.page == "verify":
        display_verification_page()
    elif st.session_state.page == "dashboard":
        if st.session_state.authenticated:
            display_dashboard()
        else:
            st.session_state.page = "landing"
            st.rerun()
    else:
        st.error(f"Unknown page: {st.session_state.page}")
        st.session_state.page = "landing"
        st.rerun()

if __name__ == "__main__":
    main()

import streamlit as st
import os
from dotenv import load_dotenv
from components.privy_auth import create_privy_auth
from utils.privy_utils import format_address

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="OLAS MCP - Web2 Login",
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
    .css-1v3fvcr {
        background-color: #f8f9fa;
    }
    .st-bk {
        color: #4e6ef2;
    }
    .auth-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    .title-container {
        text-align: center;
        margin-bottom: 30px;
    }
    .logo-image {
        max-width: 200px;
        margin-bottom: 20px;
    }
    .wallet-info {
        margin-top: 20px;
        padding: 15px;
        background-color: #f0f7ff;
        border-radius: 5px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def on_user_login(user_data):
    """Handle user login events."""
    st.session_state.wallet_address = user_data.get("address")
    
    # You can add additional logic here, such as:
    # - Creating a database record for new users
    # - Setting up permissions
    # - Initializing user-specific resources
    
    st.experimental_rerun()

def main():
    # Title and logo
    st.markdown("""
    <div class="title-container">
        <img src="https://autonolas.network/images/logos/olas-logo.svg" class="logo-image" alt="OLAS Logo">
        <h1>OLAS MCP Platform</h1>
        <p>Connect with your email or social account to use the OLAS MCP platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a container for the auth component
    auth_container = st.container()
    
    with auth_container:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # Initialize Privy Auth component
        privy_app_id = os.getenv("PRIVY_APP_ID")
        auth = create_privy_auth(privy_app_id=privy_app_id, on_login=on_user_login)
        
        # Display the login UI
        auth_result = auth.login_ui(height=500)
        
        # Display wallet information if authenticated
        if auth.is_authenticated:
            st.markdown(f"""
            <div class="wallet-info">
                <h3>🎉 Successfully Connected!</h3>
                <p><strong>Your Gnosis Chain Address:</strong> {format_address(auth.user_address)}</p>
                <p>You can now use the OLAS MCP platform with your wallet.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add button to continue to the app
            if st.button("Continue to OLAS MCP Platform", type="primary"):
                # Here you would typically redirect to the main app or load the main interface
                st.session_state.authenticated = True
                st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # If the user is authenticated and has clicked the continue button
    if st.session_state.get("authenticated", False):
        # Clear the authentication container and show the app
        auth_container.empty()
        
        st.header("OLAS MCP Platform")
        st.subheader(f"Welcome, {format_address(auth.user_address)}")
        
        # Here you would include your app's functionality
        st.write("You are now logged in. This is where the main app functionality would go.")
        
        # Add a logout button
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()

if __name__ == "__main__":
    main()

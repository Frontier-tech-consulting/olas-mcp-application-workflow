import streamlit as st
import hashlib
from src.utils.privy_rest_api import PrivyRestAPI

# Get Privy API instance
try:
    privy_api = PrivyRestAPI()
except Exception as e:
    print(f"Error initializing Privy API: {e}")
    privy_api = None

def generate_eth_address(seed):
    """Generate a mock Ethereum address from a seed string"""
    # Create a hash from the seed to generate a deterministic but random-looking result
    h = hashlib.sha256(seed.encode()).hexdigest()
    # Ethereum addresses are 40 hex chars (20 bytes) prefixed with 0x
    return f"0x{h[:40]}"

def format_eth_address(address):
    """Format an Ethereum address for display with ellipsis in the middle"""
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"

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

def display_verification_page(supabase_client, save_session_state_callback):
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
                                "wallet_address": wallet_address,
                                "display_address": format_eth_address(wallet_address)
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
                            save_session_state_callback()
                            st.session_state.page = "create_request"
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



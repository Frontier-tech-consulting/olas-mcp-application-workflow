import os
import streamlit as st
import requests
from typing import Dict, Any
import base64
import time
import jwt
from jwt import PyJWKClient
from eth_account import Account
import sys

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.supabase_utils import SupabaseClient
from models import PrivyUser

# JWKS URL template for Privy App
JWKS_URL_TEMPLATE = "https://auth.privy.io/api/v1/apps/{app_id}/jwks.json"

# Function to verify JWT using JWKS
def verify_jwt(token: str, app_id: str) -> Dict[str, Any]:
    """
    Verify a JWT using the JWKS endpoint.

    Args:
        token (str): The JWT to verify.
        app_id (str): The Privy app ID.

    Returns:
        Dict[str, Any]: Decoded token payload if verification is successful.
    """
    try:
        jwks_url = JWKS_URL_TEMPLATE.format(app_id=app_id)
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=app_id,
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        st.error("Token has expired.")
        return {"error": "Token expired"}
    except jwt.InvalidTokenError as e:
        st.error(f"Invalid token: {e}")
        return {"error": "Invalid token"}

# Function to authenticate and generate a secret
def authenticate_and_generate_secret(email: str, password: str, app_id: str) -> str:
    """
    Authenticate the user and generate a secret for API calls.

    Args:
        email (str): User's email.
        password (str): User's password.
        app_id (str): The Privy app ID.

    Returns:
        str: Generated secret for API calls.
    """
    # Simulate authentication and secret generation (replace with actual API call)
    # In a real implementation, you would call the Privy API to authenticate the user
    # and generate a secret.
    return f"secret_for_{email}"

# Streamlit component for user login and wallet creation
def wallet_component():
    """
    Streamlit UI for user login and wallet creation using Privy API.

    Returns:
        Dict[str, Any]: User authentication and wallet details.
    """
    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        return {
            "authenticated": True,
            "wallet_address": st.session_state.get('wallet_address'),
            "user_id": st.session_state.get('user_id')
        }

    st.markdown("""
    <div style="text-align: center;">
        <h3>Login to Your Account</h3>
        <p>Use your email and password to log in and create your smart account wallet.</p>
    </div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login and Create Wallet"):
        if email and password:
            app_id = os.getenv("PRIVY_APP_ID")
            supabase = SupabaseClient()

            # Step 1: Authenticate with Privy
            try:
                # In a real implementation, you would use the Privy API to authenticate
                # For now, we'll simulate authentication
                privy_user_id = f"privy_{int(time.time())}"
                
                # Step 2: Generate wallet address using eth_account
                account = Account.create()  # Create a new Ethereum account
                wallet_address = account.address
                
                # Step 3: Create or get user in Supabase
                supabase_user = supabase.create_or_get_user(
                    privy_user_id=privy_user_id,
                    email=email,
                    wallet_address=wallet_address
                )
                
                # Create PrivyUser object
                privy_user = PrivyUser(
                    user_id=supabase_user.get("id", ""),
                    privy_user_id=privy_user_id,
                    address=wallet_address,
                    email=email,
                    name=None,  # Could be added later
                    linked_accounts=[]
                )
                
                # Store all necessary information in session state
                st.session_state.authenticated = True
                st.session_state.wallet_address = wallet_address
                st.session_state.user_id = supabase_user.get("id", "")
                st.session_state.privy_user = privy_user
                st.session_state.account_info = {
                    "address": wallet_address,
                    "account_obj": account,
                    "safe_address": None,  # Will be set later if needed
                    "privy_user": privy_user
                }
                
                # Set the page to create_request
                st.session_state.page = 'create_request'

                # Show success message
                st.success(f"Successfully logged in! Wallet address: {wallet_address}")
                
                # Rerun to update the UI
                st.rerun()

                return {
                    "authenticated": True,
                    "wallet_address": wallet_address,
                    "user_id": supabase_user.get("id", "")
                }
                
            except Exception as e:
                st.error(f"Authentication failed: {e}")
                return {"authenticated": False}
        else:
            st.warning("Please enter your email and password.")

    return {"authenticated": False}
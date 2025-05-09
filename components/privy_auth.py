import os
import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, Optional, Callable, List
import uuid
import json
import sys

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models import PrivyUser
from .privy_auth_component import privy_auth_component
from utils.supabase_utils import SupabaseClient

def format_address(address: str) -> str:
    """
    Format an Ethereum address for display (e.g., 0x1234...5678).
    
    Args:
        address: The full Ethereum address
        
    Returns:
        Shortened display version of the address
    """
    if not address or not isinstance(address, str) or not address.startswith("0x"):
        return address or ""
    
    return f"{address[:6]}...{address[-4:]}"

# Define the component once with a fixed name and path
# This follows Streamlit custom component guidelines
COMPONENT_NAME = "privy_auth"
COMPONENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "privy_iframe.html")

class PrivyAuth:
    """Streamlit component for Privy authentication."""
    
    def __init__(self, privy_app_id: str = None, on_login: Optional[Callable] = None):
        """
        Initialize the Privy authentication component.
        
        Args:
            privy_app_id: Your Privy app ID from the Privy dashboard (or from env var)
            on_login: Callback function to execute when user logs in
        """
        self.privy_app_id = privy_app_id or os.environ.get("PRIVY_APP_ID")
        self.on_login = on_login
        self.supabase = SupabaseClient()
        
        if not self.privy_app_id:
            raise ValueError("Privy App ID must be provided either through constructor or PRIVY_APP_ID environment variable")
        
        # Initialize the auth history in session state if it doesn't exist
        if 'auth_history' not in st.session_state:
            st.session_state.auth_history = []
    
    def login_ui(self, key: str = None, height: int = 500) -> Dict[str, Any]:
        """
        Display the Privy login UI using Streamlit custom component approach
        
        Args:
            key: Optional key for the component
            height: Height of the component in pixels
            
        Returns:
            Dict containing authentication status and user info when logged in
        """
        component_key = key or f"privy_auth_{str(uuid.uuid4())[:8]}"
        
        # Create the component interface
        interface = {
            "privy_app_id": self.privy_app_id,
            "config": {
                "loginMethods": ["email", "google", "twitter", "discord"],
                "appearance": {
                    "theme": "light",
                    "accentColor": "#4e6ef2",
                    "logo": "https://autonolas.network/images/logos/olas-logo.svg",
                    "button": {
                        "borderRadius": "8px",
                        "fontSize": "16px",
                        "fontWeight": "bold",
                        "padding": "12px 20px",
                    }
                },
                "embeddedWallets": {
                    "createOnLogin": "all-users",
                    "noPromptOnSignature": True
                },
                "defaultChain": {
                    "id": 100,
                    "name": "Gnosis Chain",
                    "rpcUrl": "https://rpc.gnosischain.com"
                }
            }
        }
        
        # Use the React-based component
        with st.container():
            result = privy_auth_component(interface=interface, height=height)
        
        # Set up message passing for component
        if f"{component_key}_callback" not in st.session_state:
            def handle_auth_result(result):
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        result = {"authenticated": False}
                
                st.session_state[f"{component_key}_result"] = result
                
                # Store authentication history and handle Supabase integration
                if result.get("authenticated", False) and result.get("address"):
                    # Create or get user in Supabase
                    try:
                        supabase_user = self.supabase.create_or_get_user(
                            privy_user_id=result.get("userId", ""),
                            email=result.get("email", ""),
                            wallet_address=result.get("address", "")
                        )
                        
                        # Create PrivyUser object with Supabase user ID
                        privy_user = PrivyUser(
                            user_id=supabase_user.get("id", ""),  # Use Supabase user ID
                            privy_user_id=result.get("userId", ""),  # Store Privy user ID separately
                            address=result.get("address", ""),
                            email=result.get("email"),
                            name=result.get("name"),
                            linked_accounts=result.get("linkedAccounts", [])
                        )
                        
                        # Add to auth history
                        if 'auth_history' in st.session_state:
                            st.session_state.auth_history.append({
                                "timestamp": st.session_state.get("_last_auth_time", ""),
                                "user": privy_user
                            })
                            
                        # Update session state with user info
                        st.session_state.privy_user = privy_user
                        st.session_state.authenticated = True
                        
                    except Exception as e:
                        st.error(f"Error creating user: {e}")
                        result["authenticated"] = False
            
            st.session_state[f"{component_key}_callback"] = handle_auth_result
        
        # Handle callback if an on_login function was provided
        result = st.session_state.get(f"{component_key}_result", {"authenticated": False})
        if self.on_login and result.get("authenticated") and result.get("continueToApp", False):
            self.on_login(result)
        
        return result
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated through Privy."""
        if hasattr(st, 'session_state') and 'account_info' in st.session_state:
            return bool(st.session_state.account_info)
        return False
    
    @property
    def user_address(self) -> Optional[str]:
        """Get the authenticated user's wallet address."""
        if hasattr(st, 'session_state') and 'account_info' in st.session_state:
            return st.session_state.account_info.get('address')
        return None
    
    @property
    def auth_history(self) -> List[Dict[str, Any]]:
        """Get the authentication history."""
        return st.session_state.get('auth_history', [])
    
    def logout(self):
        """Log out the current user."""
        if hasattr(st, 'session_state'):
            # Clear session state
            keys_to_clear = ['account_info', 'authenticated', 'privy_user', 'auth_history']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Rerun to update UI
            st.rerun()
        
def create_privy_auth(privy_app_id: str = None, on_login: Optional[Callable] = None) -> PrivyAuth:
    """
    Create a new PrivyAuth instance.
    
    Args:
        privy_app_id: Your Privy app ID
        on_login: Callback function to execute when user logs in
        
    Returns:
        PrivyAuth instance
    """
    return PrivyAuth(privy_app_id=privy_app_id, on_login=on_login)

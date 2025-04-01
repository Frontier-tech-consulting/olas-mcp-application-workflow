import os
import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, Optional, Callable, List
import uuid
import json
from models import PrivyUser

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
        
        if not self.privy_app_id:
            raise ValueError("Privy App ID must be provided either through constructor or PRIVY_APP_ID environment variable")
        
        # Initialize the auth history in session state if it doesn't exist
        if 'auth_history' not in st.session_state:
            st.session_state.auth_history = []
    
    def login_ui(self, key: str = None, height: int = 400) -> Dict[str, Any]:
        """
        Display the Privy login UI using Streamlit custom component approach
        
        Args:
            key: Optional key for the component
            height: Height of the component in pixels
            
        Returns:
            Dict containing authentication status and user info when logged in
        """
        component_key = key or f"privy_auth_{str(uuid.uuid4())[:8]}"
        
        # Use components.iframe to properly load the HTML page
        # This is more in line with Streamlit custom component guidelines
        url = f"file://{COMPONENT_PATH}?appId={self.privy_app_id}&key={component_key}"
        
        # For production/cloud environments where file:// URLs won't work,
        # we'll use the HTML approach as a fallback
        try:
            components.iframe(url, height=height, scrolling=False)
        except Exception:
            # Fallback to HTML method
            html_content = f"""
            <iframe
                src="about:blank"
                height="{height}px"
                width="100%"
                frameBorder="0"
                id="privy-frame"
            ></iframe>
            <script>
            (function() {{
                // We'll dynamically create the HTML content for the iframe
                const iframe = document.getElementById('privy-frame');
                const doc = iframe.contentWindow.document;
                
                // Write the HTML content
                doc.open();
                doc.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>OLAS Privy Login</title>
                    <style>
                        body {{
                            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            margin: 0;
                            padding: 0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                        }}
                        .auth-container {{
                            max-width: 400px;
                            width: 100%;
                            padding: 20px;
                            box-sizing: border-box;
                        }}
                        .olas-logo {{
                            display: block;
                            width: 120px;
                            margin: 0 auto 20px;
                        }}
                        .title {{
                            text-align: center;
                            color: #4e6ef2;
                            margin-bottom: 20px;
                        }}
                        .wallet-info {{
                            margin-top: 20px;
                            padding: 15px;
                            background-color: #f0f7ff;
                            border-radius: 8px;
                            text-align: center;
                            display: none;
                        }}
                        .continue-button {{
                            display: block;
                            width: 100%;
                            padding: 10px;
                            margin-top: 10px;
                            background-color: #4e6ef2;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            font-weight: bold;
                            cursor: pointer;
                            transition: background-color 0.2s;
                        }}
                        .continue-button:hover {{
                            background-color: #3d5ce0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="auth-container">
                        <img src="https://autonolas.network/images/logos/olas-logo.svg" alt="OLAS Logo" class="olas-logo">
                        <h2 class="title">Connect to OLAS MCP</h2>
                        
                        <div id="privy-container"></div>
                        
                        <div id="wallet-info" class="wallet-info">
                            <p><strong>Connected Address:</strong> <span id="wallet-address"></span></p>
                            <button id="continue-button" class="continue-button">Continue to OLAS MCP</button>
                        </div>
                    </div>

                    <script src="https://cdn.jsdelivr.net/npm/@privy-io/privy-browser@0.0.1/dist/privy.js"></script>
                    <script>
                        // Initialize Privy
                        const privy = new Privy({{
                            appId: '{self.privy_app_id}',
                            config: {{
                                loginMethods: ['email', 'google', 'twitter', 'discord'],
                                appearance: {{
                                    theme: 'light',
                                    accentColor: '#4e6ef2',
                                    logo: 'https://autonolas.network/images/logos/olas-logo.svg',
                                    button: {{
                                        borderRadius: '8px',
                                        fontSize: '16px',
                                        fontWeight: 'bold',
                                        padding: '12px 20px',
                                    }}
                                }},
                                embeddedWallets: {{
                                    createOnLogin: 'all-users',
                                    noPromptOnSignature: true
                                }},
                                defaultChain: {{
                                    id: 100,
                                    name: 'Gnosis Chain',
                                    rpcUrl: 'https://rpc.gnosischain.com'
                                }}
                            }},
                            onLogin: async (user) => {{
                                try {{
                                    // Get user's wallet
                                    const embeddedWallet = user.linkedAccounts.find(
                                        account => account.type === 'wallet' && account.walletClientType === 'privy'
                                    );
                                    
                                    if (embeddedWallet && embeddedWallet.address) {{
                                        // Display wallet info
                                        document.getElementById('wallet-info').style.display = 'block';
                                        document.getElementById('wallet-address').textContent = embeddedWallet.address;
                                        
                                        // Send data to parent
                                        window.parent.parent.postMessage({{
                                            from: 'privy',
                                            type: 'AUTH_SUCCESS',
                                            payload: {{
                                                address: embeddedWallet.address,
                                                userId: user.id,
                                                authenticated: true,
                                                email: user.email?.address || null,
                                                name: user.name || null,
                                                linkedAccounts: user.linkedAccounts || []
                                            }}
                                        }}, '*');
                                    }}
                                }} catch (error) {{
                                    console.error("Error in onLogin:", error);
                                }}
                            }},
                            onLogout: () => {{
                                document.getElementById('wallet-info').style.display = 'none';
                                document.getElementById('wallet-address').textContent = '';
                                
                                // Send logout to parent
                                window.parent.parent.postMessage({{
                                    from: 'privy',
                                    type: 'AUTH_SUCCESS',
                                    payload: {{
                                        authenticated: false
                                    }}
                                }}, '*');
                            }}
                        }});
                        
                        // Mount the login UI
                        privy.mountLogin(document.getElementById('privy-container'));
                        
                        // Set up continue button
                        document.getElementById('continue-button').addEventListener('click', () => {{
                            const address = document.getElementById('wallet-address').textContent;
                            
                            window.parent.parent.postMessage({{
                                from: 'privy',
                                type: 'AUTH_SUCCESS',
                                payload: {{
                                    address: address,
                                    authenticated: true,
                                    continueToApp: true
                                }}
                            }}, '*');
                        }});
                    </script>
                </body>
                </html>
                `);
                doc.close();
                
                // Set up the message listener to receive messages from the iframe
                window.addEventListener('message', function(e) {{
                    if (e.data && e.data.from === 'privy' && e.data.type === 'AUTH_SUCCESS') {{
                        const data = {{
                            type: "streamlit:setComponentValue",
                            value: JSON.stringify(e.data.payload)
                        }};
                        window.parent.postMessage(data, "*");
                    }}
                }}, false);
            }})();
            </script>
            """
            components.html(html_content, height=height, scrolling=False)
        
        # Initialize session state if needed
        if f"{component_key}_result" not in st.session_state:
            st.session_state[f"{component_key}_result"] = {"authenticated": False}
        
        # Set up message passing for component
        if f"{component_key}_callback" not in st.session_state:
            def handle_auth_result(result):
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        result = {"authenticated": False}
                
                st.session_state[f"{component_key}_result"] = result
                
                # Store authentication history
                if result.get("authenticated", False) and result.get("address"):
                    privy_user = PrivyUser(
                        user_id=result.get("userId", ""),
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

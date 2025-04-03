import streamlit as st
import streamlit.components.v1 as components
import json
import os

def privy_auth_component(interface, height=600):
    """
    Streamlit component for Privy authentication that integrates with the React AuthDemo component.
    
    Args:
        interface: Dictionary containing Privy configuration
        height: Height of the component in pixels
    """
    # Get the path to the React component
    docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    
    # Create the HTML content that will load the React component
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OLAS Privy Login</title>
        <script src="https://cdn.jsdelivr.net/npm/@privy-io/privy-browser@0.0.1/dist/privy.js"></script>
        <script src="/_next/static/chunks/main.js"></script>
        <link rel="stylesheet" href="/_next/static/css/app.css">
        <style>
            body {{
                font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background-color: #f8f9fa;
            }}
            #__next {{
                width: 100%;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            .auth-container {{
                max-width: 400px;
                width: 100%;
                margin: 0 auto;
                padding: 20px;
                box-sizing: border-box;
            }}
        </style>
    </head>
    <body>
        <div id="__next">
            <div id="privy-auth-root"></div>
        </div>

        <script>
        // Initialize Privy with the provided configuration
        const privyConfig = {{
            appId: '{interface['privy_app_id']}',
            config: {json.dumps(interface['config'])},
            onLogin: async (user) => {{
                try {{
                    const embeddedWallet = user.linkedAccounts.find(
                        account => account.type === 'wallet' && account.walletClientType === 'privy'
                    );
                    
                    if (embeddedWallet && embeddedWallet.address) {{
                        window.parent.postMessage({{
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
                window.parent.postMessage({{
                    from: 'privy',
                    type: 'AUTH_SUCCESS',
                    payload: {{
                        authenticated: false
                    }}
                }}, '*');
            }}
        }};

        // Load and initialize the React component
        window.addEventListener('load', () => {{
            const root = document.getElementById('privy-auth-root');
            if (root) {{
                // Initialize the React component with Privy config
                window.__NEXT_DATA__.props.pageProps.privyConfig = privyConfig;
                window.__NEXT_DATA__.props.pageProps.onAuthSuccess = (user) => {{
                    window.parent.postMessage({{
                        from: 'privy',
                        type: 'AUTH_SUCCESS',
                        payload: {{
                            address: user.address,
                            userId: user.id,
                            authenticated: true,
                            email: user.email,
                            name: user.name,
                            linkedAccounts: user.linkedAccounts
                        }}
                    }}, '*');
                }};
            }}
        }});
        </script>
    </body>
    </html>
    """
    
    # Use Streamlit's components.html to render the component
    return components.html(html_content, height=height)
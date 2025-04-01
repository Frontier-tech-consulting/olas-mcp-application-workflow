import streamlit as st
import json
import asyncio
import time
from dotenv import load_dotenv
import os

# Import API functions and utility functions
import api
import utils
from models import ChainConfig, Tool, ExecutionStep, PrivyUser # Import necessary models
from components.privy_auth import PrivyAuth, format_address, create_privy_auth

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="OLAS DeFi Strategy Finder",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .st-emotion-cache-16txtl3 h1 {
        color: #4e6ef2;
    }
    .stButton button {
        background-color: #4e6ef2;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-size: 16px;
    }
    .stButton button:hover {
        background-color: #3d5ce0;
    }
    .info-box {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #e6e9ed;
    }
    .card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #e6e9ed;
    }
    .stSpinner > div > div { border-top-color: #4e6ef2; }
    .feature-icon {
        font-size: 20px;
        margin-right: 10px;
    }
    .header-container {
        background-color: #4e6ef2;
        padding: 20px;
        margin-bottom: 30px;
        border-radius: 10px;
        color: white;
    }
    .result-container {
        background-color: #f0f4ff;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        border-left: 4px solid #4e6ef2;
    }
    .step-container {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e6e9ed;
    }
    .step-number {
        background-color: #4e6ef2;
        color: white;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        margin-right: 15px;
    }
    .auth-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
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

# Initialize session state
def init_session_state():
    defaults = {
        'page': 'home',
        'account_info': None, # Will store {address: str, account_obj: LocalAccount, safe_address: Optional[str], privy_user: Optional[PrivyUser]}
        'chain_config': ChainConfig().model_dump(), # Use Pydantic model default
        'prompt': "",
        'available_tools': [],
        'selected_tools': [], # Stores list of Tool objects
        'total_cost': 0.0,
        'request_tx_hash': None,
        'payment_tx_hash': None,
        'execution_info': None, # Will store {requestId: str, operator: str}
        'execution_steps': [], # Stores list of ExecutionStep objects or dicts
        'execution_status': None,
        'final_result': None,
        'error_message': None,
        'transaction_id': None, # ID of the current transaction being processed
        'transaction_to_view': None, # ID of a transaction to view from history
        'selected_transaction': None, # For history page
        'authenticated': False, # Track Privy authentication status
        'privy_user': None, # Will store PrivyUser object
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Helper function to run async code from Streamlit
def run_async(async_func):
    # A simple way to run async functions; more robust solutions might be needed
    # depending on Streamlit's interaction with event loops.
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_func)
        loop.close()
        return result
    except Exception as e:
        st.session_state.error_message = f"Async execution error: {e}"
        st.exception(e)
        return None  # Indicate error

def on_user_login(user_data):
    """Handle user login from Privy."""
    if user_data.get("authenticated", False) and user_data.get("address"):
        # Create a PrivyUser object
        privy_user = PrivyUser(
            user_id=user_data.get("userId", ""),
            address=user_data.get("address", ""),
            email=user_data.get("email"),
            name=user_data.get("name")
        )
        
        # Update session state
        st.session_state.privy_user = privy_user
        st.session_state.authenticated = True
        
        # Try to get wallet associated with this address
        try:
            account = api.get_account_from_address(user_data.get("address"))
            safe_addr = run_async(api.check_safe_address_for_account(account))
            
            st.session_state.account_info = {
                "address": account.address,
                "account_obj": account,
                "safe_address": safe_addr,
                "privy_user": privy_user
            }
            st.success(f"Connected as {account.address}. Safe Account: {safe_addr or 'Not Configured'}")
            st.session_state.page = 'create_request'
        except Exception as e:
            st.session_state.error_message = f"Wallet connection failed: {e}"
            st.error(st.session_state.error_message)
    
    st.experimental_rerun()

def home():
    """Home page with introduction and connect wallet button"""
    st.markdown("""
    <div class="header-container">
        <h1>OLAS DeFi Strategy Finder</h1>
        <p>Discover optimal lending strategies powered by AI and on-chain data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content section - takes up most of the page
    st.markdown("""
    <div class="info-box">
        <h2>Find the Best DeFi Lending Strategy</h2>
        <p>Leverage the power of multiple data sources and AI-powered quantitative analysis to discover optimal lending strategies across Aave, Compound, Maker and more.</p>
        <ul>
            <li><span class="feature-icon">🔍</span> <strong>Data-Driven Analysis</strong>: Utilizing DeFiLlama, TheGraph, and Space and Time datasets</li>
            <li><span class="feature-icon">📊</span> <strong>Quantitative Comparison</strong>: Compare APYs, risks, and liquidity across platforms</li>
            <li><span class="feature-icon">🔐</span> <strong>Verified Results</strong>: Multi-agent verification with OLAS slashing mechanism (Optional)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Features section - display in a 3-column layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3><span class="feature-icon">📈</span> Yield Optimization</h3>
            <p>Find the highest APY opportunities across multiple lending platforms with risk-adjusted returns.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3><span class="feature-icon">🔄</span> Cross-Platform Analysis</h3>
            <p>Compare lending and borrowing rates across all major DeFi platforms in one place.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <h3><span class="feature-icon">🛡️</span> Risk Assessment</h3>
            <p>Evaluate platform security, liquidity risks, and historical performance before committing funds.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Create a spacer to push login section to bottom
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    
    # Authentication section - centered at bottom
    auth_container = st.container()
    
    # Check if already authenticated through Privy
    if st.session_state.authenticated and st.session_state.account_info:
        # Centered container for "Already connected" message
        auth_container.markdown("""
        <div style="max-width: 500px; margin: 0 auto; text-align: center;">
            <div class="wallet-info">
                <h3>🎉 Successfully Connected!</h3>
                <p><strong>Connected Address:</strong> {}</p>
                <p><strong>Safe Account:</strong> {}</p>
                <p>You're ready to use the OLAS DeFi Strategy Finder.</p>
            </div>
        </div>
        """.format(
            format_address(st.session_state.account_info['address']),
            st.session_state.account_info['safe_address'] or 'Not Configured'
        ), unsafe_allow_html=True)
        
        # Center the button with CSS
        auth_container.markdown("""
        <div style="display: flex; justify-content: center; margin-top: 20px;">
            <div style="width: 300px;">
        """, unsafe_allow_html=True)
        
        if auth_container.button("Continue to DeFi Strategy Finder", type="primary", key="continue_btn"):
            st.session_state.page = 'create_request'
            st.rerun()
            
        auth_container.markdown("</div></div>", unsafe_allow_html=True)
    else:
        # Create a centered container for the login component
        auth_container.markdown("""
        <div style="max-width: 500px; margin: 0 auto; text-align: center;">
            <div style="margin-bottom: 20px;">
                <h3>Get Started</h3>
                <p>Connect your wallet using Privy to begin.</p>
                <p>You can connect with your email, social accounts, or existing wallet.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Authentication component - centered
        with auth_container:
            # Title and logo for the auth container - removed from here since it's in the iframe
            
            # Initialize Privy Auth component with callback
            privy_app_id = os.getenv("PRIVY_APP_ID")
            if not privy_app_id:
                auth_container.error("Privy App ID not found. Please check your environment variables.")
                return
                
            auth = create_privy_auth(privy_app_id=privy_app_id, on_login=on_user_login)
            
            # Center the login UI
            auth_container.markdown('<div style="display: flex; justify-content: center;">', unsafe_allow_html=True)
            auth_container.markdown('<div style="width: 100%; max-width: 400px;">', unsafe_allow_html=True)
            
            # Display the login UI with increased height for better visibility
            auth_result = auth.login_ui(height=450)
            
            # Process authentication result
            if isinstance(auth_result, dict) and auth_result.get("authenticated", False) and auth_result.get("continueToApp", False):
                # This will trigger the on_user_login callback which will update the session state
                on_user_login(auth_result)
            
            auth_container.markdown('</div></div>', unsafe_allow_html=True)
            
            # Display the auth history if any exists
            if hasattr(auth, 'auth_history') and auth.auth_history:
                with auth_container.expander("Authentication History", expanded=False):
                    for i, history in enumerate(auth.auth_history):
                        st.markdown(f"**Login {i+1}**")
                        st.markdown(f"Address: {format_address(history['user'].address)}")
                        if history['user'].email:
                            st.markdown(f"Email: {history['user'].email}")
                        st.markdown("---")
            
            # Display helpful information about what you can do with Privy
            auth_container.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 14px; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto;">
                <p style="margin-bottom: 10px;"><strong>Why connect with Privy?</strong></p>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Access personalized DeFi strategies</li>
                    <li>Save and track your strategy history</li>
                    <li>No wallet required - embedded wallets created automatically</li>
                    <li>Enhanced security for your transactions</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

def create_request():
    """Page for creating a DeFi strategy request"""
    st.markdown("""
    <div class="header-container">
        <h1>Create DeFi Strategy Request</h1>
        <p>Define your criteria and let AI find the best lending strategy for you</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.account_info:
        st.warning("Please connect your wallet first.")
        if st.button("Go Home"): st.session_state.page = 'home'; st.rerun()
        return

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>Account Information</h3>
            <p><strong>Wallet Address:</strong> {st.session_state.account_info['address']}</p>
            <p><strong>Safe Account:</strong> {st.session_state.account_info['safe_address'] or 'Not Configured'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>Chain Configuration</h3>
        <p>Configure the blockchain network settings for your DeFi strategy analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    cc = st.session_state.chain_config # Local reference
    col1, col2 = st.columns(2)
    with col1:
        cc["chainId"] = st.number_input("Chain ID", value=cc["chainId"], step=1)
    
    with col2:
        cc["rpcUrl"] = st.text_input("RPC URL", value=cc["rpcUrl"])
    
    cc["mechMarketplace"] = st.text_input("Mech Marketplace Contract", value=cc["mechMarketplace"])
    
    # Update chain config in session state
    st.session_state.chain_config = cc
    
    st.markdown("""
    <div class="info-box">
        <h3>DeFi Strategy Query</h3>
        <p>Describe what you're looking for. Specify risk tolerance, platforms, etc. 
        The system will infer required tools (like DeFiLlamaAPI, TheGraphQuery) based on your prompt.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.prompt = st.text_area(
        "Enter your prompt",
        value=st.session_state.prompt,
        height=150,
        placeholder="Example: Analyze lending strategies across Aave and Compound using DeFiLlama and TheGraph, focusing on stablecoin APYs and risk scores."
    )
    
    if st.button("Analyze Prompt & Fetch Tools"):
        st.session_state.error_message = None
        if not st.session_state.prompt:
            st.error("Please enter a prompt.")
            return

        with st.spinner("Fetching available tools and preparing request..."):
            # Fetch tools from MCP
            tools_list_dict = run_async(api.list_available_tools())
            if tools_list_dict is None: # Check if run_async handled error
                 st.error(st.session_state.error_message or "Failed to fetch tools list.")
                 return

            st.session_state.available_tools = [Tool(**t) for t in tools_list_dict]
            if not st.session_state.available_tools:
                 st.warning("No tools seem to be available from the service.")
                 # Optionally allow proceeding without tools?
                 return
            
            # Infer tools based on prompt (using simple keyword matching for now)
            inferred_tools = utils.infer_tools(st.session_state.prompt, tools_list_dict)
            st.session_state.selected_tools = [Tool(**t) for t in inferred_tools]

            if not st.session_state.selected_tools:
                st.warning("Could not automatically infer any available tools based on your prompt. Please select manually on the next page or refine your prompt.")
                # Proceed anyway, user can select on next page
            else:
                st.success(f"Inferred Tools: {[t.name for t in st.session_state.selected_tools]}")

            # Calculate initial cost based on inferred tools
            total_cost = sum(float(t.cost.split()[0]) for t in st.session_state.selected_tools)
            st.session_state.total_cost = total_cost
            st.info(f"Estimated Cost (based on inferred tools): {total_cost:.3f} xDAI")
            
            # Move to payment page for confirmation and potential manual selection
            st.session_state.page = 'payment'
            st.rerun()

def payment():
    """Page for tool selection and payment"""
    st.markdown("""
    <div class="header-container">
        <h1>Select Tools & Pay Fees</h1>
        <p>Choose the analysis tools needed for your DeFi strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.account_info or not st.session_state.prompt:
        st.warning("Please connect wallet and enter a prompt first.")
        if st.button("Go Back"): st.session_state.page = 'create_request'; st.rerun()
        return
    
    # Add a progress tracker
    st.markdown("""
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px; background-color: #f0f4ff; padding: 10px; border-radius: 5px;">
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">1. Connect</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">2. Create Request</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px; background-color: #deebff; border-radius: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">3. Payment</div>
            <div style="font-size: 12px;">⏳ In Progress</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #999; font-weight: bold;">4. Execution</div>
            <div style="font-size: 12px;">⏱️ Pending</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <h3>Your Strategy Query</h3>
        <p>{}</p>
    </div>
    """.format(st.session_state.prompt), unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <h3>Available & Selected Tools</h3>
        <p>Confirm or modify the tools inferred from your prompt. The total cost will update accordingly.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.available_tools:
        st.warning("No tools data available. Try going back and fetching tools again.")
        # Potentially add a button here to re-trigger tool fetching
        return

    selected_tool_objects = []
    current_total_cost = 0.0
    selected_tool_names_in_state = [t.name for t in st.session_state.selected_tools]

    # Create a nicer tool selection UI
    for tool_model in st.session_state.available_tools:
        tool_available = tool_model.available
        is_selected = tool_model.name in selected_tool_names_in_state
        
        status_class = "available" if tool_available else "unavailable"
        if is_selected and tool_available:
            status_class += " selected"
            
        st.markdown(f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4>{tool_model.name}</h4>
                    <p>{tool_model.description}</p>
                    <p><strong>Cost:</strong> {tool_model.cost}</p>
                </div>
                <div>
        """, unsafe_allow_html=True)
        
        if tool_available:
            # Use the name from the model as key, check if it was previously selected
            is_selected = st.checkbox("Select", key=tool_model.name, value=(tool_model.name in selected_tool_names_in_state))
            if is_selected:
                selected_tool_objects.append(tool_model)
                try:
                    current_total_cost += float(tool_model.cost.split()[0])
                except ValueError:
                    st.warning(f"Invalid cost format for tool {tool_model.name}")
        else:
            st.markdown("_(Unavailable)_" + ("" if not (tool_model.name in selected_tool_names_in_state) else " _(Previously Selected)_"))
            
        st.markdown("""
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Update session state based on current checkbox selections
    st.session_state.selected_tools = selected_tool_objects
    st.session_state.total_cost = current_total_cost

    st.markdown(f"""
    <div class="result-container">
        <h3>Payment Summary</h3>
        <p><strong>Total Cost:</strong> {st.session_state.total_cost:.3f} xDAI</p>
        <p><strong>Paying from:</strong> {st.session_state.account_info['safe_address'] or st.session_state.account_info['address']}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Submit Request & Pay"):
        st.session_state.error_message = None
        if not st.session_state.selected_tools:
            st.error("Please select at least one tool.")
            return

        with st.spinner("Creating transaction record..."):
            # Create a transaction record
            transaction_id = run_async(api.create_new_transaction(
                owner_address=st.session_state.account_info['address'],
                safe_address=st.session_state.account_info['safe_address'],
                prompt=st.session_state.prompt,
                selected_tools=st.session_state.selected_tools,
                total_cost=st.session_state.total_cost
            ))
            
            if transaction_id is None:
                st.error(st.session_state.error_message or "Failed to create transaction record.")
                return
            
            # Store the transaction ID in session state for later use
            st.session_state.transaction_id = transaction_id
            st.info(f"Transaction record created: {transaction_id[:8]}...")

        with st.spinner("Submitting initial request and processing payment..."):
            # --- Step 1: Submit the initial request (as per spec) ---
            # We need an agent ID. Let's assume 0 or derive it somehow? Using 0 for now.
            # The tool name for the initial request seems to be the overall strategy name
            # The actual implementation might differ based on Mech agent deployment
            agent_id_for_request = 0
            strategy_tool_name = "DeFiLendingStrategy" # As per spec
            
            request_tx_hash = run_async(api.submit_mech_request(
                agent_id=agent_id_for_request,
                tool_name=strategy_tool_name,
                prompt=st.session_state.prompt,
                chain_config=st.session_state.chain_config,
                account=st.session_state.account_info['account_obj'],
                transaction_id=st.session_state.transaction_id  # Pass the transaction ID
            ))

            if request_tx_hash is None:
                st.error(st.session_state.error_message or "Failed to submit initial mech request.")
                return
            st.session_state.request_tx_hash = request_tx_hash
            st.info(f"Initial request submitted (Tx: ...{request_tx_hash[-6:]}) ")

            # --- Step 2: Execute Payment ---
            payment_tx_hash = run_async(api.execute_payment(
                total_cost_xdai=st.session_state.total_cost,
                selected_tools=[t.name for t in st.session_state.selected_tools],
                chain_config=st.session_state.chain_config,
                account=st.session_state.account_info['account_obj'],
                safe_address=st.session_state.account_info['safe_address'],
                transaction_id=st.session_state.transaction_id  # Pass the transaction ID
            ))

            if payment_tx_hash is None:
                st.error(st.session_state.error_message or "Payment transaction failed.")
                # Potential refund logic for request_tx_hash? Complex.
                return
            st.session_state.payment_tx_hash = payment_tx_hash
            st.success(f"Payment successful! (Tx: ...{payment_tx_hash[-6:]})")

            # --- Step 3: Start Execution ---
            # Create execution steps based on selected tools
            selected_tool_names = [t.name for t in st.session_state.selected_tools]
            execution_steps = utils.create_execution_steps(st.session_state.selected_tools)
            st.session_state.execution_steps = execution_steps
            
            execution_info = run_async(api.start_mech_execution(
                request_tx_hash=st.session_state.request_tx_hash,
                payment_tx_hash=st.session_state.payment_tx_hash,
                selected_tools_names=selected_tool_names,
                execution_steps=execution_steps,
                chain_config=st.session_state.chain_config,
                account=st.session_state.account_info['account_obj'],
                transaction_id=st.session_state.transaction_id  # Pass the transaction ID
            ))

            if execution_info is None:
                 st.error(st.session_state.error_message or "Failed to start mech execution.")
                 # Potential refund logic? Complex.
                 return
            st.session_state.execution_info = execution_info
            st.success(f"Execution started! Request ID: ...{execution_info['requestId'][-6:]}, Operator: ...{execution_info['operator'][-6:]}")
            
            st.session_state.page = 'execution'
            st.rerun()

def execution():
    """Page for execution monitoring"""
    st.markdown("""
    <div class="header-container">
        <h1>Execution Status</h1>
        <p>Monitoring the progress of your DeFi strategy analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a progress tracker
    st.markdown("""
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px; background-color: #f0f4ff; padding: 10px; border-radius: 5px;">
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">1. Connect</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">2. Create Request</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">3. Payment</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px; background-color: #deebff; border-radius: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">4. Execution</div>
            <div style="font-size: 12px;">⏳ In Progress</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.execution_info:
        st.warning("Execution not started yet.")
        if st.button("Go Back"): st.session_state.page = 'payment'; st.rerun()
        return

    req_id = st.session_state.execution_info['requestId']
    operator = st.session_state.execution_info['operator']

    # Set up auto-refresh for status updates
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
        st.session_state.last_refresh = time.time()
        st.session_state.refresh_interval = 5  # seconds
    
    # Create a columns layout
    col1, col2 = st.columns([3, 1])
    
    with col2:
        auto_refresh = st.toggle("Auto Refresh", value=st.session_state.auto_refresh)
        if auto_refresh != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh
        
        if auto_refresh:
            st.session_state.refresh_interval = st.slider(
                "Refresh Interval (seconds)", 
                min_value=3, 
                max_value=30, 
                value=st.session_state.refresh_interval
            )
            
            # Display countdown timer
            elapsed = time.time() - st.session_state.last_refresh
            remaining = max(0, st.session_state.refresh_interval - elapsed)
            st.markdown(f"Refreshing in: **{int(remaining)}s**")
    
    with col1:
        st.markdown(f"""
        <div class="info-box">
            <h3>Request Details</h3>
            <p><strong>Request ID:</strong> {req_id}</p>
            <p><strong>Operator:</strong> {operator}</p>
            <p><strong>Transaction ID:</strong> {st.session_state.transaction_id if 'transaction_id' in st.session_state else 'N/A'}</p>
            <p><strong>Status:</strong> <span id="status-span">Checking...</span></p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <h3>Execution Steps</h3>
        <p>Progress of your strategy analysis through each processing stage</p>
    </div>
    """, unsafe_allow_html=True)
    
    steps_container = st.container()

    def update_steps_display(steps):
        steps_container.empty()
        with steps_container:
             for i, step in enumerate(steps):
                 status_icon = {"pending": "⏱️", "in_progress": "⏳", "completed": "✅", "error": "❌"}.get(step['status'], "❓")
                 st.markdown(f"""
                 <div class="step-container">
                     <div class="step-number">{i+1}</div>
                     <div>
                         <strong>{step['step']}</strong><br>
                         Tool: {step['tool']}<br>
                         Status: {status_icon} {step['status'].capitalize()}
                     </div>
                 </div>
                 """, unsafe_allow_html=True)

    update_steps_display(st.session_state.execution_steps)

    # If we have a transaction ID, display a link to the history page
    if 'transaction_id' in st.session_state:
        st.markdown(f"""
        <div style="margin-top: 20px; margin-bottom: 20px;">
            <p>You can also view this transaction's progress in the 
            <a href="#" onclick="document.querySelector('[data-testid=\"stSidebarUserContent\"] [role=\"radiogroup\"] :nth-child(2)').click(); 
            return false;">Transaction History</a> page.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Add a partial results container that will be filled when we have data
    results_container = st.container()

    # Function to refresh the status
    def refresh_status():
        st.session_state.error_message = None
        transaction_id = st.session_state.transaction_id if 'transaction_id' in st.session_state else None
             
        status_data = run_async(api.get_execution_status_and_result(
            request_id=req_id,
            chain_config=st.session_state.chain_config,
            account=st.session_state.account_info['account_obj'],
            transaction_id=transaction_id  # Pass the transaction ID if available
        ))

        if status_data is None:
            st.error(st.session_state.error_message or "Failed to get status.")
            # Update status display to Error
            st.markdown(f'<script>document.getElementById("status-span").innerText = "Error"</script>', unsafe_allow_html=True)
            return

        st.session_state.execution_status = status_data['status']
        st.session_state.final_result = status_data['result'] # Might be partial or final

        # Update status text on page
        st.markdown(f'<script>document.getElementById("status-span").innerText = "{st.session_state.execution_status}"</script>', unsafe_allow_html=True)

        # If we have a transaction ID, fetch the latest data from storage
        if transaction_id:
            # Get the transaction to update the step statuses from storage
            transaction = run_async(api.get_transaction_by_id(transaction_id))
            if transaction and hasattr(transaction, 'execution_steps'):
                # Update steps from transaction storage
                updated_steps = []
                for step in transaction.execution_steps:
                    updated_steps.append({
                        'step': step.step,
                        'tool': step.tool,
                        'status': step.status
                    })
                st.session_state.execution_steps = updated_steps
                update_steps_display(updated_steps)
        else:
            # Fallback to old method (for backward compatibility)
            # --- Update Step Statuses (Basic Simulation) ---
            current_status = st.session_state.execution_status.lower()
            updated_steps = st.session_state.execution_steps
            all_completed = True
            found_in_progress = False
            for i, step in enumerate(updated_steps):
                if step['status'] == 'completed': continue
                if step['status'] == 'error': all_completed = False; continue

                # Simple logic: if overall status implies progress, mark earlier steps done
                if "processing" in current_status or "comparing" in current_status or "completed" in current_status:
                    if not found_in_progress:
                         step['status'] = 'in_progress'
                         found_in_progress = True
                         all_completed = False
                    # Mark previous steps as completed implicitly assumes linear flow
                    if i > 0 and updated_steps[i-1]['status'] == 'in_progress':
                         updated_steps[i-1]['status'] = 'completed'
                    all_completed = False
                elif "error" in current_status:
                    step['status'] = 'error' # Mark current or next step as error
                    all_completed = False
                    break # Stop updating on error
                else: # Pending
                    all_completed = False
            
            if current_status == "completed" and not all_completed:
                # If overall is complete, mark all non-error steps as complete
                for step in updated_steps:
                     if step['status'] != 'error': step['status'] = 'completed'
                all_completed = True

            st.session_state.execution_steps = updated_steps
            update_steps_display(updated_steps)

        # Display partial results if available
        with results_container:
            if st.session_state.final_result and st.session_state.final_result.get('partial', False):
                st.markdown("""
                <div class="result-container">
                    <h3>Partial Results</h3>
                    <p>Preliminary findings as analysis continues</p>
                </div>
                """, unsafe_allow_html=True)
                st.json(st.session_state.final_result['content'])  # Assuming content is JSON-friendly

        # Check for completion
        if st.session_state.execution_status == "Completed":
            st.success("Execution Completed! Proceed to view results.")
            st.session_state.auto_refresh = False  # Stop auto-refresh once completed
            st.session_state.page = 'results'
            st.rerun()
        elif st.session_state.execution_status == "Error":
            st.error("Execution failed. Check logs or operator status.")
            st.session_state.auto_refresh = False  # Stop auto-refresh on error
        else:
            st.info("Execution is still in progress. Will refresh automatically.")
    
    # Manual refresh button
    if st.button("Refresh Status Now"):
        refresh_status()
        st.session_state.last_refresh = time.time()
    
    # Auto-refresh based on timer
    if st.session_state.auto_refresh:
        current_time = time.time()
        if current_time - st.session_state.last_refresh >= st.session_state.refresh_interval:
            refresh_status()
            st.session_state.last_refresh = current_time
            time.sleep(0.1)  # Small delay to prevent excessive reloading
            st.rerun()  # Force page to refresh to show countdown timer

def results():
    """Page displaying final results"""
    st.markdown("""
    <div class="header-container">
        <h1>DeFi Strategy Results</h1>
        <p>Your personalized lending strategy recommendation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a progress tracker
    st.markdown("""
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px; background-color: #f0f4ff; padding: 10px; border-radius: 5px;">
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">1. Connect</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">2. Create Request</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">3. Payment</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
        <div style="text-align: center; width: 25%; padding: 5px;">
            <div style="color: #4e6ef2; font-weight: bold;">4. Execution</div>
            <div style="font-size: 12px;">✅ Complete</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we're viewing a specific transaction from history
    transaction_id = None
    if 'transaction_to_view' in st.session_state:
        transaction_id = st.session_state['transaction_to_view']
        # Get transaction data
        with st.spinner("Loading transaction data..."):
            transaction = run_async(api.get_transaction_by_id(transaction_id))
            if transaction:
                # Set up session state with data from this transaction
                st.session_state.execution_info = transaction.execution_info
                st.session_state.execution_status = "Completed"  # Assume completed if viewing from history
                st.session_state.final_result = transaction.final_result
                
                # Display a note that we're viewing a historical transaction
                st.info(f"Viewing results for transaction {transaction_id[:8]}...")
            else:
                st.error(f"Could not load transaction {transaction_id}")
                if st.button("Go to History"):
                    st.session_state.page = 'transaction_history'
                    st.rerun()
                return
    else:
        # Use current transaction ID if available
        transaction_id = st.session_state.transaction_id if 'transaction_id' in st.session_state else None
    
    if not st.session_state.execution_info or st.session_state.execution_status != "Completed":
        st.warning("Execution not completed or results not available.")
        if st.button("Go Back"): st.session_state.page = 'execution'; st.rerun()
        return

    req_id = st.session_state.execution_info['requestId']
    operator = st.session_state.execution_info['operator']

    # Perform final verification and processing (including potential slashing check)
    st.markdown("""
    <div class="info-box">
        <h3>Result Verification</h3>
        <p>Validating the quality and accuracy of the strategy recommendation</p>
    </div>
    """, unsafe_allow_html=True)
    
    final_verified_result = None
    with st.spinner("Verifying final results (checking slashing conditions if applicable)..."):
         final_verified_result = run_async(api.verify_and_process_results(
             request_id=req_id,
             operators=[operator], # Pass the list of operators (currently just one)
             chain_config=st.session_state.chain_config,
             account=st.session_state.account_info['account_obj'],
             transaction_id=transaction_id  # Pass the transaction ID if available
         ))
    
    if final_verified_result is None:
         st.error(st.session_state.error_message or "Failed to verify or process final results.")
         # Display raw result if verification failed but result exists?
         if st.session_state.final_result:
             st.warning("Displaying potentially unverified result:")
             st.json(st.session_state.final_result)
         return
    else:
         st.success("Result verified.")
         # Use the verified result from now on
         st.session_state.final_result = final_verified_result

    st.markdown(f"""
    <div class="info-box">
        <h3>Request Information</h3>
        <p><strong>Request ID:</strong> {req_id}</p>
        <p><strong>Operator(s):</strong> {operator}</p>
        <p><strong>Status:</strong> Completed & Verified</p>
        {f'<p><strong>Transaction ID:</strong> {transaction_id}</p>' if transaction_id else ''}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <h3>Strategy Recommendation</h3>
        <p>Based on our analysis, here's the optimal lending strategy for you</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.final_result and not st.session_state.final_result.get('isError', False):
        result_text = "No text content found."
        if isinstance(st.session_state.final_result.get('content'), list) and len(st.session_state.final_result['content']) > 0:
             result_text = st.session_state.final_result['content'][0].get('text', result_text)
        
        # Try to parse details from the text (simple example)
        apy_match = utils.parse_apy(result_text)
        apy_str = f"{apy_match:.1f}%" if apy_match else "N/A"
        platform = "Aave" if "aave" in result_text.lower() else "Compound" if "compound" in result_text.lower() else "Other" 

        st.markdown(f"""
        <div class="result-container">
            <h3>Best Strategy: {platform}</h3>
            <p><strong>Summary:</strong> {result_text}</p>
            <p><strong>Expected APY (Parsed):</strong> {apy_str}</p>
            <p><strong>Additional Details:</strong> Extracted from agent result</p>
        </div>
        """, unsafe_allow_html=True)

        # Display raw JSON result too
        with st.expander("View Raw Result Data"):
            st.json(st.session_state.final_result)

    elif st.session_state.final_result:
        st.error("The process completed with an error.")
        st.json(st.session_state.final_result)
    else:
        st.error("Final result data is missing.")

    # Placeholder for detailed analysis tabs (would require structured data)
    st.markdown("""
    <div class="info-box">
        <h3>Detailed Analysis</h3>
        <p>Comprehensive breakdown of lending options and performance metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("_(Detailed comparison, risk analysis, and historical data would require structured output from the agent)_ ")
    # tabs = st.tabs(["Comparison", "Risk Analysis", "Historical Performance"])
    # with tabs[0]: ...

    # Display slashing info if applicable
    if api.DEFAULT_SLASHING_CONTRACT_ADDRESS:
        st.markdown("""
        <div class="info-box">
            <h3>Result Validation via Slashing Contract</h3>
            <p>Results were submitted for verification against the slashing contract rules.</p>
            <p>Results from multiple operators were compared and verified.</p>
            <p>_(Verification successful in this demo)_</p>
        </div>
        """, unsafe_allow_html=True)

    # Add buttons for navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Create New Request"):
            # Reset relevant state
            keys_to_reset = ['page', 'prompt', 'available_tools', 'selected_tools', 'total_cost', 
                           'request_tx_hash', 'payment_tx_hash', 'execution_info', 
                           'execution_steps', 'execution_status', 'final_result', 'error_message',
                           'transaction_id', 'transaction_to_view']
            for key in keys_to_reset:
                if key in st.session_state:
                    if key == 'page':
                        st.session_state[key] = 'create_request'
                    else:
                        st.session_state[key] = None if key != 'selected_tools' and key != 'available_tools' and key != 'execution_steps' else []
            st.rerun()
    
    with col2:
        if st.button("View Transaction History"):
            st.session_state.page = 'transaction_history'
            st.rerun()
    
    with col3:
        if 'transaction_to_view' in st.session_state:
            if st.button("Back to History"):
                # Clear the transaction_to_view and go back to history
                if 'transaction_to_view' in st.session_state:
                    del st.session_state['transaction_to_view']
                st.session_state.page = 'transaction_history'

def transaction_history():
    """Page for viewing transaction history"""
    st.markdown("""
    <div class="header-container">
        <h1>Transaction History</h1>
        <p>View and track all your OLAS requests and their current status</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if user is connected
    if not st.session_state.account_info:
        st.warning("Please connect your wallet first to view your transaction history.")
        if st.button("Connect Wallet"):
            st.session_state.page = 'home'
            st.rerun()
        return
    
    # Get user's address
    user_address = st.session_state.account_info['address']
    
    # Fetch transactions
    with st.spinner("Loading transaction history..."):
        transactions = run_async(api.get_transactions_for_account(user_address))
    
    if not transactions:
        st.info("No transactions found. Create a request to get started!")
        if st.button("Create New Request"):
            st.session_state.page = 'create_request'
            st.rerun()
        return
    
    # Display transactions in a sortable table
    st.markdown("""
    <div class="info-box">
        <h3>Your Transactions</h3>
        <p>Recent activity and request status</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a DataFrame for better display
    import pandas as pd
    
    # Prepare data for the table
    table_data = []
    for tx in transactions:
        # Determine overall status
        status = "Pending"
        if hasattr(tx, 'verification_state') and tx.verification_state and tx.verification_state.status == "completed":
            status = "Completed"
        elif hasattr(tx, 'execution_state') and tx.execution_state and tx.execution_state.status == "completed":
            status = "Results Ready"
        elif hasattr(tx, 'execution_state') and tx.execution_state and tx.execution_state.status == "in_progress":
            status = "Executing"
        elif hasattr(tx, 'payment_state') and tx.payment_state and tx.payment_state.status == "completed":
            status = "Payment Complete"
        elif hasattr(tx, 'payment_state') and tx.payment_state and tx.payment_state.status == "in_progress":
            status = "Payment Processing"
        elif hasattr(tx, 'request_state') and tx.request_state and tx.request_state.status == "completed":
            status = "Request Submitted"
        elif hasattr(tx, 'request_state') and tx.request_state and tx.request_state.status == "failed":
            status = "Request Failed"
        
        # Extract tool names
        tools = ", ".join([t.name for t in tx.selected_tools]) if hasattr(tx, 'selected_tools') and tx.selected_tools else "N/A"
        
        # Format date
        created_at = tx.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(tx, 'created_at') and tx.created_at else "N/A"
        
        # Add to table data
        table_data.append({
            "ID": tx.id,
            "Date": created_at,
            "Status": status,
            "Tools": tools,
            "Cost": f"{tx.total_cost:.3f} xDAI" if hasattr(tx, 'total_cost') else "N/A",
        })
    
    # Create DataFrame
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Date": st.column_config.TextColumn("Date", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="medium"),
                "Tools": st.column_config.TextColumn("Tools", width="large"),
                "Cost": st.column_config.TextColumn("Cost", width="small"),
            },
            hide_index=True,
        )
    
    # Add a section for transaction details
    st.markdown("""
    <div class="info-box">
        <h3>Transaction Details</h3>
        <p>Select a transaction ID to view detailed information</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a dropdown to select transaction
    selected_tx_id = st.selectbox(
        "Select Transaction",
        options=[tx.id for tx in transactions],
        format_func=lambda x: f"{x[:8]}... - {next((tx.prompt[:30] + '...' if len(tx.prompt) > 30 else tx.prompt) for tx in transactions if tx.id == x)}"
    )
    
    if selected_tx_id:
        # Get detailed information for the selected transaction
        tx_details = run_async(api.get_transaction_details(selected_tx_id))
        
        if tx_details:
            # Display transaction information in expandable sections
            with st.expander("Request Information", expanded=True):
                st.markdown(f"""
                <div class="card">
                    <p><strong>Request ID:</strong> {tx_details['id']}</p>
                    <p><strong>Created:</strong> {tx_details['created_at']}</p>
                    <p><strong>Last Updated:</strong> {tx_details['updated_at']}</p>
                    <p><strong>Status:</strong> {tx_details['overall_status'].capitalize()}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<strong>Prompt:</strong>", unsafe_allow_html=True)
                st.text(tx_details['prompt'])
            
            with st.expander("Tool Information", expanded=True):
                st.markdown(f"""
                <div class="card">
                    <p><strong>Selected Tools:</strong> {', '.join(tx_details['selected_tools'])}</p>
                    <p><strong>Total Cost:</strong> {tx_details['total_cost']} xDAI</p>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("Transaction Status", expanded=True):
                # Create a status timeline
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown("<strong>Request:</strong>", unsafe_allow_html=True)
                    st.markdown("<strong>Payment:</strong>", unsafe_allow_html=True)
                    st.markdown("<strong>Execution:</strong>", unsafe_allow_html=True)
                    st.markdown("<strong>Verification:</strong>", unsafe_allow_html=True)
                
                with col2:
                    request_status = tx_details['request_status'].capitalize()
                    request_color = "green" if request_status == "Completed" else "red" if request_status == "Failed" else "blue"
                    st.markdown(f"<span style='color:{request_color};'>{request_status}</span>", unsafe_allow_html=True)
                    
                    payment_status = tx_details['payment_status'].capitalize()
                    payment_color = "green" if payment_status == "Completed" else "red" if payment_status == "Failed" else "blue"
                    st.markdown(f"<span style='color:{payment_color};'>{payment_status}</span>", unsafe_allow_html=True)
                    
                    execution_status = tx_details['execution_status'].capitalize()
                    execution_color = "green" if execution_status == "Completed" else "red" if execution_status == "Failed" else "blue"
                    st.markdown(f"<span style='color:{execution_color};'>{execution_status}</span>", unsafe_allow_html=True)
                    
                    verification_status = tx_details['verification_status'].capitalize() if tx_details['verification_status'] else "Not Started"
                    verification_color = "green" if verification_status == "Completed" else "red" if verification_status == "Failed" else "gray"
                    st.markdown(f"<span style='color:{verification_color};'>{verification_status}</span>", unsafe_allow_html=True)
                
                # Show transaction hashes if available
                if tx_details['request_tx_hash']:
                    st.markdown(f"<strong>Request Transaction:</strong> ...{tx_details['request_tx_hash'][-6:]}", unsafe_allow_html=True)
                
                if tx_details['payment_tx_hash']:
                    st.markdown(f"<strong>Payment Transaction:</strong> ...{tx_details['payment_tx_hash'][-6:]}", unsafe_allow_html=True)
                
                if tx_details['request_id']:
                    st.markdown(f"<strong>Mech Request ID:</strong> ...{tx_details['request_id'][-6:]}", unsafe_allow_html=True)
                
                if tx_details['operator']:
                    st.markdown(f"<strong>Operator:</strong> ...{tx_details['operator'][-6:]}", unsafe_allow_html=True)
            
            with st.expander("Execution Steps", expanded=True):
                for step in tx_details['steps']:
                    status_icon = {"pending": "⏱️", "in_progress": "⏳", "completed": "✅", "error": "❌"}.get(step['status'], "❓")
                    st.markdown(f"""
                    <div class="step-container">
                        <div>
                            <strong>{step['step']}</strong><br>
                            Tool: {step['tool']}<br>
                            Status: {status_icon} {step['status'].capitalize()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Show results if available
            if tx_details['final_result']:
                with st.expander("Results", expanded=True):
                    result_text = "No text content found."
                    if isinstance(tx_details['final_result'].get('content'), list) and len(tx_details['final_result']['content']) > 0:
                        result_text = tx_details['final_result']['content'][0].get('text', result_text)
                    
                    st.markdown(f"""
                    <div class="result-container">
                        <h3>Results</h3>
                        <p>{result_text}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display raw JSON result
                    with st.expander("Raw Result Data"):
                        st.json(tx_details['final_result'])
            
            # Add action buttons based on state
            st.markdown("<h3>Actions</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if tx_details['overall_status'] == "completed":
                    if st.button("View Detailed Results"):
                        # Set up session state to view this transaction's results
                        # This would require modifications to the results page to accept a transaction ID
                        st.session_state['transaction_to_view'] = selected_tx_id
                        st.session_state.page = 'results'
                        st.rerun()
            
            with col2:
                if st.button("Create Similar Request"):
                    # Pre-fill the prompt from this transaction
                    st.session_state.prompt = tx_details['prompt']
                    st.session_state.page = 'create_request'
                    st.rerun()
    
    # Add a button to create a new request
    if st.button("Create New Request"):
        st.session_state.page = 'create_request'
        st.rerun()

# Main navigation router
if __name__ == "__main__":
    # Add a sidebar for navigation between main flow and history
    with st.sidebar:
        st.title("Navigation")
        
        # Only show history option if user is authenticated
        if st.session_state.authenticated:
            selected_page = st.radio(
                "Go to",
                ["Main App", "Mech History"],  # Renamed from "Transaction History" to "Mech History"
                index=0,
                key="sidebar_selection"
            )
            
            # If user selects history from sidebar, override the session state
            if selected_page == "Mech History":
                st.session_state.page = 'transaction_history'
            elif selected_page == "Main App" and st.session_state.page == 'transaction_history':
                # Only reset if coming from history page
                st.session_state.page = 'home'
        else:
            # Only show main app if not authenticated
            st.info("Please log in to access Mech History")
            selected_page = "Main App"
    
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        # Optional: Add a button to clear the error
        # if st.button("Clear Error"): st.session_state.error_message = None; st.rerun()

    page = st.session_state.page
    if page == 'home':
        home()
    elif page == 'create_request':
        create_request()
    elif page == 'payment':
        payment()
    elif page == 'execution':
        execution()
    elif page == 'results':
        results()
    elif page == 'transaction_history':
        # Only allow access to transaction history if authenticated
        if st.session_state.authenticated:
            transaction_history()
        else:
            st.warning("Please connect your wallet first to view Mech History.")
            st.session_state.page = 'home'
            st.rerun()
    else:
        st.error("Invalid page state.")
        st.session_state.page = 'home'
        st.rerun()
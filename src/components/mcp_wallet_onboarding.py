import streamlit as st
import os
from web3 import Web3

def generate_eth_key():
    from eth_account import Account
    acct = Account.create()
    return acct.address, acct.key.hex()

def load_private_key_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            key = f.read().strip()
        from eth_account import Account
        acct = Account.from_key(key)
        return acct.address, key
    except Exception as e:
        return None, None

def get_eth_balance(address, rpc_url=None):
    # Default to public mainnet RPC if not provided
    rpc_url = rpc_url or os.environ.get('WEB3_RPC_URL', 'https://rpc.ankr.com/gnosis')
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        balance_wei = w3.eth.get_balance(address)
        return w3.fromWei(balance_wei, 'ether')
    except Exception:
        return None

def mcp_wallet_onboarding():
    st.markdown("""
    <h3>Wallet Onboarding</h3>
    <p>Generate a new Ethereum wallet or connect an existing one to use with MCP.</p>
    """, unsafe_allow_html=True)
    
    onboarding_mode = st.radio("Select onboarding method:", ["Generate new wallet", "Connect existing wallet"], horizontal=True)
    wallet_address = None
    private_key = None
    if onboarding_mode == "Generate new wallet":
        if st.button("Generate Wallet", key="generate_wallet_btn"):
            address, key = generate_eth_key()
            st.session_state['wallet_address'] = address
            st.session_state['private_key'] = key
            st.success(f"New wallet generated: {address}")
            st.code(key, language="text")
            wallet_address = address
            private_key = key
    else:
        uploaded = st.file_uploader("Upload your private key file (text file)", type=["txt", "key"])
        if uploaded is not None:
            key = uploaded.read().decode().strip()
            from eth_account import Account
            try:
                acct = Account.from_key(key)
                st.session_state['wallet_address'] = acct.address
                st.session_state['private_key'] = key
                st.success(f"Wallet connected: {acct.address}")
                st.code(key, language="text")
                wallet_address = acct.address
                private_key = key
            except Exception as e:
                st.error(f"Invalid private key: {e}")
    # Show wallet info if available
    if 'wallet_address' in st.session_state:
        address = st.session_state['wallet_address']
        st.info(f"**Wallet Address:** {address}")
        balance = get_eth_balance(address)
        if balance is not None:
            st.info(f"**Current Balance:** {balance} ETH")
        else:
            st.warning("Could not fetch balance. Check your RPC settings.")
        # Example: required stake (could be dynamic)
        required_stake = 40
        st.info(f"**Staking Required:** {required_stake} OLAS")
        # Optionally, show a button to proceed to MCP wallet main page
        if st.button("Proceed to MCP Wallet", key="proceed_mcp_wallet"):
            st.session_state['onboarded'] = True
            st.experimental_rerun()

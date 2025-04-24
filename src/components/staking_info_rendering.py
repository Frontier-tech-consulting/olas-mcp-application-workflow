import streamlit as st
def render_account_and_staking_info():
    """Render user account details, connection status, and staking requirements (top right corner)."""
    if not st.session_state.get('authenticated') or not st.session_state.get('account_info'):
        return
    account = st.session_state.account_info
    # Example values for staking and trading requirements
    staking_required = 40
    trading_required = 10
    current_balance = 101.7  # You may want to fetch this dynamically
    safe_address = account.get('wallet_address', '0x...')
    display_address = account.get('display_address', safe_address[:6] + '...' + safe_address[-4:])
    
    col1, col2 = st.columns([3, 2])
    with col2:
        st.markdown(f"""
        <div style='background: #f6f0ff; border-radius: 10px; padding: 16px; margin-bottom: 10px; text-align: right;'>
            <div style='font-size: 0.95rem; color: #7c3aed; font-weight: bold;'>Connected</div>
            <div style='font-size: 0.85rem; color: #333;'>
                <b>Safe Address:</b> {display_address}
            </div>
            <div style='font-size: 0.85rem; color: #333;'>
                <b>Current Balance:</b> {current_balance} OLAS
            </div>
            <div style='font-size: 0.85rem; color: #333;'>
                <b>Staking Required:</b> {staking_required} OLAS<br>
                <b>Trading Required:</b> {trading_required} XDAI
            </div>
        </div>
        """, unsafe_allow_html=True)

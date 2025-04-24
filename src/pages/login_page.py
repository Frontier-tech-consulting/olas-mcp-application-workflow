import streamlit as st
from src.utils.session_state import init_session_state, save_session_state_if_authenticated
from src.components.styling import define_stepper_section
from src.utils.transaction_storage import generate_eth_address, generate_gnosis_safe_address, format_eth_address
from src.utils.session_state import save_session_state_if_authenticated
def app_login():
    """Application login page with mock authentication"""
    # Create a header for the login page
    st.markdown(f"""
    <div class="header">
        <h1>{st.session_state.selected_app.replace('_', ' ').title()}</h1>
        <p>Sign in to access the application dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # Show authentication form
    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        # Center the login button and control its width
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button("Login")
            
        if submit:
            # Login logic
            if email and password:
                # Create a mock owner wallet address
                owner_address = generate_eth_address(email.lower())
                
                # Create a mock Gnosis Safe address based on the owner address
                safe_address = generate_gnosis_safe_address(owner_address)
                
                # Store formatted address for display
                display_address = format_eth_address(safe_address)
                
                st.session_state.authenticated = True
                st.session_state.account_info = {
                    "email": email,
                    "user_id": "mock_user_id",
                    "wallet_address": safe_address,
                    "owner_address": owner_address,
                    "display_address": display_address
                }
                st.success("Login successful!")
                save_session_state_if_authenticated()
                st.session_state.page = 'create_request'
                st.rerun()
            else:
                st.error("Please enter both email and password")
    
    # Back button
    if st.button("Back to App Store"):
        st.session_state.page = 'home'
        st.rerun()

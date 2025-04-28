import streamlit as st
from src.components.styling import display_user_header
from src.components.process_payment import process_payment
from src.components.execution_status import ExecutionStatus
def app_execution_page():
    """
    Application execution page showing service execution status
    """
    # Display user header
    display_user_header()
    
    # Check if we're in payment processing mode
    if st.session_state.get('payment_processing', False) and not st.session_state.get('payment_completed', False):
        # Show payment processing UI
        process_payment(st.session_state.current_request)
        return
    
    # Ensure the request is properly stored in session state
    if 'current_request' in st.session_state and st.session_state.current_request:
        # Also store in the standard 'request' key that ExecutionStatus expects
        st.session_state.request = st.session_state.current_request
        
        # Initialize execution status component with current request and render it
        execution_status = ExecutionStatus()
        execution_status.render()
    else:
        st.error("No active request found. Please create a request first.")
        if st.button("Back to Request Form", key="back_to_request_nodata"):
            st.session_state.page = "create_request"
            st.rerun()

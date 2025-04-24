import streamlit as st
import json

def init_session_state():
    """Initialize session state variables and load (from Supabase if available.)"""
    defaults = {
        "page": "landing",  # Landing page as default
        "authenticated": False,
        "account_info": None,
        "selected_app": None,
        "show_login": True,
        "show_signup": False,
        "current_request": None,
        "transaction_id": None,
        "chain": "Gnosis Chain",  # Default chain
        "payment_processing": False,
        "payment_completed": False,
        "submitted_requests": [],
        "services": [],  # Initialize empty services list
        "login_email": "",
        "verification_id": "",
        "wallet_address": None,
        "reasoning_complete": False,
        "reasoning_response": "",
        "selected_services": []
    }
    # Try to load session state from Supabase if user is authenticated
    user_id = None
    if "account_info" in st.session_state and st.session_state.account_info:
        user_id = st.session_state.account_info.get("user_id")
    if user_id:
        loaded_state = supabase_client.load_session_state(user_id)
        if loaded_state:
            for k, v in loaded_state.items():
                st.session_state[k] = v
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Load services data from JSON file if not already in session state
    if not st.session_state.get("services"):
        try:
            with open('enriched_services_data.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "services" in data:
                    st.session_state.services = data["services"]
                    print(f"Loaded {len(data['services'])} services into session state")
                elif isinstance(data, list):
                    st.session_state.services = data
                    print(f"Loaded {len(data)} services into session state")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading services data: {str(e)}")
            # Use default services if file not found
            st.session_state.services = []


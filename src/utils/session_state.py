import json
import streamlit as st

def init_session_state(supabase_client=None):
    defaults = {
        "page": "landing",
        "authenticated": False,
        "account_info": None,
        "selected_app": None,
        "show_login": True,
        "show_signup": False,
        "current_request": None,
        "transaction_id": None,
        "chain": "Gnosis Chain",
        "payment_processing": False,
        "payment_completed": False,
        "submitted_requests": [],
        "services": [],
        "login_email": "",
        "verification_id": "",
        "wallet_address": None,
        "reasoning_complete": False,
        "reasoning_response": "",
        "selected_services": []
    }
    user_id = None
    if "account_info" in st.session_state and st.session_state.account_info:
        user_id = st.session_state.account_info.get("user_id")
    if user_id and supabase_client:
        loaded_state = supabase_client.load_session_state(user_id)
        if loaded_state:
            for k, v in loaded_state.items():
                st.session_state[k] = v
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if not st.session_state.get("services"):
        try:
            with open('enriched_services_data.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "services" in data:
                    st.session_state.services = data["services"]
                elif isinstance(data, list):
                    st.session_state.services = data
        except (FileNotFoundError, json.JSONDecodeError):
            st.session_state.services = []

def save_session_state_if_authenticated(supabase_client):
    if st.session_state.get("authenticated") and st.session_state.get("account_info"):
        user_id = st.session_state.account_info.get("user_id")
        if user_id:
            state_to_save = {k: v for k, v in st.session_state.items() if k != "_callbacks"}
            supabase_client.save_session_state(user_id, state_to_save)

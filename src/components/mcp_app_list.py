import streamlit as st
from src.components.staking_info_rendering import render_account_and_staking_info


def app_storefront():
    """Show the MCP App Storefront with 4 app cards and account info."""
    # Top right: account and staking info
    render_account_and_staking_info()
    
    st.markdown("""
    <div style='text-align: center; margin-top: 2rem; margin-bottom: 2rem;'>
        <h1 style='font-size: 2.2rem;'> Select the MCP app mode</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;'>
            <div style='text-align: center; margin-bottom: 12px;'>
                <img src='https://cdn-icons-png.flaticon.com/512/1048/1048953.png' style='width: 80px; height: 80px; object-fit: contain;'>
            </div>
            <h3 style='text-align: center; margin-bottom: 8px;'>browser-extension</h3>
            <p style='text-align: center; color: #666; margin-bottom: 16px;'>
                Use MCP as a browser extension for seamless web integration.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select", key="select_browser_ext", use_container_width=True):
            st.session_state.page = 'browser_extension'
            st.rerun()
    with col2:
        st.markdown("""
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;'>
            <div style='text-align: center; margin-bottom: 12px;'>
                <img src='https://cdn-icons-png.flaticon.com/512/2721/2721278.png' style='width: 80px; height: 80px; object-fit: contain;'>
            </div>
            <h3 style='text-align: center; margin-bottom: 8px;'>Deep-researcher</h3>
            <p style='text-align: center; color: #666; margin-bottom: 16px;'>
                Access the full-featured MCP web application.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select", key="select_web_app", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()
    with col3:
        st.markdown("""
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;'>
            <div style='text-align: center; margin-bottom: 12px;'>
            </div>
            <h3 style='text-align: center; margin-bottom: 8px;'>computer-use-app (mac/linux) coming-soon</h3>
            <p style='text-align: center; color: #666; margin-bottom: 16px;'>
                (Coming soon ) setup the local MCP client to query across the linux commands.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Select", key="select_win_app", use_container_width=True, disabled=True)


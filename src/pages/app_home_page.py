import streamlit as st
from src.utils.session_state import init_session_state, save_session_state_if_authenticated
def app_home():
    """Home page with app selection"""
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; margin-bottom: 3rem;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">Pearl App Store</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # If already authenticated, show quick access to last used app
    if st.session_state.authenticated:
        st.markdown("### Welcome Back!")
        st.markdown(f"Continue working with {st.session_state.selected_app.replace('_', ' ').title() if st.session_state.selected_app else 'Olas apps'}:")
        
        # Create three columns for quick access options
        col1, col2, col3 = st.columns(3)
    
        with col1:
            if st.button("Continue Last App", key="home_continue", use_container_width=True):
                if st.session_state.selected_app == "olas_mcp":
                    st.session_state.page = 'create_request'
                else:
                    st.session_state.page = 'dashboard'
                st.rerun()
    
        with col2:
            if st.button("Browse All Apps", key="home_browse", use_container_width=True):
                # This will show the app listings below
                pass
        
        with col3:
            if st.button("Logout", key="home_logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.account_info = {}
                save_session_state_if_authenticated()
                st.rerun()
    
    # Display available apps
    st.markdown("### Available Applications")
    
    # Create a 2x2 grid of app cards
    col1, col2 = st.columns(2)
    
    with col1:
        # MCP App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://assets.website-files.com/625a1e828031aa55b8e0c4b2/6498b97f7c82d53a6e38065d_olas-icon-p-500.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
                </div>
            <h3 style="text-align: center; margin-bottom: 8px;">Olas MCP</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Access AI services through the Multi-Chain Protocol
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> AI Task Processing<br>
                    <span style="color: #4CAF50;">✓</span> On-chain Payment<br>
                    <span style="color: #4CAF50;">✓</span> Gnosis Chain Integration
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
        if st.button("Open Olas MCP", key="open_mcp", use_container_width=True):
            st.session_state.selected_app = "olas_mcp"
            if st.session_state.authenticated:
                st.session_state.page = 'create_request'
            else:
                st.session_state.page = 'login'
            st.rerun()
    
    with col2:
        # Pearl Store App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://static.wixstatic.com/media/e52fa3_6e54262068914db7bfaebe3f37d0b5f7~mv2.png/v1/crop/x_131,y_0,w_639,h_800/fill/w_120,h_150,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/intro-pearl-store.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
            </div>
            <h3 style="text-align: center; margin-bottom: 8px;">Pearl Store</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Decentralized marketplace for digital assets
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> NFT Marketplace<br>
                    <span style="color: #4CAF50;">✓</span> Creator Economy<br>
                    <span style="color: #4CAF50;">✓</span> Multi-chain Support
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
        if st.button("Open Pearl Store", key="open_pearl", use_container_width=True):
            st.session_state.selected_app = "pearl_store"
            if st.session_state.authenticated:
                st.session_state.page = 'dashboard'
            else:
                st.session_state.page = 'login'
            st.rerun()

    # Second row of apps
    col3, col4 = st.columns(2)
    
    with col3:
        # DeFi Dashboard App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://cdn-icons-png.flaticon.com/512/5726/5726778.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
            </div>
            <h3 style="text-align: center; margin-bottom: 8px;">DeFi Dashboard</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Analytics and management for DeFi protocols
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> Portfolio Tracking<br>
                    <span style="color: #4CAF50;">✓</span> Yield Optimization<br>
                    <span style="color: #4CAF50;">✓</span> Risk Management
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open DeFi Dashboard", key="open_defi", use_container_width=True, disabled=True):
            st.session_state.selected_app = "defi_dashboard"
            st.info("Coming soon! This app is under development.")
    
    with col4:
        # Governance Portal App Card
        st.markdown("""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; height: 100%; margin-bottom: 20px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="https://cdn-icons-png.flaticon.com/512/5372/5372785.png" 
                     style="width: 120px; height: 120px; object-fit: contain;">
            </div>
            <h3 style="text-align: center; margin-bottom: 8px;">Governance Portal</h3>
            <p style="text-align: center; color: #666; margin-bottom: 16px;">
                Participate in DAO governance and voting
            </p>
            <div style="text-align: center;">
                <p style="font-size: 0.85rem; color: #444; margin-bottom: 16px;">
                    <span style="color: #4CAF50;">✓</span> Proposal Creation<br>
                    <span style="color: #4CAF50;">✓</span> Voting Interface<br>
                    <span style="color: #4CAF50;">✓</span> Delegation Tools
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Governance Portal", key="open_gov", use_container_width=True, disabled=True):
            st.session_state.selected_app = "governance_portal"
            st.info("Coming soon! This app is under development.")


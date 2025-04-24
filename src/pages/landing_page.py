import streamlit as st
from src.utils.session_state import init_session_state, save_session_state_if_authenticated
from src import define_stepper_section
from src.mock_details.utils import generate_mock_agent_daa_data, generate_mock_usecase_data
import altair as alt

def display_landing_page():
    """Display the landing page content"""
    # Hero section
    st.markdown("""
    <div class="title-container">
        <img src="https://olas.network/images/olas-logo.svg" class="logo-image" alt="OLAS Logo">
        <img src="https://avatars.githubusercontent.com/u/182288589?s=200&v=4" class="logo-image" alt="MCP logo">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">OLAS MCP Platform</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Hero call-to-action
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <p style="font-size: 1.1rem; margin: 1rem 0; max-width: 700px; margin-left: auto; margin-right: auto;">
            Access a wide range of AI agents and services through the Model Context Protocol.<br>
            Submit requests across various categories (browser, chat, computer use) via the mech client.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login button (centered)
    login_col1, login_col2, login_col3 = st.columns([2, 2, 2])
    with login_col2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        if st.button("Login with Privy", key="login_button", use_container_width=True, type="primary"):
            st.session_state.page = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Charts side by side
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Agent Operations Growth (DAA)</h2>", unsafe_allow_html=True)
        daa_data = generate_mock_agent_daa_data()
        # Create bar chart for DAA
        daa_chart = alt.Chart(daa_data).mark_bar(color='#4e6ef2').encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('DAA:Q', title='Daily Active Agents (>=10 interactions)'),
            tooltip=['date:T', alt.Tooltip('DAA:Q', format='.0f')]
        ).properties(
            height=400
        )
        
        st.altair_chart(daa_chart, use_container_width=True)
    with chart_col2:
        st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Agent Use Case Distribution</h2>", unsafe_allow_html=True)
        usecase_data = generate_mock_usecase_data()
        # Create pie chart for use case distribution
        usecase_chart = alt.Chart(usecase_data).mark_arc().encode(
            theta=alt.Theta('proportion:Q'),
            color=alt.Color('use_case:N', scale=alt.Scale(scheme='category10')),
            tooltip=['use_case:N', alt.Tooltip('proportion:Q', format='.1%')]
        ).properties(
            height=400
        )
        
        # Add text labels
        text = alt.Chart(usecase_data).mark_text(radiusOffset=15).encode(
            theta=alt.Theta('proportion:Q', stack=True),
            radius=alt.value(100),
            text=alt.Text('use_case:N')
        )
        
        st.altair_chart(usecase_chart + text, use_container_width=True)
    
    define_stepper_section()  # Define stepper section for instructions

import streamlit as st

def define_mainpage_styling():
    """
    Defines the styling of the main page.
    """

        # Custom CSS for styling
    return st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .title-container {
            text-align: center;
            padding: 2rem 0;
        }
        .logo-image {
            width: 150px;
            margin-bottom: 1rem;
        }
        .chart-container {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin: 20px 0;
        }
        .hero-section {
            background-color: #4e6ef2;
            color: white;
            padding: 3rem 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
        }
        .feature-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin: 10px 0;
            height: 100%;
        }
        .cta-button {
            background-color: #4e6ef2;
            color: white;
            border-radius: 5px;
            padding: 0.75rem 1.5rem;
            font-weight: bold;
            text-align: center;
            display: inline-block;
            margin: 1rem 0;
            border: none;
        }
        .auth-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .wallet-info {
            background-color: #e6f7ff;
            padding: 15px; 
            border-radius: 5px;
            margin-top: 20px;
        }
        .privy-input {
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            margin-bottom: 15px;
            width: 100%;
        }
        .verification-code-input {
            letter-spacing: 0.5em;
            font-size: 24px;
            text-align: center;
        }
        /* Style for all standard Streamlit buttons */
        .stButton button {
            color: white !important;
            background-color: black !important;
            font-weight: bold !important;
            border: none !important;
        }
        
        /* Style for navigation buttons */
        .stButton button[data-testid="baseButton-secondary"] {
            color: white !important;
            background-color: black !important;
            font-weight: bold !important;
            border: none !important;
        }
        
        /* Style for form submit buttons */
        button[type="submit"] {
            color: white !important;
            background-color: black !important;
            font-weight: bold !important;
            width: 100% !important;
            padding: 10px !important;
            border: none !important;
        }
        
        /* Hover state */
        .stButton button:hover {
            color: white !important;
            background-color: #333 !important;
            border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)


def define_stepper_section():
    # Instructions Stepper Section
    st.markdown("<h2 style='text-align: center; margin-top: 2.5rem;'>How to Run the Application</h2>", unsafe_allow_html=True)
    steps = [
        {"title": "Clone the Repository", "desc": "Clone the OLAS MCP repository to your local machine using <code>git clone &lt;repo-url&gt;</code>."},
        {"title": "Install Dependencies", "desc": "Install Python dependencies with <code>pip install -r requirements.txt</code>."},
        {"title": "Set Up Environment", "desc": "Copy <code>.env.example</code> to <code>.env</code> and fill in your Supabase and Privy credentials."},
        {"title": "Initialize Supabase (Optional)", "desc": "Run <code>python init_supabase.py</code> to set up the database tables (see <code>SUPABASE_SETUP.md</code>)."},
        {"title": "Run the App", "desc": "Start the Streamlit app with <code>streamlit run app.py</code>."},
        {"title": "Access the App", "desc": "Open your browser and go to <code>http://localhost:8501</code> to use the OLAS MCP platform."}
    ]
    st.markdown("""
    <style>
    .stepper {
        max-width: 700px;
        margin: 2rem auto 0 auto;
        padding: 0;
    }
    .step {
        display: flex;
        align-items: flex-start;
        margin-bottom: 1.5rem;
    }
    .step-index {
        min-width: 36px;
        height: 36px;
        background: #4e6ef2;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.1rem;
        margin-right: 18px;
        margin-top: 2px;
    }
    .step-content {
        flex: 1;
    }
    .step-title {
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.2rem;
    }
    .step-desc {
        color: #444;
        font-size: 1rem;
    }
    </style>
    <div class="stepper">
    """, unsafe_allow_html=True)
    for i, step in enumerate(steps, 1):
        st.markdown(f"""
        <div class="step">
            <div class="step-index">{i}</div>
            <div class="step-content">
                <div class="step-title">{step['title']}</div>
                <div class="step-desc">{step['desc']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def define_styling_app():
    """
    Define styling for buttons and other common themes of buttons
    """

    st.markdown("""
    <style>
    /* Style for all standard Streamlit buttons */
    .stButton button {
        color: white !important;
        background-color: black !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    /* Style for navigation buttons */
    .stButton button[data-testid="baseButton-secondary"] {
        color: white !important;
        background-color: black !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    /* Style for form submit buttons */
    button[type="submit"] {
        color: white !important;
        background-color: black !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 10px !important;
        border: none !important;
    }
    
    /* Hover state */
    .stButton button:hover {
        color: white !important;
        background-color: #333 !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
            


def display_user_header():
    """Display the user header with account information"""
    if st.session_state.authenticated and 'account_info' in st.session_state:
        account_info = st.session_state.account_info
        address = account_info.get('wallet_address', '')
        display_address = account_info.get('display_address', format_eth_address(address))
        
        # Create columns for layout
        _, col_header = st.columns([0.7, 0.3])
        
        with col_header:
            st.markdown(f"""
            <div style="text-align: right; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                <span style="font-weight: bold;">{account_info.get('email')}</span><br>
                <span style="font-family: monospace; font-size: 0.9em;">
                    {display_address} <span style="background-color: #e6e6e6; padding: 2px 5px; border-radius: 3px; font-size: 0.8em;">Gnosis Chain</span>
                </span>
            </div>
            """, unsafe_allow_html=True)


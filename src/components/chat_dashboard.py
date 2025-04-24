import streamlit as st



def dashboard():
    """Display task history and chat sidebar"""
    # Display task history header
    st.markdown("<h2>Task History</h2>", unsafe_allow_html=True)
    
    # Create mock task history data
    if 'task_history' not in st.session_state:
        # Initialize with some mock history data
        st.session_state.task_history = [
            {
                "id": "tx-001",
                "date": "2023-09-15",
                "prompt": "Analyze APY rates for Uniswap pools",
                "services": ["1815", "1966"],
                "status": "completed"
            },
            {
                "id": "tx-002",
                "date": "2023-09-20",
                "prompt": "Compare gas fees across different L2 solutions",
                "services": ["1722", "1999"],
                "status": "completed"
            },
            {
                "id": "tx-003",
                "date": "2023-09-27",
                "prompt": "Find arbitrage opportunities between DEXs",
                "services": ["1983", "2010"],
                "status": "error"
            }
        ]
    
    # Display task history in a table with styled cards
    if not st.session_state.task_history:
        st.info("You don't have any task history yet. Create a new request to get started.")
    else:
        for task in st.session_state.task_history:
            # Determine the status color
            status_color = "#4CAF50" if task["status"] == "completed" else "#F44336"
            
            # Create a styled card for each task
            st.markdown(f"""
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: white;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 0.9rem; color: #555;">{task["date"]}</span>
                    <span style="background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem;">{task["status"].title()}</span>
                </div>
                <h4 style="margin-top: 0; margin-bottom: 10px;">{task["prompt"]}</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px;">
                    {' '.join([f'<span style="background-color: #f0f0f0; color: #333; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">Service {service_id}</span>' for service_id in task["services"]])}
                </div>
                <div style="font-family: monospace; font-size: 0.85rem; color: #666; margin-bottom: 10px;">Transaction ID: {task["id"]}</div>
            </div>
            """, unsafe_allow_html=True)

    # Button to create a new request
    if st.button("Create New Request"):
        st.session_state.page = 'create_request'
        st.rerun()
    
    # Sidebar for chats
    st.sidebar.markdown("<h3>Chats</h3>", unsafe_allow_html=True)
    st.sidebar.write("Chat history will be displayed here.")

# src/components/reasoning_feedback.py
from typing import Dict, List, Any, Optional, Callable
import streamlit as st
import time

def display_manual_service_selection(recommended_services):
    """Display UI for manual service selection."""
    st.markdown("## Manual Service Selection")
    st.write("Select the services you want to use:")
    
    # Initialize selected services if not already done
    if 'manually_selected_services' not in st.session_state:
        st.session_state.manually_selected_services = []
    
    # Group services by category
    service_categories = {}
    for service in recommended_services:
        category = service.get('category', 'Other')
        if category not in service_categories:
            service_categories[category] = []
        service_categories[category].append(service)
    
    # Add a few more services for variety
    more_services = [
        {"name": "DefiLlama Integration", "description": "Access comprehensive DeFi data and metrics", "service_id": "2001", "category": "Data", "cost": 8},
        {"name": "Token Metrics Analysis", "description": "Advanced token metrics and fundamentals analysis", "service_id": "2002", "category": "Analysis", "cost": 12},
        {"name": "Risk Assessment Tool", "description": "Evaluate project risk profiles and security concerns", "service_id": "2003", "category": "Risk", "cost": 15}
    ]
    
    for service in more_services:
        category = service.get('category', 'Other')
        if category not in service_categories:
            service_categories[category] = []
        service_categories[category].append(service)
    
    # Create a form for service selection
    with st.form("service_selection_form"):
        selected_service_ids = []
        
        # Display each category
        for category, services in service_categories.items():
            st.markdown(f"### {category}")
            
            for service in services:
                service_id = service.get('service_id')
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    selected = st.checkbox(
                        f"{service.get('name')} - {service.get('description', '')}",
                        key=f"select_{service_id}"
                    )
                
                with col2:
                    st.write(f"**{service.get('cost', 0)} OLAS**")
                
                if selected:
                    selected_service_ids.append(service_id)
        
        # Calculate total cost of selected services
        all_services = [s for services in service_categories.values() for s in services]
        selected_services = [s for s in all_services if s.get('service_id') in selected_service_ids]
        total_cost = sum(service.get('cost', 0) for service in selected_services)
        
        st.markdown(f"### Total Cost: {total_cost} OLAS")
        
        submit_button = st.form_submit_button("Proceed to Execution", use_container_width=True)
        
        if submit_button:
            st.session_state.selected_services = selected_services
            st.session_state.total_cost = total_cost
            
            # Display execution status
            from utils.execution_status import ExecutionStatus
            execution_status = ExecutionStatus()
            execution_status.render()



def reasoning_feedback_component(
    reasoning_data: Dict[str, Any], 
    on_feedback: Optional[Callable] = None
) -> None:
    """
    Display agent reasoning feedback and collect user sentiment.
    
    Args:
        reasoning_data: Dictionary containing reasoning steps and recommendations
        on_feedback: Optional callback function when feedback is submitted
    """
    st.markdown("## Agent Reasoning Process")
    st.write("The AI agent is analyzing your query to determine the best services to use.")
    
    # Initialize feedback in session state if not already present
    if "reasoning_feedback" not in st.session_state:
        st.session_state.reasoning_feedback = None
    
    # Initialize feedback submitted flag
    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False
    
    # Display reasoning steps
    reasoning_steps = reasoning_data.get("reasoning_steps", [])
    
    for i, step in enumerate(reasoning_steps):
        # Create an expander for each step
        with st.expander(f"Step {i+1}: {step.get('step', 'Unknown step')}", expanded=True):
            st.write(step.get("reasoning", "No reasoning available"))
            
            # Simulate thinking with a progress indicator if in progress
            if step.get("status") == "in_progress":
                st.info("Thinking...")

            
            # Show completion status
            if step.get("status") == "completed":
                st.success("Completed")
            elif step.get("status") == "in_progress":
                st.info("In progress...")
            else:
                st.write("Pending")
    
    # Display recommended services
    st.markdown("## Recommended Services")
    st.write("Based on the reasoning process, the following services are recommended:")
    
    recommended_services = reasoning_data.get("recommended_services", [])
    
    if not recommended_services:
        st.warning("No services were recommended. Please try a different query.")
        return
    
    # Display services in a grid
    cols = st.columns(min(len(recommended_services), 3))
    
    for i, service in enumerate(recommended_services):
        col_index = i % len(cols)
        with cols[col_index]:
            # Create a card-like display for each service
            st.markdown(f"""
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4>{service.get('name', 'Unknown Service')}</h4>
                <p style="font-size: 0.9em;">{service.get('description', 'No description available')[:150]}...</p>
                <p style="font-size: 0.8em; color: #666;">
                    Service ID: {service.get('service_id', 'N/A')}<br>
                    Category: {service.get('category', 'General')}<br>
                    Cost: {service.get('cost', 0)} xDAI
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Calculate and display total cost
    total_cost = sum(service.get('cost', 0) for service in recommended_services)
    st.markdown(f"### Total Cost: {total_cost} OLAS")
    st.write("These OLAS tokens will be staked during task execution.")

    # Display a cost breakdown if there are multiple services
    if len(recommended_services) > 1:
        with st.expander("Cost Breakdown"):
            for service in recommended_services:
                st.write(f"- {service.get('name', 'Service')}: {service.get('cost', 0)} OLAS")

    # Add explanatory note about staking
    st.info("""
    **Note on OLAS Staking**: The specified OLAS tokens will be staked during task execution.
    These tokens are returned upon successful completion, with potential rewards for high-quality results.
    A portion may be slashed if verification fails.
    """)

    # Add overall feedback section after all reasoning steps and recommended services
    st.markdown("### Was this reasoning and service selection helpful?")
    
    # If feedback has been submitted, just show a thank you message
    if st.session_state.feedback_submitted:
        st.success("Thanks for your feedback! We'll use it to improve our reasoning system.")
    else:
        # Create columns for feedback options and text
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Radio button for basic sentiment
            feedback_options = ["👍 Helpful", "👎 Not helpful", "🤔 Neutral"]
            feedback = st.radio(
                "Select your feedback:",
                options=feedback_options,
                horizontal=True,
                key="overall_feedback"
            )
        
        with col2:
            # Optional text feedback
            feedback_text = st.text_area(
                "Additional comments (optional):",
                key="feedback_text",
                height=80
            )
        
        # Submit button for feedback
        if st.button("Submit Feedback", use_container_width=True, key="submit_feedback"):
            # Determine numeric value for feedback (for compatibility with existing code)
            feedback_value = 1  # Default to neutral
            
            if feedback == "👍 Helpful":
                feedback_value = 2
            elif feedback == "👎 Not helpful":
                feedback_value = 0
            else:
                feedback_value = 1
                
            # Store feedback in session state
            st.session_state.reasoning_feedback = {
                "sentiment": feedback_value,
                "text": feedback_text,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            # Set submitted flag
            st.session_state.feedback_submitted = True
            
            # Call the callback function if provided
            if on_feedback:
                on_feedback(feedback_value, feedback_text)
            
            # Rerun to update UI
            st.rerun()
    
    # Buttons for service selection
    st.markdown("### Continue with the recommended services?")
    
    # Add a button to proceed with the recommended services
    recommended_services = reasoning_data.get("recommended_services", [])
    if st.button("Use Recommended Services", use_container_width=True):
        st.session_state.selected_services = recommended_services
        st.session_state.reasoning_complete = True
        # Calculate total OLAS cost
        total_cost = sum(service.get('cost', 0) for service in recommended_services)
        st.session_state.total_cost = total_cost
        # Instead of st.rerun, display info and proceed
        st.success(f"Selected {len(recommended_services)} services. Proceeding to execution...")
        # Show the execution status component directly
        from utils.execution_status import ExecutionStatus
        execution_status = ExecutionStatus()
        execution_status.render()

    # Add an option to manually select services
    if st.button("Select Services Manually", use_container_width=True):
        st.session_state.reasoning_complete = True
        st.session_state.manual_selection = True
        # Instead of st.rerun, update UI
        st.info("Proceeding to manual service selection...")
        # Show the service selection UI
        display_manual_service_selection(recommended_services)


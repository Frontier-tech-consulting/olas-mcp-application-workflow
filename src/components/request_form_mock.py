# src/components/request_form.py
import streamlit as st
import time
import random
import uuid
from typing import Dict, Any, List, Callable
from datetime import datetime

class RequestForm:
    """Component for creating a new request."""
    
    def __init__(self, submit_callback: Callable, user_email: str = ""):
        """
        Initialize the request form component.
        
        Args:
            submit_callback: Callback function to handle form submission
            user_email: User's email address
        """
        self.submit_callback = submit_callback
        self.user_email = user_email
        
        # Initialize the MockMechService
        from src.services.mock_mech_service import MockMechService
        self.mech_service = MockMechService()
    
    def render(self):
        """Render the request form component"""
        st.markdown("## Create a New Request")
        
        # Input for the request prompt
        st.markdown("### Enter your request:")
        prompt = st.text_area(
            "Describe what you want to analyze:",
            height=150,
            key="prompt_input",
            placeholder="Example: Analyze current yield farming opportunities across Uniswap, Curve, and Compound"
        )
        
        # When user submits the prompt
        if st.button("Analyze Request", use_container_width=True):
            if not prompt or len(prompt.strip()) < 10:
                st.error("Please enter a more detailed request (at least 10 characters)")
                return
            
            # Store the prompt in session state
            st.session_state.prompt = prompt
            
            # Get available services
            services = self.mech_service.get_available_services()
            
            # Set the flag to show reasoning
            st.session_state.show_reasoning = True
            
            # Display the reasoning agent
            self.render_reasoning_agent(prompt, services)
            
        # Handle selection if reasoning is complete
        if st.session_state.get('reasoning_complete', False):
            if st.session_state.get('manual_selection', False):
                # Handle manual selection
                self._render_manual_service_selection()
            else:
                # Handle form submission with selected services
                self.handle_form_submission()
    
    def _render_prompt_input(self):
        """Render the prompt input form."""
        st.write("Enter your query to analyze a DeFi strategy, cryptocurrency, or market condition.")
        
        prompt = st.text_area(
            "Enter your query",
            height=150,
            placeholder="Example: Analyze the current APY rates for Uniswap V3 DAI/USDC pools and compare with other DEXs",
            key="prompt_input",
            help="Be specific about what you're looking for to get better results"
        )
        
        if st.button("Analyze Query", use_container_width=True):
            if not prompt or len(prompt.strip()) < 10:
                st.error("Please enter a more detailed query (at least 10 characters).")
                return
            
            # Store the prompt in session state
            st.session_state.prompt = prompt
            
            # Get agent reasoning feedback
            with st.spinner("Analyzing your query..."):
                reasoning_response = self.mech_service.analyze_query(prompt)
                st.session_state.reasoning_response = reasoning_response
            
            # Handle feedback submissions - updated to match new feedback format
            def handle_reasoning_feedback(feedback_value, feedback_text=None):
                # Store feedback for later analysis
                feedback_data = {
                    "query": prompt,
                    "feedback_value": feedback_value,
                    "feedback_text": feedback_text,
                    "timestamp": datetime.now().isoformat()
                }
                if "feedback_history" not in st.session_state:
                    st.session_state.feedback_history = []
                st.session_state.feedback_history.append(feedback_data)
            
            # Render the reasoning feedback component
            from src.components.reasoning_feedback import reasoning_feedback_component
            reasoning_feedback_component(
                reasoning_data=reasoning_response,
                on_feedback=handle_reasoning_feedback
            )
    
    def _render_manual_service_selection(self):
        """Render manual service selection UI."""
        st.markdown("## Select Services")
        st.write("Select the services you want to use for your query:")
        
        # Show the prompt
        st.info(f"Your query: {st.session_state.prompt}")
        
        # Get available services
        available_services = self.mech_service.get_available_services()
        
        # Group services by category
        services_by_category = {}
        for service in available_services:
            category = service.get("category", "General")
            if category not in services_by_category:
                services_by_category[category] = []
            services_by_category[category].append(service)
        
        # Create a multi-select for each category
        selected_services = []
        
        for category, services in services_by_category.items():
            st.markdown(f"### {category}")
            
            # Create a grid of 2 or 3 columns for services
            cols = st.columns(min(len(services), 3))
            
            for i, service in enumerate(services):
                col_index = i % len(cols)
                with cols[col_index]:
                    # Create a checkbox for each service
                    selected = st.checkbox(
                        f"{service.get('name', 'Unknown Service')}",
                        key=f"service_{service.get('id', i)}",
                        help=f"{service.get('description', 'No description')} | Cost: {service.get('cost', 0)} xDAI"
                    )
                    
                    if selected:
                        selected_services.append(service)
        
        # Calculate total cost
        total_cost = sum(float(service.get("cost", 0)) for service in selected_services)
        
        # Display summary
        st.markdown("### Summary")
        st.markdown(f"**Total Services Selected:** {len(selected_services)}")
        st.markdown(f"**Total Cost:** {total_cost:.3f} xDAI")
        
        # Create a submit button
        if st.button("Submit Request", use_container_width=True, disabled=len(selected_services) == 0):
            if len(selected_services) == 0:
                st.error("Please select at least one service")
                return
            
            # Create a new request
            request = {
                "prompt": st.session_state.prompt,
                "user_email": self.user_email,
                "selected_services": selected_services,
                "total_cost": total_cost,
                "timestamp": datetime.now().isoformat()
            }
            
            # Submit the request
            self.submit_callback(request)
        
        # Back button
        if st.button("Back", use_container_width=True):
            st.session_state.reasoning_complete = False
            st.session_state.manual_selection = False
            st.rerun()
    
    def _render_service_confirmation(self):
        """Render service confirmation UI."""
        st.markdown("## Confirm Selected Services")
        st.write("The following services have been recommended based on your query:")
        
        # Show the prompt
        st.info(f"Your query: {st.session_state.prompt}")
        
        # Get selected services
        selected_services = st.session_state.selected_services
        
        # Display selected services
        for service in selected_services:
            with st.expander(f"{service.get('name', 'Unknown Service')} - {service.get('cost', 0)} xDAI", expanded=True):
                st.write(service.get("description", "No description available"))
                st.write(f"Service ID: {service.get('service_id', 'N/A')}")
                st.write(f"Category: {service.get('category', 'General')}")
        
        # Calculate total cost
        total_cost = sum(float(service.get("cost", 0)) for service in selected_services)
        
        # Display summary
        st.markdown("### Summary")
        st.markdown(f"**Total Services Selected:** {len(selected_services)}")
        st.markdown(f"**Total Cost:** {total_cost:.3f} xDAI")
        
        # Create submit and edit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Submit Request", use_container_width=True):
                # Create a new request
                request = {
                    "prompt": st.session_state.prompt,
                    "user_email": self.user_email,
                    "selected_services": selected_services,
                    "total_cost": total_cost,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Submit the request
                self.submit_callback(request)
        
        with col2:
            if st.button("Edit Selection", use_container_width=True):
                st.session_state.manual_selection = True
                st.rerun()
        
        # Back button
        if st.button("Back", use_container_width=True):
            st.session_state.reasoning_complete = False
            st.rerun()
    
    def generate_reasoning(self, request_text: str, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate reasoning for service selection based on the request text
        
        Args:
            request_text: The text of the request
            services: List of available services
            
        Returns:
            Dict containing reasoning steps and recommended services
        """
        try:
            # Simulate reasoning with mock data for demonstration
            reasoning_steps = []
            
            # Add initial query analysis step
            reasoning_steps.append({
                "step": "Query Analysis",
                "reasoning": f"Analyzing query: '{request_text}'\n\nThe query appears to be about financial data and market analysis.",
                "status": "completed"
            })
            
            # Add service matching step
            reasoning_steps.append({
                "step": "Service Matching",
                "reasoning": "Matching query requirements with available services...\n\n• Need for market data extraction\n• Need for financial analysis\n• Need for result visualization",
                "status": "completed"
            })
            
            # Select recommended services based on query content
            recommended_services = []
            keywords = request_text.lower().split()
            
            for service in services:
                service_id = service.get('service_id') or service.get('id')
                if not service_id:
                    continue
                    
                # Simple keyword matching for demo purposes
                service_name = service.get('name', '').lower()
                service_desc = service.get('description', '').lower()
                
                # Generate category if not present
                if 'category' not in service:
                    if any(word in service_name or word in service_desc for word in ['analytics', 'analysis']):
                        service['category'] = 'Analysis'
                    elif any(word in service_name or word in service_desc for word in ['data', 'feed']):
                        service['category'] = 'Data'
                    else:
                        service['category'] = 'Other'
                
                # Generate cost if not present
                if 'cost' not in service:
                    service['cost'] = float(service.get('price', 10.0))
                    
                # Simple matching algorithm
                relevance_score = 0
                for keyword in keywords:
                    if keyword in service_name or keyword in service_desc:
                        relevance_score += 1
                
                # Set a threshold for inclusion
                if relevance_score > 0 or len(recommended_services) < 2:  # Ensure at least some services
                    recommended_services.append(service)
                    
                # Limit to 3 services for simplicity
                if len(recommended_services) >= 3:
                    break
            
            # Add service selection step
            service_names = [s.get('name', f"Service {s.get('service_id')}") for s in recommended_services]
            reasoning_steps.append({
                "step": "Selected Services",
                "reasoning": f"Based on the query analysis, the following services are recommended:\n\n" +
                             "\n".join([f"• {name}" for name in service_names]),
                "status": "completed"
            })
            
            return {
                "reasoning_steps": reasoning_steps,
                "recommended_services": recommended_services
            }
            
        except Exception as e:
            st.error(f"Error generating reasoning: {str(e)}")
            return {"reasoning_steps": [], "recommended_services": []}
    
    def render_reasoning_agent(self, request_text: str, services: List[Dict[str, Any]]) -> None:
        """Render the reasoning agent and update session state"""
        # Generate reasoning data
        reasoning_data = self.generate_reasoning(request_text, services)
        
        # Store in session state
        st.session_state.reasoning_data = reasoning_data
        st.session_state.reasoning_steps = reasoning_data.get("reasoning_steps", [])
        st.session_state.recommended_services = reasoning_data.get("recommended_services", [])
        
        # Display the reasoning feedback component
        from src.components.reasoning_feedback import reasoning_feedback_component
        
        # Define callback for feedback submission
        def on_feedback_submitted(sentiment_value, feedback_text):
            st.session_state.feedback_data = {
                "sentiment": sentiment_value,
                "text": feedback_text,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        
        # Display the component with reasoning data
        reasoning_feedback_component(
            reasoning_data=reasoning_data,
            on_feedback=on_feedback_submitted
        )
    
    def handle_form_submission(self):
        """Handle form submission with service selection"""
        # Check if we have selected services in session state
        if st.session_state.get('selected_services'):
            selected_services = st.session_state.selected_services
            total_cost = st.session_state.get('total_cost', 0)
            
            # Create a complete request object
            request = {
                "prompt": st.session_state.get('prompt', ''),
                "selected_services": selected_services,
                "total_cost": total_cost,
                "timestamp": datetime.now().isoformat(),
                "transaction_id": f"tx_{uuid.uuid4().hex[:8]}"
            }
            
            # Call the submit callback
            if self.submit_callback:
                self.submit_callback(request)
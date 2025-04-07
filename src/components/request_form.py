import streamlit as st
import json
import os
import time
import random
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from ..services.mcp_service import MCPService
from ..services.defillama_api import DefiLlamaAPI
from ..models.request import Request
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.messages import SystemMessage, HumanMessage
import datetime

# Load environment variables
load_dotenv()

class RequestForm:
    """Component for creating and submitting requests"""
    
    def __init__(self, submit_callback, user_email):
        """Initialize the RequestForm component"""
        self.submit_callback = submit_callback
        self.user_email = user_email
        # Create an instance of MCPService for handling data
        self.mcp_service_instance = MCPService()
        # Get a reference to the defillama_api instance
        self.defillama_api = getattr(self.mcp_service_instance, 'defillama_api', None)
        # Initialize OpenAI client with explicit token limits
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            max_tokens=1000,  # Limit output tokens
            api_key=os.getenv("OPENAI_API_KEY"),
            streaming=True
        )
    
    def update_request_text(self, text):
        """Update the request text in session state"""
        st.session_state.request_text = text
    
    def generate_reasoning(self, request_text: str, services: List[Dict[str, Any]]) -> List[str]:
        """
        Generate reasoning for service selection based on the request text
        
        Args:
            request_text: The text of the request
            services: List of available services
            
        Returns:
            List of reasoning steps
        """
        try:
            # Create a dictionary mapping service IDs to their descriptions
            service_descriptions = {}
            available_service_ids = []
            
            for service in services:
                service_id = service.get('service_id', '')
                description = service.get('description', '')
                if service_id and description:
                    service_descriptions[service_id] = description
                    available_service_ids.append(service_id)
            
            if not available_service_ids:
                return ["No services available for selection."]
                
            # Get DeFi Llama data using first service ID as default (will be overridden by reasoning)
            defillama_results = None
            if self.defillama_api:
                try:
                    # Use the first service ID if available
                    service_id = available_service_ids[0] if available_service_ids else "default_service"
                    defillama_results = self.defillama_api.process_query(request_text, service_id)
                    # Store in session state for later use
                    st.session_state.defillama_results = defillama_results
                except Exception as e:
                    print(f"Error fetching DeFi Llama data: {e}")
            
            # Create a more informative prompt that includes DeFi Llama data if available
            defillama_summary = ""
            if defillama_results:
                defillama_summary = f"\nDeFi Llama Analysis:\n"
                if "summary" in defillama_results:
                    defillama_summary += f"- {defillama_results['summary']}\n"
                if "aggregated_data" in defillama_results and defillama_results["aggregated_data"]:
                    for key, value in defillama_results["aggregated_data"].items():
                        if key == "top_protocols" and isinstance(value, list) and len(value) > 0:
                            defillama_summary += f"- Top protocols include: {', '.join([p.get('name', 'unknown') for p in value[:3]])}\n"
            
            # Prompt the AI to recommend 2-3 different services based on the query
            # The prompt specifically instructs the AI to consider different IDs
            prompt = f"""
            You are a service selector for Olas MCP. Your job is to recommend 2-3 of the most suitable services to fulfill a user's request.
            
            Here are the available services:
            {json.dumps(service_descriptions, indent=2)}
            
            User request: {request_text}
            {defillama_summary}
            
            Provide your recommendation in this format:
            
            Step 1: Analyze the user's request.
            Step 2: Determine the type of analysis needed.
            Step 3: Selected Services:
            • Service {available_service_ids[0]}: Brief explanation of why this service is suitable.
            • Service {available_service_ids[1 % len(available_service_ids)]}: Brief explanation of why this service is suitable.
            
            Make sure to consider ALL available services, rather than defaulting to just Service 1722.
            IMPORTANT: Recommend 2-3 different service IDs from the available options with brief bullet points explaining why each is suitable.
            Choose services that best match the user's specific request based on their descriptions.
            """
            
            # Initialize OpenAI client
            try:
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                # Make API call with new format
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600,
                    temperature=0.3
                )
                
                # Extract the response content
                reasoning_text = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error calling OpenAI API: {str(e)}")
                # Provide a fallback response recommending all services
                fallback_steps = [
                    "Step 1: Analyze the user's request.",
                    "Step 2: Due to API limitations, using fallback recommendation approach.",
                    f"Selected Services:\n• Service {available_service_ids[0]}: Recommended as a suitable service for the request.\n"
                ]
                if len(available_service_ids) > 1:
                    fallback_steps[-1] += f"• Service {available_service_ids[1]}: Also recommended as a suitable service for the request."
                
                return fallback_steps
            
            # Split the response into individual steps
            steps = []
            current_step = ""
            
            for line in reasoning_text.split('\n'):
                line = line.strip()
                if line.startswith("Step "):
                    if current_step:
                        steps.append(current_step)
                    current_step = line
                elif "Selected Services" in line and not current_step.startswith("Step "):
                    if current_step:
                        steps.append(current_step)
                    current_step = line
                elif line:
                    if current_step:
                        current_step += "\n" + line
                    else:
                        current_step = line
            
            # Add the last step if it exists
            if current_step:
                steps.append(current_step)
            
            # If no steps were found, use the entire text as a single step
            if not steps:
                steps = [reasoning_text]
            
            # Extract recommended service IDs
            recommended_services = []
            for step in steps:
                if "Selected Services" in step:
                    # Look for service IDs in the format "Service XXXX"
                    service_ids = re.findall(r'Service (\d+)', step)
                    if service_ids:
                        recommended_services.extend(service_ids)
            
            # Store the recommended services
            st.session_state.recommended_services = recommended_services
            
            # Return the steps
            return steps
        except Exception as e:
            # Log the error
            print(f"Error generating reasoning: {str(e)}")
            return [f"Error analyzing request: {str(e)}"]
    
    def render_reasoning_agent(self, request_text: str, services: List[Dict[str, Any]]) -> None:
        """Render the reasoning agent and update session state"""
        # Generate reasoning steps
        reasoning_steps = self.generate_reasoning(request_text, services)
        
        # Process the reasoning steps
        if reasoning_steps:
            # Display reasoning steps
            self.display_reasoning_steps(reasoning_steps)
            
            # Store in session state
            st.session_state.reasoning_response = reasoning_steps
            st.session_state.reasoning_complete = True
            
            # Extract recommended service IDs
            recommended_services = self.extract_recommended_services(reasoning_steps)
            st.session_state.recommended_services = recommended_services
        else:
            st.error("Could not generate reasoning for your request. Using default recommendations.")
            st.session_state.reasoning_complete = True
            st.session_state.recommended_services = []  # Use default services

    def display_reasoning_steps(self, reasoning_steps: List[str]) -> None:
        """Display reasoning steps in a styled container"""
        st.markdown("## Request Analysis")
        st.markdown("Our system has analyzed your request and prepared the following reasoning:")
        
        # Create a styled container for all reasoning steps
        st.markdown("""
        <div class="reasoning-container">
        """, unsafe_allow_html=True)
        
        # Display each reasoning step with styled container
        for i, step in enumerate(reasoning_steps):
            step_header, step_content = self.format_reasoning_step(step, i)
            
            # Add styled step to UI
            st.markdown(f"""
            <div class="reasoning-step">
                <div class="reasoning-header">
                    {step_header}
                </div>
                <div class="reasoning-content">
                    {step_content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Close the reasoning container
        st.markdown("</div>", unsafe_allow_html=True)

    def format_reasoning_step(self, step: str, index: int) -> (str, str):
        """Format a reasoning step for display"""
        step_header = f"Step {index + 1}"
        step_content = step
        
        if step.startswith("Step "):
            # Extract step name for header
            parts = step.split("\n", 1)
            step_header = parts[0]
            step_content = parts[1] if len(parts) > 1 else ""
        elif "Selected Services" in step:
            step_header = "Selected Services"
            step_content = step.replace("Selected Services:", "").strip()
        
        # Format content - ensure bullet points are preserved
        formatted_content = step_content.replace("\n• ", "<br>• ")
        formatted_content = formatted_content.replace("\n* ", "<br>* ")
        formatted_content = formatted_content.replace("\n- ", "<br>- ")
        
        return step_header, formatted_content

    def extract_recommended_services(self, reasoning_steps: List[str]) -> List[str]:
        """Extract recommended service IDs from reasoning steps"""
        recommended_services = []
        for step in reasoning_steps:
            if "Selected Services" in step:
                # Look for service IDs in the format "Service XXXX"
                service_ids = re.findall(r'Service (\d+)', step)
                if service_ids:
                    recommended_services.extend(service_ids)
        return recommended_services

    def display_service_recommendations(self, reasoning_steps: List[str]):
        """
        Display service recommendations and allow user to select services.
        
        Args:
            reasoning_steps: List of reasoning steps from the reasoning agent
        """
        # Get services from MCP service
        mcp_service = self.mcp_service_instance
        all_services = mcp_service.get_available_services()
        
        # Extract recommended service IDs from reasoning steps
        if 'recommended_services' not in st.session_state:
            recommended_service_ids = self.extract_recommended_services(reasoning_steps)
            # Store in session state to avoid recalculating
            st.session_state.recommended_services = recommended_service_ids
        else:
            recommended_service_ids = st.session_state.recommended_services
        
        # Initialize checkbox state if not already done
        if 'checkboxes' not in st.session_state:
            st.session_state.checkboxes = {}
        
        # Select services based on IDs
        recommended_services = []
        other_services = []
        
        for service in all_services:
            service_id = service.get('id') or service.get('service_id')
            # Generate a unique ID if service_id is None
            if not service_id:
                service_id = f"service-{hash(str(service))}"
                
            # Ensure the service has a price
            if 'price' not in service:
                service['price'] = float(service.get('cost', 10))
            
            if service_id in recommended_service_ids:
                recommended_services.append(service)
            else:
                other_services.append(service)
        
        # Divide the page into sections
        st.markdown("### Recommended Services")
        
        # Initialize variables to track selections
        selected_services = []
        total_cost = 0.0
        
        # Display recommended services
        if recommended_services:
            for service in recommended_services:
                self._render_service_card(service, selected_services, total_cost)
        else:
            st.info("No services were specifically recommended based on your request.")
        
        # Display other available services
        st.markdown("### Other Available Services")
        for service in other_services:
            self._render_service_card(service, selected_services, total_cost)
        
        # Recalculate total cost based on current selections
        total_cost = sum(service.get('price', 10.0) for service in selected_services)
        
        # Display payment summary if services are selected
        if selected_services:
            st.markdown("### Payment Summary")
            st.markdown(f"**Total Cost:** {total_cost:.2f} OLAS")
            
            # Create two columns for buttons
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("Proceed to Payment", key="proceed_to_payment"):
                    # Set payment confirmation in session state
                    st.session_state.payment_confirmed = True
                    
                    # Call handle payment to create request object
                    self.handle_payment_confirmation(selected_services)
                    
                    # Navigate to execution page
                    st.session_state.page = 'execution'
                    st.rerun()
            
            with col2:
                if st.button("Reset Selections", key="reset_selections"):
                    # Reset checkboxes and selections
                    st.session_state.checkboxes = {}
                    st.rerun()
        else:
            st.info("Select at least one service to proceed.")

    def _render_service_card(self, service, selected_services, total_cost):
        """
        Render a single service card with checkbox.
        
        Args:
            service: Service dictionary to render
            selected_services: List to append selected services to
            total_cost: Running total cost value (not used, cost is recalculated later)
        """
        service_id = service.get('id') or service.get('service_id')
        # Generate a unique ID if service_id is None
        if not service_id:
            service_id = f"service-{hash(str(service))}"
            
        service_name = service.get('name') or service.get('description', 'Unknown Service')
        service_price = service.get('price', 10.0)
        checkbox_key = f"checkbox_{service_id}"
        
        # Display service card
        st.markdown(f"""
        <div class="recommended-service">
            <h4>{service_name} (ID: {service_id})</h4>
            <p>{service.get('description', '')}</p>
            <p>
                <span class="service-price">Cost: {service_price} OLAS</span>
                <span class="service-mech-address">Mech: {service.get('mech_address', 'N/A')}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get the initial state without creating a recursive reference
        initial_state = False
        if checkbox_key in st.session_state.checkboxes:
            initial_state = st.session_state.checkboxes[checkbox_key]
        
        # Add checkbox for selection
        is_checked = st.checkbox(
            f"Select Service {service_id}",
            value=initial_state,
            key=checkbox_key
        )
        
        # Update the checkbox state in session_state
        st.session_state.checkboxes[checkbox_key] = is_checked
        
        # Update selected services if checked
        if is_checked:
            selected_services.append(service)

    def handle_payment_confirmation(self, selected_services: List[Dict[str, Any]]):
        """Handle payment confirmation and transition to execution page"""
        try:
            # Calculate total cost from selected services
            total_cost_value = sum(service.get('price', 10) for service in selected_services)
            total_cost = f"{total_cost_value:.2f} OLAS"
            
            # Create a dictionary request object with the prompt and selected services
            request = {
                "prompt": st.session_state.request_text,
                "selected_services": selected_services,
                "user_email": self.user_email,
                "total_cost": total_cost_value,
                "submitted_at": datetime.datetime.now().isoformat()
            }
            
            # Submit the request with a spinner to indicate processing
            with st.spinner("Preparing payment..."):
                # Store the request in session state for the execution page
                st.session_state.current_request = request
                
                # Set up payment processing flags for app.py to handle
                st.session_state.payment_processing = True
                st.session_state.payment_completed = False
                
                # Submit the request directly to obtain a transaction ID
                if self.submit_callback:
                    try:
                        self.submit_callback(request)
                    except Exception as e:
                        st.warning(f"Callback warning: {str(e)}")
                
                # Log this request regardless of callback success
                if "submitted_requests" not in st.session_state:
                    st.session_state.submitted_requests = []
                
                # Add to submitted requests list if not already there
                if request not in st.session_state.submitted_requests:
                    st.session_state.submitted_requests.append(request)
                
                # Navigate to execution page
                st.session_state.page = 'execution'
                st.rerun()
                
        except Exception as e:
            st.error(f"Error submitting request: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

    def render(self):
        """Render the request form component"""
        
        # Check if we should access session state
        # NOTE: This is needed to work with Streamlit's execution flow
        if 'page' not in st.session_state:
            st.session_state.page = 'create_request'
            
        # Get data needed for the form
        mcp_service = self.mcp_service_instance
        services = mcp_service.get_available_services()
        infrastructure_data = mcp_service.get_infrastructure_stats()
        
        # Display header
        st.markdown("""
        <div class="request-form-header">
            <h2>Submit New Request</h2>
            <p>Submit your request for analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add custom CSS for styling
        st.markdown("""
        <style>
            /* Form styles */
            textarea.stTextArea {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            /* Button styles */
            .stButton button {
                background-color: #000000 !important; 
                color: #ffffff !important;
                border: none !important;
                padding: 0.5rem 1rem !important;
                border-radius: 4px !important;
                transition: all 0.3s;
                font-weight: 600 !important;
                width: 100%; /* Make buttons fill their container */
            }
            .stButton button:hover {
                background-color: #333333 !important;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            
            /* Button text styling - more comprehensive selectors */
            .stButton button p, 
            .stButton button span,
            div[data-testid="StyledLinkIconContainer"] p,
            div[data-testid="StyledLinkIconContainer"] span,
            button[kind="primary"] p,
            button[kind="secondary"] p,
            div[data-baseweb="button"] p,
            div[data-baseweb="button"] span {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            
            /* Aggressive button text fixing - target all button children */
            button *, button p, button span, button div {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            
            /* Fix for Streamlit button text */
            button[kind="primaryFormSubmit"] p,
            button[kind="secondaryFormSubmit"] p,
            button[data-baseweb="button"] p,
            [data-testid="baseButton-secondary"] p,
            [data-testid="baseButton-primary"] p,
            [data-testid="StyledFullScreenButton"] span,
            button[data-testid*="StyledButton"] span {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            
            /* Additional selector for any remaining buttons */
            div[role="button"] p, 
            div[role="button"] span {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            
            /* Make sure task history button is styled properly */
            button[key="task_history_button"] {
                background-color: #333333 !important;
                border: 1px solid #000000 !important;
            }
            
            button[key="task_history_button"] p,
            button[key="task_history_button"] span {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            
            /* Progress bar */
            .stProgress > div > div {
                background-color: #000000;
            }
            
            /* Service card styling */
            .recommended-service {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                transition: all 0.2s ease;
            }
            .recommended-service:hover {
                box-shadow: 0 3px 8px rgba(0,0,0,0.15);
            }
            .service-price {
                background-color: #f0f0f0;
                color: #000000;
                padding: 5px 10px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.9rem;
            }
            .service-mech-address {
                font-family: monospace;
                font-size: 0.85rem;
                color: #555;
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 3px;
            }
            
            /* Checkbox styling */
            [data-testid="stCheckbox"] {
                margin-top: 10px;
            }
            [data-testid="stCheckbox"] > label {
                font-weight: 600;
            }
            
            /* Results container */
            .results-container {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
            }
            
            /* Reasoning display styling */
            .reasoning-container {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 30px;
                background-color: #f9f9ff;
            }
            
            .reasoning-step {
                margin-bottom: 15px;
                border-left: 3px solid #000000;
                padding-left: 15px;
            }
            
            .reasoning-header {
                font-weight: bold;
                font-size: 1.1rem;
                margin-bottom: 8px;
                color: #000000;
            }
            
            .reasoning-content {
                background-color: white;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #e6e6e6;
                line-height: 1.6;
            }
            
            /* Improve bullet point display */
            .reasoning-content ul {
                padding-left: 20px;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            
            .reasoning-content li {
                margin-bottom: 5px;
            }
            
            /* Payment button - make it stand out */
            button[key="payment_button"] {
                background-color: #1a8917 !important;  /* Green for payment */
                font-size: 1.1rem !important;
                padding: 0.6rem 1.2rem !important;
            }
            
            button[key="payment_button"]:hover {
                background-color: #146612 !important;
                box-shadow: 0 3px 8px rgba(0,0,0,0.3) !important;
            }
            
            /* Ensure payment button text is white */
            button[key="payment_button"] p {
                color: #ffffff !important;
                font-weight: 600 !important;
                font-size: 1.1rem !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Initialize session state variables if they don't exist
        if 'checkboxes' not in st.session_state:
            st.session_state.checkboxes = {}
        if 'selected_services' not in st.session_state:
            st.session_state.selected_services = []
        if 'reasoning_complete' not in st.session_state:
            st.session_state.reasoning_complete = False
        if 'reasoning_response' not in st.session_state:
            st.session_state.reasoning_response = []
        if 'payment_confirmed' not in st.session_state:
            st.session_state.payment_confirmed = False
        if 'total_cost' not in st.session_state:
            st.session_state.total_cost = 0
        if 'request_submitted' not in st.session_state:
            st.session_state.request_submitted = False
        if 'transaction_id' not in st.session_state:
            st.session_state.transaction_id = None
        if 'defillama_results' not in st.session_state:
            st.session_state.defillama_results = None
        if 'request_text' not in st.session_state:
            st.session_state.request_text = ""
        
        # Add text area for request description
        if 'request_text' in st.session_state and st.session_state.request_text:
            request_text_value = st.session_state.request_text
        elif 'request_textarea' in st.session_state and st.session_state.request_textarea:
            request_text_value = st.session_state.request_textarea
            # Also update request_text
            st.session_state.request_text = request_text_value
        else:
            request_text_value = ""
        
        st.text_area(
            "Request Description",
            value=request_text_value,
            height=120,
            key="request_textarea",
            on_change=self.update_text_callback
        )
        
        # Create columns for the buttons
        col1, col2 = st.columns([1, 1])
        
        # Place the evaluate button in the first column
        with col1:
            # Add button to evaluate request
            if st.button("Evaluate Request", key="evaluate_button"):
                # Ensure we have request text from either session state or the text area
                request_text_to_use = st.session_state.get('request_text', '') or st.session_state.get('request_textarea', '')
                
                # Update session state directly
                if not st.session_state.get('request_text') and st.session_state.get('request_textarea'):
                    st.session_state.request_text = st.session_state.get('request_textarea', '')
                
                if request_text_to_use and request_text_to_use.strip():
                    st.session_state.show_reasoning = True
                    # Trigger reasoning agent
                    self.render_reasoning_agent(request_text_to_use, services)
                    # Set reasoning complete to show service recommendations
                    st.session_state.reasoning_complete = True
                    # Rerun to update UI
                    st.rerun()
                else:
                    st.error("Please enter a request description in the text area above.")
        
        # Place the task history button in the second column
        with col2:
            # Add button to view task history
            if st.button("Task History", key="task_history_button"):
                # Navigate to dashboard page
                st.session_state.page = "dashboard"
                st.rerun()
        
        # Display infrastructure stats in a grid
        st.markdown("### Network Infrastructure")
        
        # Create 3 columns for stats
        cols = st.columns(3)
        
        # Format the infrastructure data
        infra_metrics = [
            {"label": "Active Mechs", "value": infrastructure_data.get("active_mechs", 25), "unit": ""},
            {"label": "Network Health", "value": infrastructure_data.get("network_health", 98), "unit": "%"},
            {"label": "Avg Response Time", "value": infrastructure_data.get("avg_response_time", 2.5), "unit": "s"}
        ]
        
        # Display each metric in its own column
        for i, metric in enumerate(infra_metrics):
            with cols[i]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background-color: white; 
                          border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="font-size: 2rem; font-weight: bold;">{metric['value']}{metric['unit']}</div>
                    <div style="font-size: 0.9rem; color: #555;">{metric['label']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Display reasoning steps if requested
        if hasattr(st.session_state, 'show_reasoning') and st.session_state.show_reasoning and 'reasoning_response' in st.session_state:
            self.display_reasoning_steps(st.session_state.reasoning_response)
        
        # Display service recommendations if reasoning is complete
        if st.session_state.reasoning_complete:
            self.display_service_recommendations(st.session_state.reasoning_response)
        
        # Don't use st.rerun() in the main render flow to avoid infinite loops
        # Instead, let Streamlit's natural flow control handle the UI updates
        
        # Mark form as submitted to prevent duplicate submissions
        if 'payment_confirmed' in st.session_state and st.session_state.payment_confirmed:
            # Reset form state for next use
            if st.session_state.page != 'execution':
                st.session_state.reasoning_complete = False
                st.session_state.reasoning_response = []
                st.session_state.payment_confirmed = False

    def update_text_callback(self):
        """Callback function for text area changes"""
        if "request_textarea" in st.session_state:
            try:
                self.update_request_text(st.session_state.request_textarea)
            except AttributeError:
                # Direct fallback if method is not found
                st.session_state.request_text = st.session_state.request_textarea 
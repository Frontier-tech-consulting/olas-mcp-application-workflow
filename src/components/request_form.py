import streamlit as st
import json
import os
import time
import random
import re
from dotenv import load_dotenv
from ..services.mcp_service import MCPService
from ..services.defillama_api import DefiLlamaAPI
from ..models.request import Request
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()

class RequestForm:
    """Component for creating and submitting requests"""
    
    def __init__(self, submit_callback, user_email):
        self.submit_callback = submit_callback
        self.user_email = user_email
        self.mcp_service = MCPService()
        self.defillama_api = DefiLlamaAPI()
        # Initialize OpenAI client with explicit token limits
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            max_tokens=1000,  # Limit output tokens
            api_key=os.getenv("OPENAI_API_KEY"),
            streaming=True
        )
    
    def generate_reasoning(self, query, services, infrastructure_data):
        """Generate reasoning steps using OpenAI and DeFi Llama data"""
        # Use the first service ID from available services if present
        service_id = None
        if services and isinstance(services, list) and len(services) > 0:
            first_service = services[0]
            if isinstance(first_service, dict) and 'service_id' in first_service:
                service_id = first_service['service_id']
        
        # Default to a fallback if no valid service ID found
        if not service_id:
            service_id = "default_service"
            
        # Get DeFi Llama data using service ID
        defillama_results = self.defillama_api.process_query(query, service_id)
        
        # Simplify the services data to reduce token count
        simplified_services = []
        for service in services:
            if isinstance(service, dict):
                simplified_service = {
                    "service_id": service.get("service_id", ""),
                    "description": service.get("description", ""),
                    "mech_address": service.get("mech_address", ""),
                }
                simplified_services.append(simplified_service)
        
        # Simplify the DeFi Llama data to reduce token count
        simplified_defillama = {}
        if "summary" in defillama_results:
            simplified_defillama["summary"] = defillama_results["summary"]
        if "processing_steps" in defillama_results:
            simplified_defillama["steps"] = [step["step"] for step in defillama_results["processing_steps"]]
        if "aggregated_data" in defillama_results:
            agg_data = defillama_results["aggregated_data"]
            simplified_agg = {}
            if "top_protocols" in agg_data:
                simplified_agg["top_protocols"] = [{"name": p.get("name"), "tvl": p.get("tvl")} 
                                                  for p in agg_data["top_protocols"][:3]]
            simplified_defillama["data"] = simplified_agg
        
        # Create a more compact prompt
        prompt_content = f"""
        You are an AI assistant helping select OLAS mech services based on user queries. Analyze the request and available services.
        
        Break down reasoning into FOUR steps:
        Step 1: Task Identification - Understand the user's request and objectives
        Step 2: Required Capabilities - Identify technical needs and data sources
        Step 3: Service Matching - Match needs to available services
        Step 4: Selected Services - Final recommendations with benefits
        
        USER QUERY: {query}
        
        AVAILABLE SERVICES: {json.dumps(simplified_services)}
        
        RELEVANT DATA: {json.dumps(simplified_defillama)}
        
        Format with clear step headings (e.g., "Step 1: Task Identification") and build a coherent reasoning chain.
        """
        
        return prompt_content, defillama_results
    
    def render(self):
        """Render the request form"""
        # Add CSS styling for smooth transitions and step containers
        st.markdown("""
        <style>
        /* Smooth transitions */
        * {
            transition: all 0.3s ease;
        }
        
        /* Scrollable output container */
        .reasoning-step-content {
            max-height: 250px;
            overflow-y: auto;
            padding: 12px;
            background-color: #f9f9f9;
            border-radius: 4px;
            border: 1px solid #f0f0f0;
        }
        
        /* Recommended service styling */
        .recommended-service {
            border-left: 4px solid #6200ee !important;
            background-color: #f9f5ff !important;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .service-price {
            font-weight: bold;
            color: #6200ee;
            font-size: 1.1rem;
        }
        
        .service-mech-address {
            font-family: monospace;
            background-color: #f5f5f5;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            color: #444;
            margin-top: 8px;
        }
        
        /* Styling for reasoning steps */
        .reasoning-container {
            margin: 20px 0;
            padding: 10px;
            border-radius: 10px;
            background-color: #fbfbfb;
        }
        
        .reasoning-step-container {
            position: relative;
            padding-left: 30px;
            margin-bottom: 25px;
            border-left: 2px solid #e0e0e0;
        }
        
        .reasoning-step-circle {
            position: absolute;
            left: -10px;
            top: 0;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background-color: #6200ee;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        
        .reasoning-step-header {
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 10px;
            color: #333;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="header-container">
            <h2>Create Request</h2>
            <p>Submit your request for analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize session state variables if they don't exist
        if 'reasoning_complete' not in st.session_state:
            st.session_state.reasoning_complete = False
        if 'reasoning_response' not in st.session_state:
            st.session_state.reasoning_response = ""
        if 'selected_services' not in st.session_state:
            st.session_state.selected_services = []
        if 'checkboxes' not in st.session_state:
            st.session_state.checkboxes = {}
        if 'show_payment' not in st.session_state:
            st.session_state.show_payment = False
        if 'payment_complete' not in st.session_state:
            st.session_state.payment_complete = False
        if 'defillama_results' not in st.session_state:
            st.session_state.defillama_results = None
        
        # Input for request description
        request_description = st.text_area("Request Description", placeholder="Describe your request here...")
        
        # Create evaluate button
        evaluate_clicked = st.button("Evaluate Request")
        
        # Load services data
        services = self.mcp_service.services
        infrastructure_data = self.mcp_service.infrastructure_stats
        
        # Fix for potential data structure issues
        if isinstance(services, dict) and "services" in services:
            services = services["services"]
        elif not isinstance(services, list):
            print(f"Warning: Services data has unexpected format: {type(services)}")
            services = []
        
        if evaluate_clicked and request_description:
            # Reset session state for a new evaluation
            st.session_state.reasoning_complete = False
            st.session_state.reasoning_response = ""
            st.session_state.selected_services = []
            st.session_state.checkboxes = {}
            st.session_state.show_payment = False
            st.session_state.payment_complete = False
            st.session_state.defillama_results = None
            
            # Generate reasoning with DeFi Llama data
            st.markdown("### Reasoning Simulation")
            
            # Create a single placeholder for the reasoning output
            reasoning_placeholder = st.empty()
            
            # Set up progress indication
            progress_bar = st.progress(0)
            
            # Set up streaming callback
            with st.spinner("Generating reasoning..."):
                prompt_content, defillama_results = self.generate_reasoning(request_description, services, infrastructure_data)
                
                # Store DeFi Llama results in session state
                st.session_state.defillama_results = defillama_results
                
                # Initialize steps content
                steps_content = {
                    "Step 1: Task Identification": "",
                    "Step 2: Required Capabilities": "",
                    "Step 3: Service Matching": "",
                    "Step 4: Selected Services": ""
                }
                
                # Streaming implementation
                current_step = None
                full_response = ""
                step_keys = list(steps_content.keys())
                
                # Use a more efficient batch update approach
                buffer = ""
                update_frequency = 20  # Update UI every 20 chunks
                
                for i, chunk in enumerate(self.llm.stream(prompt_content)):
                    content = chunk.content
                    buffer += content
                    full_response += content
                    
                    # Only process content periodically to reduce UI updates
                    if i % update_frequency == 0 or "Step" in buffer:
                        # Process the content to identify and update steps
                        for step_idx, step_name in enumerate(step_keys):
                            if step_name in full_response and (current_step is None or current_step != step_name):
                                current_step = step_name
                                # Update progress bar
                                progress_bar.progress((step_idx + 1) / len(step_keys) * 0.8)
                        
                        if current_step:
                            # Extract content for current step
                            parts = full_response.split(current_step)
                            if len(parts) > 1:
                                step_text = parts[1]
                                # If there's a next step, only take content up to that point
                                next_steps = step_keys
                                current_index = next_steps.index(current_step)
                                
                                if current_index < len(next_steps) - 1:
                                    next_step = next_steps[current_index + 1]
                                    if next_step in step_text:
                                        step_text = step_text.split(next_step)[0]
                                
                                steps_content[current_step] = step_text.strip()
                        
                        # Construct the combined content for all steps
                        combined_html = ""
                        for step_idx, (step_name, content) in enumerate(steps_content.items()):
                            if content:
                                # Extract the step number for the circle
                                step_num = step_name.split(':')[0].replace('Step ', '')
                                
                                # Create the styled step container
                                step_content_html = content.replace('\n', '<br>')
                                combined_html += f"""
                                <div class="reasoning-step-container">
                                    <div class="reasoning-step-circle">{step_num}</div>
                                    <div class="reasoning-step-header">{step_name.split(': ')[1]}</div>
                                    <div class="reasoning-step-content">{step_content_html}</div>
                                </div>
                                """
                        
                        # Update the single placeholder with all steps
                        if combined_html:
                            reasoning_placeholder.markdown(f"""
                            <div class="reasoning-container">
                                {combined_html}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Reset buffer after processing
                        buffer = ""
                    
                    time.sleep(0.01)  # Small delay
                
                # Process any remaining content in buffer
                if buffer:
                    # Final update with remaining content
                    for step_idx, step_name in enumerate(step_keys):
                        if step_name in full_response and (current_step is None or current_step != step_name):
                            current_step = step_name
                    
                    if current_step:
                        # Extract content for current step
                        parts = full_response.split(current_step)
                        if len(parts) > 1:
                            step_text = parts[1]
                            steps_content[current_step] = step_text.strip()
                    
                    # Update UI one final time
                    combined_html = ""
                    for step_idx, (step_name, content) in enumerate(steps_content.items()):
                        if content:
                            step_num = step_name.split(':')[0].replace('Step ', '')
                            step_content_html = content.replace('\n', '<br>')
                            combined_html += f"""
                            <div class="reasoning-step-container">
                                <div class="reasoning-step-circle">{step_num}</div>
                                <div class="reasoning-step-header">{step_name.split(': ')[1]}</div>
                                <div class="reasoning-step-content">{step_content_html}</div>
                            </div>
                            """
                    
                    if combined_html:
                        reasoning_placeholder.markdown(f"""
                        <div class="reasoning-container">
                            {combined_html}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Complete the progress bar
                progress_bar.progress(1.0)
                
                # Extract steps as separate entries for storage
                parsed_steps = []
                for step_name, content in steps_content.items():
                    if content:
                        parsed_steps.append(f"{step_name}:\n{content}")
                
                # Store parsed steps or full response if parsing failed
                if parsed_steps:
                    st.session_state.reasoning_response = parsed_steps
                else:
                    st.session_state.reasoning_response = full_response
                
                st.session_state.reasoning_complete = True
                st.session_state.query = request_description  # Store the query for later
                
                # Extract recommended service IDs from the reasoning
                recommended_services = []
                services_justification = ""
                
                # Find recommended services from the justification
                for step in parsed_steps:
                    if "Selected Services" in step:
                        services_justification = step
                        # Extract service IDs using regex pattern matching
                        service_matches = re.findall(r'Service\s+(\d+)', step)
                        if service_matches:
                            recommended_services = list(set(service_matches))  # Remove duplicates
                        break
                
                # Store recommended services in session state for later use
                st.session_state.recommended_services = recommended_services
        
        # Display service selection after reasoning is complete
        if st.session_state.reasoning_complete:
            st.markdown("### Recommended Services")
            
            # Track selected services
            selected_services = []
            
            # Identify the recommended services
            recommended_service_objects = []
            
            for service in services:
                service_id = service.get('service_id', '')
                if hasattr(st.session_state, 'recommended_services') and service_id in st.session_state.recommended_services:
                    recommended_service_objects.append(service)
            
            # If no recommended services, use a default set
            if not recommended_service_objects and services:
                # Get first service as a fallback
                recommended_service_objects = [services[0]]
            
            # Display recommended services
            for idx, service in enumerate(recommended_service_objects):
                # Extract service information with safe access
                service_id = service.get('service_id', f"Service-{idx}")
                service_desc = service.get('description', f"Service {idx}")
                if isinstance(service_desc, str):
                    service_name = service_desc.split(' - ')[0]
                else:
                    service_name = f"Service {idx}"
                
                # Get additional service details
                mech_address = service.get('mech_address', 'Unknown')
                owner_address = service.get('owner_address', 'Unknown')
                threshold = service.get('threshold', '1')
                version = service.get('version', '0.1.0')
                
                # Create a unique key for this checkbox
                checkbox_key = f"service_{service_id}_{idx}"
                
                # Initialize checkbox state to checked by default
                if checkbox_key not in st.session_state.checkboxes:
                    st.session_state.checkboxes[checkbox_key] = True
                
                # Display checkbox for service selection
                is_checked = st.checkbox(
                    f"Select {service_name} (Service ID: {service_id})",
                    value=st.session_state.checkboxes[checkbox_key],
                    key=checkbox_key,
                    help=f"Select this service for execution"
                )
                
                # Display service details
                st.markdown(f"""
                <div class="recommended-service">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #2e2e2e;">Service {service_id}: {service_name}</h4>
                            <p style="margin: 5px 0; color: #555;">{service_desc}</p>
                        </div>
                        <div class="service-price">1 OLAS</div>
                    </div>
                    <div style="margin-top: 10px;">
                        <div><strong>Mech Address:</strong> <span class="service-mech-address">{mech_address}</span></div>
                        <div><strong>Owner Address:</strong> <span class="service-mech-address">{owner_address}</span></div>
                        <div><strong>Version:</strong> {version} | <strong>Threshold:</strong> {threshold}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Update our tracking of selected services
                st.session_state.checkboxes[checkbox_key] = is_checked
                
                if is_checked:
                    # Add service to selected services
                    service_copy = service.copy() if service else {}
                    # Set price to 1 OLAS
                    service_copy['price'] = "1 OLAS"
                    selected_services.append(service_copy)
            
            # Update session state with selected services
            st.session_state.selected_services = selected_services
            
            # Display total cost
            total_cost = len(st.session_state.selected_services)  # 1 OLAS per service
            st.markdown(f"""
            <div style="margin-top: 20px; padding: 15px; background-color: #f9f5ff; border-radius: 10px; text-align: center;">
                <h4 style="margin: 0; color: #6200ee;">Total Cost: {total_cost} OLAS</h4>
                <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #666;">For {len(st.session_state.selected_services)} selected services</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Submit button for final submission
            if not st.session_state.show_payment:
                submit_col1, submit_col2 = st.columns([3, 1])
                with submit_col1:
                    st.markdown("")  # spacer
                with submit_col2:
                    if st.button("Submit Request", key="submit_request_button", type="primary"):
                        if st.session_state.selected_services:
                            st.session_state.show_payment = True
                            st.rerun()
                        else:
                            st.error("Please select at least one service.")
        
        # Payment confirmation
        if st.session_state.show_payment:
            # Apply styling for payment view
            st.markdown("""
            <style>
            /* Hide the request description and evaluate button during payment */
            div[data-testid="stTextArea"] {
                display: none !important;
            }
            button[data-testid="baseButton-secondary"] {
                margin-right: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Show a clear summary header
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h2>Payment Confirmation</h2>
                <p>Please review your selected services before confirming payment</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Calculate service costs (1 OLAS per service)
            total_cost = len(st.session_state.selected_services)
            
            # Create a summary of selected services using Streamlit components
            st.markdown("### Order Summary")
            
            # Display selected services in a table
            service_data = []
            for idx, service in enumerate(st.session_state.selected_services):
                service_id = service.get('service_id', f"Unknown-{idx}")
                service_desc = service.get('description', f"Service {idx}")
                if isinstance(service_desc, str):
                    service_name = service_desc.split(' - ')[0]
                else:
                    service_name = f"Service {idx}"
                    
                mech_address = service.get('mech_address', 'Unknown')
                
                service_data.append({
                    "Service ID": service_id,
                    "Name": service_name,
                    "Mech Address": mech_address,
                    "Price": "1 OLAS"
                })
            
            # Display services in a table
            st.table(service_data)
            
            # Display cost breakdown
            st.markdown("### Cost Breakdown")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Subtotal:", f"{total_cost} OLAS")
                st.write("Network Fee:", "0.001 OLAS")
            with col2:
                st.write("Total:", f"{round(total_cost + 0.001, 3)} OLAS")
            
            # Payment buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel", key="cancel_payment", type="secondary"):
                    st.session_state.show_payment = False
                    st.rerun()
            with col2:
                payment_confirmed = st.button("Confirm Payment", key="confirm_payment", type="primary")
                
                if payment_confirmed:
                    # Show payment processing animation
                    with st.spinner("Processing Payment..."):
                        # Simulate a short delay for payment processing
                        time.sleep(1.5)
                        
                        # Create proper execution steps list
                        execution_steps = []
                        if st.session_state.reasoning_response:
                            execution_steps = [st.session_state.reasoning_response]
                        
                        # Create the request object with all required data
                        request = Request(
                            prompt=request_description,
                            selected_services=st.session_state.selected_services,
                            total_cost=total_cost,  # 1 OLAS per service
                            reasoning_steps=execution_steps
                        )
                        
                        # Add DeFi Llama results to the request if available
                        if hasattr(st.session_state, 'defillama_results') and st.session_state.defillama_results:
                            request.defillama_results = st.session_state.defillama_results
                        
                        # Show success message
                        st.success("Payment Successful! Your request has been submitted.")
                        
                        # Add a small delay for UX
                        time.sleep(1)
                        
                        # Submit the request and transition to execution status
                        self.submit_callback(request) 
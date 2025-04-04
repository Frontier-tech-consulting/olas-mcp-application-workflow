import streamlit as st
import time
import re
import json
import random
from typing import Dict, List, Any, Optional
from ..models.request import Request
from ..services.mcp_service import MCPService
from ..services.defillama_api import DefiLlamaAPI

class ExecutionStatus:
    """Component for displaying execution status"""
    
    def __init__(self, request: Request):
        """Initialize with a Request object"""
        self.request = request
        self.mcp_service = MCPService()
        self.defillama_api = DefiLlamaAPI()
    
    def ensure_transaction(self):
        """Ensure the request has a transaction ID"""
        if not self.request or not self.request.transaction_id:
            # Submit the request to get a transaction ID
            try:
                result = self.mcp_service.submit_request(self.request)
                if result and isinstance(result, str):
                    self.request.transaction_id = result
                    # Store in session state
                    st.session_state.transaction_id = result
                else:
                    st.error("Failed to create transaction ID")
            except Exception as e:
                st.error(f"Failed to create transaction: {str(e)}")
    
    def render(self):
        """Render the execution status component"""
        try:
            if not self.request:
                st.error("No active request found")
                if st.button("Create New Request", key="new_request_from_exec"):
                    st.session_state.page = 'create_request'
                    st.rerun()
                return

            # Ensure we have a transaction ID
            self.ensure_transaction()
            if not self.request.transaction_id:
                st.error("No transaction ID found for request")
                if st.button("Return to Create Request", key="no_tx_return_create"):
                    st.session_state.page = 'create_request'
                    st.rerun()
                return

            # Get current execution status with error handling
            status = None
            try:
                status = self.mcp_service.get_execution_status(self.request.transaction_id)
            except Exception as e:
                st.error(f"Error retrieving status: {str(e)}")
                status = {"status": "error", "message": str(e)}
            
            # Check if status is None or not a dictionary and handle accordingly
            if status is None:
                st.error("Could not retrieve execution status. Status returned None.")
                if st.button("Return to Dashboard", key="error_return_dash"):
                    st.session_state.page = 'dashboard'
                    st.rerun()
                if st.button("Try Again", key="retry_status"):
                    st.rerun()
                return
            
            # Ensure status is a dictionary
            if not isinstance(status, dict):
                st.error(f"Invalid status format: {type(status)}")
                status = {"status": "error", "message": "Invalid status format"}
                
            # Store execution status in session state for app.py to use
            if status.get("status") == "completed":
                st.session_state.execution_complete = True
                if 'execution_error' in st.session_state:
                    st.session_state.pop('execution_error')
            elif status.get("status") == "error":
                st.session_state.execution_error = True
                if 'execution_complete' in st.session_state:
                    st.session_state.pop('execution_complete')
            
            # Display execution header
            st.markdown("""
            <div style='margin-bottom: 2rem;'>
                <h2>Request Execution Status</h2>
                <p>Monitoring the execution of your request across selected services</p>
            </div>
            """, unsafe_allow_html=True)

            # Create columns for request details and overall progress
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Request Details")
                st.markdown(f"**Prompt:** {self.request.prompt}")
                st.markdown(f"**Transaction ID:** {self.request.transaction_id}")
                st.markdown(f"**Services Selected:** {len(self.request.selected_services or [])}")
                
            with col2:
                st.markdown("### Overall Progress")
                # Calculate overall progress with safe access
                if status.get("status") == "completed":
                    progress = 100
                elif status.get("status") == "running":
                    service_results = status.get("service_results", []) or []
                    progress = sum(s.get("progress", 0) for s in service_results) / max(len(service_results), 1)
                else:
                    progress = 0
                st.progress(progress / 100)
                st.markdown(f"**Status:** {status.get('status', 'Unknown').title()}")

            # Display processing pipeline
            st.markdown("### Processing Pipeline")
            steps = status.get("steps", []) or []
            total_steps = 6  # Total expected steps
            current_step = len(steps)
            
            # Create a timeline visualization
            st.markdown("""
            <div class="timeline-container" style="margin: 2rem 0;">
            """, unsafe_allow_html=True)
            
            for i, step in enumerate(steps):
                icon = "✓" if i < current_step else "○"
                color = "#4CAF50" if i < current_step else "#9E9E9E"
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <div style="color: {color}; font-weight: bold; margin-right: 1rem;">{icon}</div>
                    <div style="flex-grow: 1;">
                        <div style="color: {color};">{step}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Display service execution cards
            st.markdown("### Service Execution")
            
            service_results = status.get("service_results", []) or []
            if not service_results:
                st.info("No service execution data available yet.")
            
            for service_result in service_results:
                # Safe access with default values
                service_id = service_result.get('service_id', 'Unknown')
                service_name = service_result.get('name', 'Service')
                
                with st.expander(f"Service {service_id} - {service_name}", expanded=True):
                    # Service progress with safe access
                    st.progress(service_result.get("progress", 0) / 100)
                    
                    # Service status and timing
                    cols = st.columns(3)
                    with cols[0]:
                        st.markdown(f"**Status:** {service_result.get('status', 'Unknown').title()}")
                    with cols[1]:
                        start_time = service_result.get("start_time")
                        if start_time:
                            st.markdown(f"**Started:** {time.strftime('%H:%M:%S', time.localtime(start_time))}")
                    with cols[2]:
                        if service_result.get("status") == "completed":
                            st.markdown("**Completed** ✓")
                    
                    # Display execution steps with safe access
                    execution_steps = service_result.get("execution_steps", []) or []
                    if execution_steps:
                        st.markdown("#### Execution Steps:")
                        for i, step in enumerate(execution_steps):
                            is_current = i == len(execution_steps) - 1 and service_result.get("status") == "running"
                            if is_current:
                                st.markdown(f"▶ **{step}** _(Current)_")
                            else:
                                st.markdown(f"✓ {step}")
                    
                    # Display service result if available with safe access
                    result = service_result.get("result")
                    if result:
                        st.markdown("#### Results:")
                        if isinstance(result, dict):
                            if "confidence" in result:
                                st.markdown(f"**Confidence:** {result.get('confidence', 0):.2%}")
                            if "output" in result:
                                st.markdown("**Output:**")
                                st.markdown(result.get("output", ""))
                            if "processing_time" in result:
                                st.markdown(f"**Processing Time:** {result.get('processing_time', 0):.2f}s")
                        else:
                            # Handle non-dict results
                            st.markdown(f"**Result:** {result}")

            # Display final results if completed
            result = status.get("result")
            if status.get("status") == "completed" and result:
                st.markdown("### Final Results")
                try:
                    # Store result in session state
                    st.session_state.execution_result = result
                    
                    if isinstance(result, dict):
                        if "summary" in result:
                            st.markdown("#### Summary")
                            st.markdown(result.get("summary", ""))
                        if "details" in result and result.get("details"):
                            st.markdown("#### Details")
                            for detail in result.get("details", []):
                                st.markdown(f"- {detail}")
                        if "recommendations" in result and result.get("recommendations"):
                            st.markdown("#### Recommendations")
                            for rec in result.get("recommendations", []):
                                st.markdown(f"- {rec}")
                    else:
                        st.markdown(str(result))
                except Exception as e:
                    st.error(f"Error displaying results: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

            # Auto-refresh while execution is running
            if status.get("status") == "running":
                time.sleep(1)  # Small delay to prevent too frequent refreshes
                st.rerun()

            # Button layout
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Refresh Status", key="refresh_status"):
                    st.rerun()

            # Back button
            with col2:
                if st.button("Back to Dashboard", key="back_to_dashboard"):
                    st.session_state.page = 'dashboard'
                    st.rerun()

        except Exception as e:
            st.error(f"Error displaying execution status: {str(e)}")
            import traceback
            error_msg = traceback.format_exc()
            st.error(error_msg)
            
            # Debug information
            st.markdown("### Debug Information")
            st.markdown("This information might help diagnose the issue:")
            
            # Show available session state keys
            st.markdown("**Session State Keys:**")
            session_keys = ", ".join(list(st.session_state.keys()))
            st.code(session_keys)
            
            # Show request info if available
            if self.request:
                st.markdown("**Request Info:**")
                request_info = {
                    "prompt": self.request.prompt,
                    "transaction_id": self.request.transaction_id,
                    "has_selected_services": bool(self.request.selected_services)
                }
                st.json(request_info)
            
            # Navigation options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Return to Home", key="exception_return_home"):
                    st.session_state.page = 'home'
                    st.rerun()
            with col2:
                if st.button("Try Again", key="exception_try_again"):
                    st.rerun()

        # Add custom CSS for styling
        st.markdown("""
        <style>
        /* Timeline styling */
        .timeline-container {
            border-left: 2px solid #000000;
            padding-left: 20px;
            margin-left: 10px;
        }
        
        /* Service card styling */
        .stExpander {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        /* Progress bar styling */
        .stProgress > div > div {
            background-color: #000000;
        }
        
        /* Button styling */
        .stButton button {
            background-color: #000000 !important; 
            color: #ffffff !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            border-radius: 4px !important;
            transition: all 0.3s;
            font-weight: 600 !important;
        }
        .stButton button:hover {
            background-color: #333333 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Button text styling */
        .stButton button p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Comprehensive button text targeting */
        button p, button span, button div {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Fix for Streamlit button text */
        button[kind="primaryFormSubmit"] p,
        button[kind="secondaryFormSubmit"] p,
        button[data-baseweb="button"] p,
        [data-testid="baseButton-secondary"] p,
        [data-testid="baseButton-primary"] p,
        button[data-testid*="StyledButton"] span {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)
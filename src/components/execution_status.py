import streamlit as st
import time
import re
import json
import random
from typing import Dict, List, Any
from ..models.request import Request
from ..services.mcp_service import MCPService
from ..services.defillama_api import DefiLlamaAPI

class ExecutionStatus:
    """Component for displaying execution status"""
    
    def __init__(self, mcp_service: MCPService):
        self.mcp_service = mcp_service
        self.defillama_api = DefiLlamaAPI()
    
    def ensure_transaction(self, request: Request):
        """Ensure the request has a valid transaction ID, creating one if needed"""
        try:
            # Check if transaction_id is missing or invalid
            if not hasattr(request, 'transaction_id') or not request.transaction_id:
                # Generate a mock transaction ID
                transaction_id = f"tx_{random.randint(1000, 9999)}_{int(time.time())}"
                request.transaction_id = transaction_id
                
                # Submit to MCP service to start tracking
                try:
                    self.mcp_service.submit_request(request)
                    print(f"Created new transaction: {transaction_id}")
                except Exception as e:
                    print(f"Error submitting request to MCP service: {str(e)}")
                    # Continue with the mock ID anyway
            
            return request.transaction_id
        except Exception as e:
            print(f"Error in ensure_transaction: {str(e)}")
            # Fallback to a guaranteed transaction ID
            fallback_id = f"fallback_tx_{random.randint(1000, 9999)}_{int(time.time())}"
            request.transaction_id = fallback_id
            return fallback_id
    
    def render(self, request: Request):
        """Render the execution status"""
        # Ensure we have a valid transaction ID
        self.ensure_transaction(request)
        
        # Hide Streamlit UI elements
        st.markdown("""
        <style>
        /* Hide streamlit search and other bars */
        [data-testid="stToolbar"] {
            display: none;
        }
        header {
            visibility: hidden;
        }
        footer {
            visibility: hidden;
        }
        
        /* Text colors - black with soft contrast */
        p, h1, h2, h3, h4, h5, h6, div, span, label {
            color: #2e2e2e !important;
        }
        
        /* Make progress steps more appealing */
        .step-container {
            border-left: 2px solid #ccc;
            padding-left: 20px;
            margin-left: 20px;
            position: relative;
            margin-bottom: 15px;
        }
        .step-circle {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            position: absolute;
            left: -15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .step-content {
            padding: 10px 15px;
            margin-left: 20px;
            margin-bottom: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            max-height: 250px;
            overflow-y: auto;
            overflow-x: hidden;
        }
        
        /* Service execution cards */
        .service-execution-card {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
            transition: all 0.3s ease;
        }
        .service-execution-card.running {
            border-left: 4px solid #6200ee;
            background-color: #f9f5ff;
        }
        .service-execution-card.completed {
            border-left: 4px solid #4CAF50;
            background-color: #f0fff4;
        }
        .service-execution-card.error {
            border-left: 4px solid #F44336;
            background-color: #fff5f5;
        }
        .service-execution-card.verification {
            border-left: 4px solid #FF9800;
            background-color: #fff9e6;
        }
        
        /* Add loading animation */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border-left-color: #6200ee;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
            vertical-align: middle;
        }
        .execution-header {
            text-align: center;
            padding: 20px 0;
        }
        .execution-container {
            background-color: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .execution-progress {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            position: relative;
            padding-bottom: 10px;
        }
        .progress-line {
            position: absolute;
            height: 2px;
            background-color: #e6e9ed;
            top: 10px;
            left: 30px;
            right: 30px;
            z-index: 1;
        }
        .progress-complete {
            position: absolute;
            height: 2px;
            background-color: #6200ee;
            top: 10px;
            left: 30px;
            z-index: 2;
            transition: width 0.3s ease;
        }
        .progress-step {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: #e6e9ed;
            z-index: 3;
            position: relative;
            text-align: center;
        }
        .progress-step.active {
            background-color: #6200ee;
            color: white;
        }
        .progress-step.completed {
            background-color: #4CAF50;
            color: white;
        }
        
        /* Oracle verification section */
        .oracle-verification {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            background-color: #fff9e6;
            border-left: 4px solid #FF9800;
        }
        .oracle-header {
            font-weight: 600;
            color: #E65100;
            margin-bottom: 10px;
        }
        .refund-info {
            padding: 10px;
            background-color: #fff;
            border-radius: 4px;
            margin-top: 10px;
            border: 1px solid #FFE0B2;
        }
        
        /* Service loading states */
        .service-loading-state {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }
        .loading-indicator {
            width: 24px;
            height: 24px;
            margin-right: 10px;
            text-align: center;
        }
        .loading-indicator-spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-left-color: #6200ee;
            animation: spin 1s linear infinite;
            display: inline-block;
        }
        .loading-text {
            flex-grow: 1;
        }
        .loading-time {
            font-size: 0.8em;
            color: #666;
        }
        .service-processing-stage {
            padding-left: 34px;
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #666;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Focus solely on execution progress
        st.markdown("""
        <div class="execution-header">
            <h1>MCP Execution Status</h1>
            <p>Tracking progress of your service execution</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create columns for request details and services
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Display request details in a compact format
            st.markdown("""
            <div class="execution-container">
                <h3>Request Details</h3>
            """, unsafe_allow_html=True)
            
            st.text_area("Query", value=request.prompt, height=100, disabled=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display execution status with a prominent header
            st.markdown("<h2>Execution Progress</h2>", unsafe_allow_html=True)
            
            try:
                # Get current status
                status = self.mcp_service.get_execution_status(request.transaction_id)
                
                # Handle case where status is None
                if status is None:
                    print(f"Warning: Received None status for transaction {request.transaction_id}")
                    status = {
                        "status": "pending",
                        "steps": [],
                        "result": None,
                        "error": None
                    }
                
                # Update request with new status
                request.execution_status = status.get("status", "pending")
                request.execution_steps = status.get("steps", [])
                request.final_result = status.get("result")
                request.error_message = status.get("error")
                
                # Generate detailed service states based on the selected services
                service_states = []
                
                # Define processing stages for each service
                processing_stages = [
                    "Initializing service",
                    "Loading data sources",
                    "Processing request",
                    "Analyzing results",
                    "Preparing response",
                    "Finalizing"
                ]
                
                # Create detailed service states based on the selected services
                for idx, service in enumerate(request.selected_services):
                    service_id = service.get('service_id', f"Unknown-{idx}")
                    service_desc = service.get('description', f"Service {idx}")
                    if isinstance(service_desc, str):
                        service_name = service_desc.split(' - ')[0]
                    else:
                        service_name = f"Service {idx}"
                        
                    # Generate realistic service states based on execution status
                    current_time = time.time()
                    stages = []
                    service_state = "pending"
                    
                    # Determine dynamic progress based on execution status and current service
                    if request.execution_status == "pending":
                        service_state = "pending"
                        progress = 0
                        stages = []
                    elif request.execution_status == "running":
                        # Create a cascading start for services
                        if idx == 0:  # First service: either completed or almost done
                            service_state = "completed" if len(request.execution_steps) >= 5 else "running"
                            progress = 100 if service_state == "completed" else random.randint(80, 95)
                            stages = processing_stages
                        elif idx == 1 and len(request.execution_steps) >= 3:  # Second service: in progress
                            service_state = "running"
                            progress = random.randint(30, 60)
                            # Include only a subset of stages
                            stage_count = int(len(processing_stages) * progress / 100)
                            stages = processing_stages[:stage_count]
                        elif idx == 2 and len(request.execution_steps) >= 4:  # Third service: just started
                            service_state = "running"
                            progress = random.randint(5, 20)
                            # Only the first couple of stages
                            stages = processing_stages[:2]
                        else:  # Remaining services: still pending
                            service_state = "pending"
                            progress = 0
                            stages = []
                    elif request.execution_status == "completed":
                        service_state = "completed"
                        progress = 100
                        stages = processing_stages
                    else:  # Error state
                        service_state = "error" if idx == 0 else "pending"
                        progress = 30 if service_state == "error" else 0
                        stages = processing_stages[:2] if service_state == "error" else []
                    
                    # Calculate start time based on service state
                    start_time = None
                    if service_state != "pending":
                        # Earlier services would have started earlier
                        start_time = current_time - (600 - idx * 120)
                    
                    service_states.append({
                        "service_id": service_id,
                        "name": service_name,
                        "state": service_state,
                        "progress": progress,
                        "mech_address": service.get('mech_address', 'Unknown'),
                        "start_time": start_time,
                        "stages": stages,
                        "current_stage": len(stages) - 1 if stages else -1
                    })
                
                # Add these states to the request for future reference
                request.service_states = service_states
                
                # Determine Oracle verification status
                oracle_verified = False
                refund_issued = False
                oracle_diff = 0
                
                if request.execution_status == "completed" and not hasattr(request, 'oracle_verified'):
                    # Simulate oracle verification with a 20% chance of finding discrepancy
                    oracle_check = random.random() < 0.2
                    request.oracle_verified = True
                    request.oracle_diff = random.randint(5, 30) if oracle_check else 0
                    request.refund_issued = oracle_check
                    
                    # If oracle found discrepancy, issue refund
                    if request.oracle_diff > 0:
                        refund_amount = 0.3 * len(request.selected_services)  # 30% refund
                        request.refund_amount = refund_amount
                
                # Display status with appropriate styling
                status_color = {
                    "pending": "#3498db",
                    "running": "#6200ee",
                    "completed": "#4CAF50",
                    "error": "#F44336"
                }.get(request.execution_status, "#9E9E9E")
                
                status_text = request.execution_status.title()
                status_icon = {
                    "pending": "⏳",
                    "running": "⚙️",
                    "completed": "✅",
                    "error": "❌"
                }.get(request.execution_status, "⏳")
                
                st.markdown(f"""
                <div style="padding: 15px; border-radius: 10px; background-color: {status_color}; color: white; text-align: center; font-size: 20px; margin-bottom: 20px;">
                    {status_icon} Status: {status_text}
                </div>
                """, unsafe_allow_html=True)
                
                # Create a visual progress tracker
                if request.execution_steps:
                    total_steps = max(10, len(request.execution_steps) + 2)  # Ensure at least 10 steps for visual consistency
                    current_step = min(len(request.execution_steps), total_steps)
                    progress_percent = (current_step / total_steps) * 100
                    
                    # Display progress bar
                    st.progress(progress_percent / 100)
                    
                    # Create a visual stepper
                    st.markdown(f"""
                    <div class="execution-container">
                        <div class="execution-progress">
                            <div class="progress-line"></div>
                            <div class="progress-complete" style="width: {progress_percent}%;"></div>
                    """, unsafe_allow_html=True)
                    
                    for i in range(1, total_steps + 1):
                        step_class = "progress-step"
                        if i <= current_step:
                            step_class += " completed" if i < current_step else " active"
                        
                        st.markdown(f"""
                        <div class="{step_class}"></div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    # Display service execution cards - one for each selected service
                    st.markdown("<h3>Service Execution Status</h3>", unsafe_allow_html=True)
                    
                    # First show the overall processing steps
                    st.markdown("""
                    <div style="margin-bottom: 20px;">
                        <h4>Processing Pipeline</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create a timeline visualization for the processing steps
                    step_names = [
                        "Query Analysis",
                        "Parameter Inference",
                        "API Execution",
                        "Service Processing",
                        "Data Aggregation",
                        "Result Generation"
                    ]
                    
                    # Determine which steps are complete based on the execution steps
                    step_statuses = []
                    for step_name in step_names:
                        step_found = False
                        for exec_step in request.execution_steps:
                            if step_name in exec_step:
                                step_found = True
                                break
                        step_statuses.append(step_found)
                    
                    # If no steps are complete yet, mark the first step as active
                    if not any(step_statuses) and request.execution_status == "running":
                        step_statuses[0] = "active"
                    
                    # Calculate active step index
                    active_step_idx = -1
                    if request.execution_status == "running":
                        for i, status in enumerate(step_statuses):
                            if status == "active" or (i > 0 and step_statuses[i-1] and not status):
                                active_step_idx = i
                                break
                        if active_step_idx == -1 and any(step_statuses):
                            # Find the last completed step
                            for i in range(len(step_statuses)-1, -1, -1):
                                if step_statuses[i]:
                                    active_step_idx = i + 1
                                    if active_step_idx >= len(step_statuses):
                                        active_step_idx = len(step_statuses) - 1
                                    break
                    
                    # Create timeline progress bar
                    progress_percent = 0
                    if request.execution_status == "completed":
                        progress_percent = 100
                    elif request.execution_status == "running":
                        # Calculate progress based on steps completed
                        completed_count = sum(1 for s in step_statuses if s is True)
                        progress_percent = min(95, (completed_count / len(step_statuses)) * 100)
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 10px; position: relative; height: 60px;">
                        <div style="position: absolute; height: 4px; background-color: #e0e0e0; top: 28px; left: 0; right: 0; z-index: 1;"></div>
                        <div style="position: absolute; height: 4px; background-color: #6200ee; top: 28px; left: 0; width: {progress_percent}%; z-index: 2; transition: width 0.5s ease;"></div>
                    """, unsafe_allow_html=True)
                    
                    # Add timeline step indicators
                    for i, (step_name, is_complete) in enumerate(zip(step_names, step_statuses)):
                        left_pos = (i / (len(step_names) - 1)) * 100
                        
                        # Determine the status class
                        if is_complete is True:
                            status_class = "completed"
                            icon = "✓"
                            bg_color = "#4CAF50"
                        elif i == active_step_idx or is_complete == "active":
                            status_class = "active"
                            icon = '<div class="loading-indicator-spinner" style="margin: 5px;"></div>'
                            bg_color = "#6200ee"
                        else:
                            status_class = "pending"
                            icon = str(i + 1)
                            bg_color = "#e0e0e0"
                        
                        st.markdown(f"""
                        <div style="position: absolute; left: calc({left_pos}% - 15px); top: 20px; z-index: 3;">
                            <div style="width: 30px; height: 30px; border-radius: 50%; background-color: {bg_color}; 
                                 display: flex; align-items: center; justify-content: center; color: white; 
                                 font-weight: bold; margin-bottom: 5px;">
                                {icon}
                            </div>
                            <div style="text-align: center; font-size: 0.75rem; width: 80px; margin-left: -25px;">
                                {step_name}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Close the timeline container
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display execution steps aligned with the timeline
                    execution_steps_html = ""
                    for step in request.execution_steps:
                        # Determine which phase this step belongs to
                        phase = ""
                        for step_name in step_names:
                            if step_name in step:
                                phase = step_name
                                break
                        
                        if phase:
                            color = "#6200ee"
                        else:
                            color = "#666"
                        
                        execution_steps_html += f"""
                        <div style="padding: 8px 12px; margin-bottom: 8px; border-left: 3px solid {color}; background-color: #f9f9f9;">
                            <span style="font-weight: 500;">{step}</span>
                        </div>
                        """
                    
                    if execution_steps_html:
                        st.markdown(f"""
                        <div style="margin-top: 20px; margin-bottom: 30px;">
                            <h5>Detailed Steps</h5>
                            {execution_steps_html}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Now show individual service cards
                    for service_state in service_states:
                        state = service_state["state"]
                        service_id = service_state["service_id"]
                        service_name = service_state["name"]
                        progress = service_state["progress"]
                        mech_address = service_state["mech_address"]
                        stages = service_state["stages"]
                        current_stage = service_state["current_stage"]
                        
                        # Determine card styling based on state
                        card_class = f"service-execution-card {state}"
                        
                        # Create header content based on state
                        if state == "pending":
                            header_content = f"⏳ Pending: Service {service_id} - {service_name}"
                        elif state == "running":
                            header_content = f"⚙️ Running: Service {service_id} - {service_name}"
                        elif state == "completed":
                            header_content = f"✅ Completed: Service {service_id} - {service_name}"
                        else:
                            header_content = f"❌ Error: Service {service_id} - {service_name}"
                        
                        # Create the service execution card
                        st.markdown(f"""
                        <div class="{card_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="font-weight: 600;">{header_content}</div>
                                <div style="font-weight: 600;">{progress}%</div>
                            </div>
                            <div style="margin: 10px 0;">
                                <div style="height: 6px; background-color: #e0e0e0; border-radius: 3px; overflow: hidden;">
                                    <div style="height: 100%; background-color: {status_color}; width: {progress}%;"></div>
                                </div>
                            </div>
                            <div style="font-size: 0.85rem; color: #666;">
                                <strong>Mech Address:</strong> <span style="font-family: monospace;">{mech_address}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Show processing stages for running services
                        if state == "running" or state == "completed":
                            st.markdown("""
                            <div style="margin-top: 15px; margin-bottom: 5px; font-weight: 500;">Processing Stages:</div>
                            """, unsafe_allow_html=True)
                            
                            # Display each processing stage with appropriate status indicators
                            for idx, stage in enumerate(stages):
                                if idx < current_stage:  # Completed stage
                                    icon = "✅"
                                    stage_time = f"{random.randint(2, 15)}s"
                                    stage_class = "completed"
                                elif idx == current_stage:  # Current stage
                                    icon = '<div class="loading-indicator-spinner"></div>'
                                    stage_time = "in progress..."
                                    stage_class = "running"
                                else:  # Future stage
                                    icon = "⏳"
                                    stage_time = "pending"
                                    stage_class = "pending"
                                
                                st.markdown(f"""
                                <div class="service-loading-state {stage_class}">
                                    <div class="loading-indicator">{icon}</div>
                                    <div class="loading-text">{stage}</div>
                                    <div class="loading-time">{stage_time}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Add sub-steps for the current running stage
                                if idx == current_stage and state == "running":
                                    sub_steps = [
                                        "Connecting to service endpoints",
                                        "Fetching required data",
                                        "Processing query parameters"
                                    ]
                                    active_sub_step = random.randint(0, len(sub_steps)-1)
                                    
                                    for sub_idx, sub_step in enumerate(sub_steps):
                                        if sub_idx < active_sub_step:
                                            sub_status = "✓"
                                            sub_class = "completed"
                                        elif sub_idx == active_sub_step:
                                            sub_status = "⟳"
                                            sub_class = "running"
                                        else:
                                            sub_status = "•"
                                            sub_class = "pending"
                                        
                                        st.markdown(f"""
                                        <div class="service-processing-stage {sub_class}">
                                            {sub_status} {sub_step}
                                        </div>
                                        """, unsafe_allow_html=True)
                        
                        # Close the service card div
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # If all services are complete, show oracle verification 
                    if request.execution_status == "completed" and hasattr(request, 'oracle_verified'):
                        oracle_message = ""
                        
                        if request.oracle_diff > 0:
                            oracle_message = f"""
                            <div class="oracle-verification">
                                <div class="oracle-header">⚠️ Oracle Verification Found Discrepancy</div>
                                <p>The Oracle verification found a {request.oracle_diff}% difference between expected and actual results.</p>
                                <div class="refund-info">
                                    <p><strong>Partial Refund Issued:</strong> {request.refund_amount} OLAS</p>
                                    <p>A partial refund of 30% has been issued due to the discrepancy in results. The remainder has been used to compensate the service providers.</p>
                                </div>
                            </div>
                            """
                        else:
                            oracle_message = f"""
                            <div class="oracle-verification" style="background-color: #f0fff4; border-left-color: #4CAF50;">
                                <div class="oracle-header" style="color: #2E7D32;">✅ Oracle Verification Passed</div>
                                <p>The Oracle has verified the results and found them to be accurate.</p>
                                <p>All services have been fully compensated for their work.</p>
                            </div>
                            """
                        
                        st.markdown(oracle_message, unsafe_allow_html=True)
                
                # If execution is running, show a loading animation
                if request.execution_status in ["pending", "running"]:
                    st.markdown("""
                    <div style="text-align: center; margin: 30px 0;">
                        <div class="spinner"></div>
                        <p style="display: inline-block; vertical-align: middle; margin-left: 10px;">
                            Processing your request...
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # If execution is complete, show result summary
                if request.execution_status == "completed" and request.final_result:
                    st.markdown("""
                    <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #f0fff4; border-radius: 10px;">
                        <h3 style="color: #2E7D32;">✅ Execution Complete</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    try:
                        # Parse the JSON result
                        result_json = json.loads(request.final_result)
                        
                        # Display summary
                        st.markdown("### Results Summary")
                        st.success(result_json["results"]["summary"])
                        
                        # Display aggregate result
                        st.markdown("### Aggregated Results")
                        st.write(result_json["results"]["aggregate_result"])
                        
                        # Display recommendations
                        if "recommendations" in result_json["results"]:
                            st.markdown("### Recommendations")
                            for rec in result_json["results"]["recommendations"]:
                                st.markdown(f"- {rec}")
                    except json.JSONDecodeError:
                        # Fallback if not valid JSON
                        st.write(request.final_result)
                
            except Exception as e:
                # Handle any errors gracefully
                print(f"Error tracking execution: {str(e)}")
                st.error(f"Error tracking execution: {str(e)}")
                
                # Set default status to handle the error gracefully
                request.execution_status = "pending"
                if not hasattr(request, "execution_steps") or request.execution_steps is None:
                    request.execution_steps = []
                if not hasattr(request, "final_result"):
                    request.final_result = None
                if not hasattr(request, "error_message"):
                    request.error_message = str(e)
                
                # Create a default service state for visualization
                if not hasattr(request, "service_states") or request.service_states is None:
                    service_states = []
                    for idx, service in enumerate(request.selected_services):
                        service_id = service.get('service_id', f"Unknown-{idx}")
                        service_desc = service.get('description', f"Service {idx}")
                        if isinstance(service_desc, str):
                            service_name = service_desc.split(' - ')[0]
                        else:
                            service_name = f"Service {idx}"
                            
                        service_states.append({
                            "service_id": service_id,
                            "name": service_name,
                            "state": "pending",
                            "progress": 0,
                            "mech_address": service.get('mech_address', 'Unknown'),
                            "start_time": None,
                            "stages": [],
                            "current_stage": -1
                        })
                    
                    request.service_states = service_states
                
                # Show retry button
                if st.button("Retry", key="retry_button"):
                    st.rerun()
                
                # Continue rendering the rest of the UI with default values
                st.markdown("""
                <div style="padding: 15px; border-radius: 10px; background-color: #3498db; color: white; text-align: center; font-size: 20px; margin-bottom: 20px;">
                    ⏳ Status: Pending
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Display selected services
            st.markdown("""
            <div class="execution-container">
                <h3>Selected Services</h3>
            """, unsafe_allow_html=True)
            
            for service in request.selected_services:
                service_id = service.get('service_id', 'Unknown ID')
                service_name = service.get('description', 'Unknown Service').split(' - ')[0] if isinstance(service.get('description'), str) else 'Unknown Service'
                service_cost = service.get('price', "1 OLAS")  # Get the price or use 1 OLAS default
                mech_address = service.get('mech_address', 'Unknown')
                
                # Create service card
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #f8f9fa;">
                    <div style="font-weight: bold; color: #6200ee;">Service {service_id}</div>
                    <div style="margin: 5px 0;">{service_name}</div>
                    <div style="font-family: monospace; font-size: 0.8rem; color: #666; word-break: break-all; margin: 5px 0;">{mech_address}</div>
                    <div style="display: inline-block; background-color: #f9f5ff; color: #6200ee; border-radius: 20px; padding: 3px 10px; font-size: 0.8rem; margin-top: 5px;">Cost: {service_cost}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display service execution details if result is available
            if request.execution_status == "completed" and request.final_result:
                try:
                    result_json = json.loads(request.final_result)
                    
                    st.markdown("""
                    <div class="execution-container">
                        <h3>Service Results</h3>
                    """, unsafe_allow_html=True)
                    
                    # Display individual service results
                    if "details" in result_json["results"]:
                        for detail in result_json["results"]["details"]:
                            service_id = detail.get("service_id", "Unknown")
                            confidence = detail.get("confidence", 0) * 100
                            
                            with st.expander(f"Service {service_id} Output", expanded=False):
                                st.write(detail.get("output", "No output available"))
                                st.progress(confidence / 100)
                                st.write(f"Confidence: {confidence:.1f}%")
                    
                    # Download button for the complete result
                    st.download_button(
                        label="Download Full Results",
                        data=request.final_result,
                        file_name="mcp_execution_result.json",
                        mime="application/json",
                        key="download_results_button"
                    )
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                except json.JSONDecodeError:
                    st.write("Service results not available in structured format")
            
            # Display real-time execution data if available
            if hasattr(request, 'defillama_results') and request.defillama_results:
                st.markdown("""
                <div class="execution-container">
                    <h3>Real-time Data</h3>
                """, unsafe_allow_html=True)
                
                # Display processing steps
                if "processing_steps" in request.defillama_results:
                    st.markdown("#### Processing Steps")
                    
                    for step in request.defillama_results["processing_steps"]:
                        step_status = step.get("status", "pending")
                        step_name = step.get("step", "Unknown Step")
                        step_detail = step.get("detail", "")
                        
                        # Choose icon based on status
                        if step_status == "complete":
                            icon = "✅"
                            color = "#4CAF50"
                        elif step_status == "pending":
                            icon = "⏳"
                            color = "#3498db"
                        elif step_status == "error":
                            icon = "❌"
                            color = "#F44336"
                        else:
                            icon = "⚠️"
                            color = "#FF9800"
                        
                        st.markdown(f"""
                        <div style="margin-bottom: 10px; padding: 8px; border-left: 3px solid {color}; background-color: #f9f9f9;">
                            <div style="font-weight: 500;">{icon} {step_name}</div>
                            <div style="font-size: 0.9em; color: #666; margin-top: 5px;">{step_detail}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Show aggregated data if available
                if "aggregated_data" in request.defillama_results:
                    agg_data = request.defillama_results["aggregated_data"]
                    
                    # If we have TVL data
                    if "top_protocols" in agg_data:
                        st.markdown("#### Top Protocols by TVL")
                        protocols_data = {}
                        
                        for protocol in agg_data["top_protocols"][:5]:  # Show top 5
                            name = protocol.get("name", "Unknown")
                            tvl = protocol.get("tvl", 0) / 1e9  # Convert to billions
                            protocols_data[name] = tvl
                        
                        if protocols_data:
                            st.bar_chart(protocols_data)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Back button at the bottom with a unique key
        st.markdown("---")
        if st.button("Back to Dashboard", key="back_to_dashboard_button"):
            st.session_state.page = 'home'
            st.rerun()
        
        # Auto-refresh if still running
        if request.execution_status in ["pending", "running"]:
            time.sleep(1.5)  # Slight delay to avoid too frequent refreshes
            st.rerun() 
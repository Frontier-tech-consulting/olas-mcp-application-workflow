"""Utility functions for execution status processing and display."""
import random
import json
import copy
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

def deep_copy_request(request):
    """Create a deep copy of a request object, whether dict or object"""
    if not request:
        return None
        
    try:
        # For dictionaries, use copy.deepcopy
        if isinstance(request, dict):
            return copy.deepcopy(request)
        else:
            # For objects, try to copy attributes
            try:
                # Try to use object's own copy method if available
                return request.copy()
            except AttributeError:
                # Create a dictionary copy if object doesn't have copy method
                return {
                    "prompt": getattr(request, "prompt", ""),
                    "selected_services": copy.deepcopy(getattr(request, "selected_services", [])),
                    "user_email": getattr(request, "user_email", ""),
                    "total_cost": getattr(request, "total_cost", 0),
                    "transaction_id": getattr(request, "transaction_id", None),
                    "submitted_at": getattr(request, "submitted_at", None)
                }
    except Exception as e:
        print(f"Error copying request: {str(e)}")
        # Return the original as a fallback - not ideal but better than None
        return request

def generate_random_transaction_id():
    """Generate a random transaction hash that looks like a Gnosis Chain tx"""
    return f"0x{''.join(random.choices('0123456789abcdef', k=64))}"

def get_service_name(service_id, services_map=None, service_name_map=None):
    """Get the name of a service from its ID"""
    # Define default service name map if not provided
    if service_name_map is None:
        service_name_map = {
            "1722": "DeFi Analytics Service",
            "1815": "Token Price Analysis Service", 
            "1966": "AI Task Execution Service",
            "1961": "AI Task Execution Service",
            "1983": "AI Task Processing Mech",
            "1993": "Task Execution Mech Service",
            "1999": "Yield Farming Optimizer",
            "2010": "Nevermined Subscription Mech"
        }
    
    # Handle the case where service_id is None or empty
    if not service_id:
        return "Unknown Service"
        
    try:
        # If service_id is already a dict, extract the id
        if isinstance(service_id, dict) and 'id' in service_id:
            service_id = service_id['id']
        
        # Handle string representations of dictionaries
        if isinstance(service_id, str) and service_id.startswith('{') and service_id.endswith('}'):
            try:
                service_dict = json.loads(service_id.replace("'", "\""))
                service_id = service_dict.get('id', service_id)
            except:
                pass
                
        # First try the service_name_map
        if service_name_map and str(service_id) in service_name_map:
            return service_name_map[str(service_id)]
            
        # Then try the services_map
        if services_map and service_id in services_map:
            service = services_map[service_id]
            return service.get('name', service.get('description', f"Service {service_id}"))
        
        # Return a default service name if not found
        return f"Service {service_id}"
    except Exception as e:
        print(f"Error getting service name: {str(e)}")
        return f"Service {service_id}"

def generate_pipeline_steps(service_ids, request_text=""):
    """Generate the model context execution pipeline for the given service IDs and request text"""
    # Return default steps if no service IDs
    if not service_ids:
        print("No service IDs provided for pipeline steps. Using default steps.")
        return get_default_pipeline_steps()
    
    try:
        # Initialize ChatOpenAI with a reasonable temperature
        chat_model = ChatOpenAI(temperature=0.2)
        
        # Create a prompt template for generating pipeline steps
        prompt = ChatPromptTemplate.from_template(
            """You are an AI orchestration system that creates execution pipelines for AI service requests.
            Generate a detailed, realistic execution pipeline for processing a user request with the following services.
            
            User Request: {request_text}
            Services: {services}
            
            Create a pipeline with 5-7 steps that covers:
            1. Initial request parsing and validation
            2. Data collection and processing specific to the request
            3. Service-specific processing steps (one per service)
            4. Integration of results
            5. Final response generation and verification
            
            For each step include:
            - name: A short name for the step
            - description: A detailed description of what happens in this step
            - status: One of "complete", "in_progress", "pending", based on position
            - duration: A realistic duration in seconds for the step
            
            Format your response as a JSON array of step objects.
            """
        )
        
        # Format service information for the prompt
        service_info = []
        for service_id in service_ids:
            service_name = get_service_name(service_id)
            service_info.append(f"{service_name} (ID: {service_id})")
        
        services_str = ", ".join(service_info)
        
        # If we don't have a request_text, use a default
        if not request_text:
            request_text = "Analyze current DeFi market trends and recommend investment strategies"
        
        # Create and execute the chain
        chain = prompt | chat_model | JsonOutputParser()
        
        try:
            # Try to generate pipeline steps using the LLM
            pipeline_steps = chain.invoke({
                "request_text": request_text, 
                "services": services_str
            })
            
            # Set appropriate statuses based on position
            # First 2 steps complete, current step in progress, rest pending
            for i, step in enumerate(pipeline_steps):
                if i < 2:
                    step["status"] = "complete"
                elif i == 2:
                    step["status"] = "in_progress"
                else:
                    step["status"] = "pending"
                    
            return pipeline_steps
            
        except Exception as e:
            # Fall back to default steps if generation fails
            print(f"Error generating pipeline steps: {str(e)}")
            return generate_fallback_steps(service_ids)
            
    except Exception as e:
        print(f"Error in generate_pipeline_steps: {str(e)}")
        return generate_fallback_steps(service_ids)

def get_default_pipeline_steps():
    """Generate default pipeline steps when no service IDs are provided"""
    return [
        {"name": "Request Initialization", "description": "Processing initial request parameters", "status": "complete", "duration": "2 seconds"},
        {"name": "Service Selection", "description": "Determining appropriate services for the request", "status": "complete", "duration": "3 seconds"},
        {"name": "Data Collection", "description": "Gathering relevant DeFi market data from trusted sources", "status": "in_progress", "duration": "5 seconds"},
        {"name": "Market Analysis", "description": "Processing gathered market data to identify key trends and patterns", "status": "pending", "duration": "7 seconds"},
        {"name": "Strategy Formulation", "description": "Developing investment strategies based on market analysis", "status": "pending", "duration": "6 seconds"},
        {"name": "Report Generation", "description": "Compiling analysis and recommendations into a comprehensive report", "status": "pending", "duration": "4 seconds"}
    ]

def generate_fallback_steps(service_ids):
    """Generate fallback pipeline steps based on service IDs"""
    steps = [
        {"name": "Request Validation", "description": "Validating input parameters and service requirements", "status": "complete", "duration": "3 seconds"}
    ]
    
    # Add steps for each service
    for service_id in service_ids:
        service_name = get_service_name(service_id)
        
        # Add service-specific steps
        if "Analytics" in service_name or "Analysis" in service_name:
            steps.append({
                "name": "Data Collection", 
                "description": f"Collecting relevant data for {service_name}", 
                "status": "complete", 
                "duration": f"{random.randint(4, 8)} seconds"
            })
            steps.append({
                "name": "Analysis Execution", 
                "description": f"Performing data analysis using {service_name}", 
                "status": "complete", 
                "duration": f"{random.randint(5, 12)} seconds"
            })
        elif "Task" in service_name or "Execution" in service_name:
            steps.append({
                "name": "Task Preparation", 
                "description": f"Preparing execution environment for {service_name}", 
                "status": "complete", 
                "duration": f"{random.randint(3, 7)} seconds"
            })
            steps.append({
                "name": "Task Execution", 
                "description": f"Running requested tasks on {service_name}", 
                "status": "complete", 
                "duration": f"{random.randint(6, 15)} seconds"
            })
        else:
            steps.append({
                "name": "Service Initialization", 
                "description": f"Initializing service {service_name}", 
                "status": "complete", 
                "duration": f"{random.randint(2, 5)} seconds"
            })
            steps.append({
                "name": "Service Execution", 
                "description": f"Processing request with {service_name}", 
                "status": "complete", 
                "duration": f"{random.randint(4, 10)} seconds"
            })
    
    # Add final result processing step
    steps.append({
        "name": "Result Aggregation", 
        "description": "Combining and formatting results from all services", 
        "status": "complete", 
        "duration": f"{random.randint(2, 6)} seconds"
    })
    
    return steps

def determine_result_type(service_name, default_type):
    """Determine the most appropriate result type based on service name"""
    service_name_lower = service_name.lower()
    
    if any(keyword in service_name_lower for keyword in ["analytics", "analysis", "insight"]):
        return "analytics"
    elif any(keyword in service_name_lower for keyword in ["price", "prediction", "forecast"]):
        return "prediction"
    elif any(keyword in service_name_lower for keyword in ["token", "nft", "asset"]):
        return "token"
    elif any(keyword in service_name_lower for keyword in ["feed", "stream", "data"]):
        return "data_feed"
    elif any(keyword in service_name_lower for keyword in ["optimize", "efficiency", "improve"]):
        return "optimization"
    else:
        return default_type

def generate_mock_data_for_defillama():
    """Generate mock DeFi Llama data for demo purposes"""
    return {
        "aggregated_data": {
            "total_tvl": random.uniform(40, 200) * 1e9,  # $40-200B
            "top_protocols": [
                {"name": "Lido", "tvl": random.uniform(10, 30) * 1e9},
                {"name": "MakerDAO", "tvl": random.uniform(5, 15) * 1e9},
                {"name": "Aave", "tvl": random.uniform(3, 10) * 1e9}
            ],
            "token_prices": {
                "ETH": random.uniform(1500, 3500),
                "BTC": random.uniform(30000, 60000),
                "AAVE": random.uniform(50, 200)
            }
        },
        "api_calls": [
            {"endpoint": "https://api.llama.fi/protocols", "success": True},
            {"endpoint": "https://api.llama.fi/tvl/ethereum", "success": True},
            {"endpoint": "https://coins.llama.fi/prices/current/ethereum:0x...", "success": True}
        ]
    }

def format_eth_address(address):
    """Format an Ethereum address for display with ellipsis in the middle"""
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}" 
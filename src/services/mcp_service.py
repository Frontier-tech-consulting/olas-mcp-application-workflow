import json
import os
import time
import random
from typing import Dict, Any, List, Union
from ..models.request import Request
from .defillama_api import DefiLlamaAPI

class MCPService:
    """Service class for interacting with the Olas MCP"""
    
    def __init__(self, server_profile="mock"):
        self.server_profile = server_profile
        self.transactions = {}
        self.services = []
        self.infrastructure_stats = {}
        
        # Initialize default values
        self.base_url = "http://localhost:5000"
        self.api_key = "test_api_key"
        
        # If server_profile is a URL, assume it's a remote server URL
        if isinstance(server_profile, str) and server_profile.startswith("http"):
            self.base_url = server_profile
            self.server_profile = "remote"
            print(f"Using remote server at {self.base_url}")
        
        # Load mock data if using mock profile
        if self.server_profile == "mock":
            self.load_mock_services()
            self.load_mock_infrastructure_stats()
            self.defillama_api = DefiLlamaAPI()
    
    def load_mock_services(self):
        """Load mock services data from JSON file"""
        try:
            with open('enriched_services_data.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "services" in data:
                    self.services = data["services"]
                elif isinstance(data, list):
                    self.services = data
                else:
                    self.services = []
                print(f"Loaded {len(self.services)} mock services")
        except FileNotFoundError:
            print("Mock services data file not found. Using default services list.")
            # Default mock services
            self.services = [
                {
                    "service_id": "1722",
                    "description": "The mech executes AI tasks requested on-chain and delivers the results to the requester.",
                    "mech_address": "0xf07fdfed257949e0d9c399fda361edf4f35de166",
                    "safe_address": "0x9e9d9...15565",
                    "status": "Active"
                },
                {
                    "service_id": "1815",
                    "description": "The mech executes AI tasks requested on-chain and delivers the results to the requester.",
                    "mech_address": "0x478ad20ed958dcc5ad4aba6f4e4cc51e07a840e4",
                    "safe_address": "0xDFE16...b84b5",
                    "status": "Active"
                },
                {
                    "service_id": "1999",
                    "description": "Mech for useful tools",
                    "mech_address": "0xa61026515b701c9a123b0587fd601857f368127a",
                    "safe_address": "0x6ddde...45e56",
                    "status": "Active"
                }
            ]
        except json.JSONDecodeError:
            print("Error parsing services JSON file. Using default services list.")
            self.services = [
                {
                    "service_id": "1722",
                    "description": "The mech executes AI tasks requested on-chain and delivers the results to the requester.",
                    "mech_address": "0xf07fdfed257949e0d9c399fda361edf4f35de166",
                    "safe_address": "0x9e9d9...15565",
                    "status": "Active"
                }
            ]
    
    def load_mock_infrastructure_stats(self):
        """Load mock infrastructure stats from JSON file"""
        try:
            with open('olas_infrastructure_stats.json', 'r') as f:
                self.infrastructure_stats = json.load(f)
                print("Loaded mock infrastructure stats")
        except FileNotFoundError:
            print("Mock infrastructure stats file not found. Using default stats.")
            # Default mock data for infrastructure stats
            self.infrastructure_stats = {
                "ethereum": {
                    "components": [],
                    "agent_instances": 0,
                    "service_instances": 0
                },
                "gnosis": {
                    "components": [],
                    "agent_instances": 0,
                    "service_instances": 0
                }
            }
    
    def get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available services from the MCP"""
        if self.server_profile == "mock":
            return self.services
        else:
            # In a real implementation, this would call the actual MCP API
            pass
    
    def get_infrastructure_stats(self) -> Dict[str, Any]:
        """Get statistics about the Olas infrastructure"""
        if self.server_profile == "mock":
            return self.infrastructure_stats
        else:
            # In a real implementation, this would call the actual MCP API
            pass
    
    def submit_request(self, request: Request) -> str:
        """Submit a request to the MCP"""
        if self.server_profile == "mock":
            try:
                # Simulate request submission
                transaction_id = request.transaction_id or f"tx_{random.randint(1000, 9999)}_{int(time.time())}"
                print(f"Creating transaction with ID: {transaction_id}")
                
                # Ensure selected_services is properly initialized
                if not hasattr(request, 'selected_services') or request.selected_services is None:
                    request.selected_services = []
                    print("Warning: selected_services was None, initialized to empty list")
                
                # Generate mock execution steps based on selected services
                service_count = len(request.selected_services) if request.selected_services else 0
                print(f"Request has {service_count} selected services")
                
                # Create initial steps
                initial_steps = ["Request received", "Validating request parameters"]
                
                # Create a mock transaction record
                self.transactions[transaction_id] = {
                    "request": request.to_dict(),
                    "status": "pending",
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "steps": initial_steps,
                    "current_step": 0,
                    "service_count": service_count,
                    "error": None,
                    "result": None,
                    "defillama_data": None
                }
                print(f"Created transaction record for {transaction_id}")
                
                # If there are selected services, prepare for DeFi Llama API calls
                if service_count > 0 and request.prompt:
                    # Process the request with DefiLlamaAPI in the background
                    try:
                        # Get service ID from first service if available
                        service_id = None
                        if request.selected_services and len(request.selected_services) > 0:
                            first_service = request.selected_services[0]
                            if isinstance(first_service, dict) and 'service_id' in first_service:
                                service_id = first_service['service_id']
                        
                        # Use default if no valid service ID found
                        if not service_id:
                            service_id = "default_service"
                            
                        print(f"Processing DeFi Llama query for service ID: {service_id}")
                        
                        # Get data from DeFi Llama
                        defillama_results = self.defillama_api.process_query(request.prompt, service_id)
                        
                        # Store the results in the transaction
                        self.transactions[transaction_id]["defillama_data"] = defillama_results
                        
                        # If defillama_results contains processing_steps, pre-populate steps
                        # to accelerate the visualization
                        if "processing_steps" in defillama_results:
                            # Keep the initial steps
                            pre_steps = initial_steps.copy()
                            
                            # Append properly formatted processing steps for the timeline
                            for step in defillama_results["processing_steps"]:
                                step_name = step.get("step", "")
                                step_detail = step.get("detail", "")
                                step_status = step.get("status", "")
                                
                                # Format step for display in the processing pipeline
                                if "Query Analysis" in step_name:
                                    pre_steps.append(f"Query Analysis - {step_detail}")
                                elif "Parameter Inference" in step_name:
                                    pre_steps.append(f"Parameter Inference - {step_detail}")
                                elif "API" in step_name:
                                    pre_steps.append(f"API Execution - {step_detail}")
                                elif "Data Aggregation" in step_name or "Aggregating" in step_name:
                                    pre_steps.append(f"Data Aggregation - {step_detail}")
                            
                            # Update transaction steps if we have pre-populated steps
                            if len(pre_steps) > len(initial_steps):
                                self.transactions[transaction_id]["steps"] = pre_steps
                        
                        print("DeFi Llama query processed successfully")
                    except Exception as e:
                        print(f"Error processing DeFi Llama query: {str(e)}")
                
                # Return just the transaction ID string, not a dictionary
                print(f"Returning transaction ID: {transaction_id}")
                return transaction_id
            except Exception as e:
                print(f"Exception in submit_request: {str(e)}")
                # Return a fallback transaction ID in case of error
                fallback_id = f"error_tx_{int(time.time())}"
                return fallback_id
        else:
            # In a real implementation, this would call the actual MCP API
            print(f"Non-mock server profile: {self.server_profile}")
            # Return a mock transaction ID for now
            return f"remote_tx_{int(time.time())}"
    
    def get_execution_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get the status of a request execution"""
        if self.server_profile == "mock":
            # Check if transaction exists
            if transaction_id not in self.transactions:
                return {
                    "status": "error",
                    "error": "Transaction not found",
                    "steps": [],
                    "result": None
                }
            
            # Get the transaction record
            tx = self.transactions[transaction_id]
            
            # If transaction is completed or error, return immediately
            if tx["status"] in ["completed", "error"]:
                return {
                    "status": tx["status"],
                    "steps": tx["steps"],
                    "error": tx["error"],
                    "result": tx["result"]
                }
            
            # Update the transaction status based on time elapsed
            elapsed_time = time.time() - tx["created_at"]
            
            # Define the execution timeline based on selected services
            service_count = tx["service_count"]
            steps = tx["steps"].copy()
            
            # Accelerate the timeline to complete within one minute
            # Phase 1: Query Analysis (0-15 seconds)
            if elapsed_time > 2 and len(steps) == 2:
                steps.append("Query Analysis - Understanding request parameters")
            
            if elapsed_time > 5 and len(steps) == 3:
                steps.append("Parameter Inference - Extracting relevant data points")
            
            # Phase 2: API Execution (15-30 seconds)
            if elapsed_time > 10 and len(steps) == 4:
                steps.append("API Execution - Fetching required data")
            
            # Phase 3: Service Processing (30-45 seconds)
            # Add steps for each service execution in a more compact timeframe
            for i in range(service_count):
                # Calculate service name
                try:
                    service_obj = tx["request"]["selected_services"][i] if i < len(tx["request"]["selected_services"]) else {}
                    if isinstance(service_obj, dict):
                        service_name = service_obj.get("name", "") or service_obj.get("description", f"Service {i+1}")
                    else:
                        service_name = f"Service {i+1}"
                except (IndexError, KeyError, TypeError):
                    service_name = f"Service {i+1}"
                
                # Service start time - distribute evenly between 15-35 seconds
                service_start_time = 15 + (i * (20 / max(1, service_count)))
                
                if elapsed_time > service_start_time and len(steps) == 5 + i:
                    steps.append(f"Executing service {i+1}: {service_name}")
            
            # Phase 4: Data Aggregation and Result Generation (45-60 seconds)
            agg_start_time = 40
            if service_count > 0 and elapsed_time > agg_start_time and len(steps) == 5 + service_count:
                steps.append("Data Aggregation - Combining service results")
            
            result_time = 50
            if elapsed_time > result_time and len(steps) == 6 + service_count:
                steps.append("Result Generation - Preparing final output")
            
            # Complete the transaction at the 60-second mark
            if elapsed_time > 55 and len(steps) == 7 + service_count:
                steps.append("Request completed")
                tx["status"] = "completed"
                
                # Generate a result with real data if available
                defillama_data = tx.get("defillama_data")
                if defillama_data:
                    # Create a structured result
                    result = {
                        "transaction_id": transaction_id,
                        "request": tx["request"],
                        "results": {
                            "summary": defillama_data.get("summary", "Analysis complete"),
                            "aggregate_result": defillama_data.get("aggregated_data", {}),
                            "details": [],
                            "processing_steps": defillama_data.get("processing_steps", [])
                        }
                    }
                    
                    # Add details for each service with more descriptive information
                    for i, service in enumerate(tx["request"]["selected_services"]):
                        service_id = service.get("service_id", f"S{i+1}")
                        service_name = service.get("name", service.get("description", f"Service {i+1}"))
                        
                        # Extract relevant API calls for this service
                        relevant_calls = []
                        if defillama_data and "api_calls" in defillama_data:
                            # Assign API calls to each service
                            for call in defillama_data["api_calls"]:
                                relevant_calls.append(call)
                        
                        # Create service-specific output
                        service_detail = {
                            "service_id": service_id,
                            "name": service_name,
                            "confidence": random.uniform(0.8, 0.99),  # Mock confidence score
                            "processing_time": f"{random.randint(2, 15)} seconds",
                            "status": "completed"
                        }
                        
                        # Add API call results if available
                        if relevant_calls:
                            if i < len(relevant_calls):
                                service_detail["output"] = relevant_calls[i]
                            else:
                                service_detail["output"] = relevant_calls[-1]  # Use the last one
                        else:
                            service_detail["output"] = "No API data available"
                        
                        result["results"]["details"].append(service_detail)
                    
                    # Add recommendations based on the data
                    recommendations = []
                    
                    # TVL-based recommendations
                    if "top_protocols" in defillama_data.get("aggregated_data", {}):
                        top_protocol = defillama_data["aggregated_data"]["top_protocols"][0]
                        recommendations.append(
                            f"Consider focusing on {top_protocol.get('name', 'top protocols')} which has the highest TVL"
                        )
                    
                    # Yield-based recommendations
                    if "top_yield_pools" in defillama_data.get("aggregated_data", {}):
                        top_pool = defillama_data["aggregated_data"]["top_yield_pools"][0]
                        recommendations.append(
                            f"For highest yields, consider {top_pool.get('pool', 'top pools')} with {top_pool.get('apy', 0):.2f}% APY"
                        )
                    
                    # Add recommendations to the result
                    if recommendations:
                        result["results"]["recommendations"] = recommendations
                    
                    tx["result"] = json.dumps(result)
                else:
                    # Fallback to a simple result
                    tx["result"] = json.dumps({
                        "transaction_id": transaction_id,
                        "results": {
                            "summary": "Analysis complete, but no detailed data available",
                            "aggregate_result": {},
                            "details": []
                        }
                    })
            
            # Update the transaction record
            tx["steps"] = steps
            tx["updated_at"] = time.time()
            tx["current_step"] = len(steps) - 1
            
            # Return the current status
            return {
                "status": tx["status"],
                "steps": tx["steps"],
                "error": tx["error"],
                "result": tx["result"]
            }
        else:
            # For real implementations, return a default pending status
            # rather than None or pass
            print(f"Using real implementation for transaction {transaction_id}, returning default status")
            return {
                "status": "pending",
                "steps": ["Initializing execution", "Connecting to services"],
                "error": None,
                "result": None
            } 
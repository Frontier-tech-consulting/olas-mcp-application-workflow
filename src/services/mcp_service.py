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
                
                # Create a mock transaction record
                self.transactions[transaction_id] = {
                    "request": request.to_dict(),
                    "status": "pending",
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "steps": ["Request received", "Validating request parameters"],
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
                        service_id = request.selected_services[0].get('service_id', '1722')
                        print(f"Processing DeFi Llama query for service ID: {service_id}")
                        defillama_results = self.defillama_api.process_query(request.prompt, service_id)
                        self.transactions[transaction_id]["defillama_data"] = defillama_results
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
            
            # Add steps for service preparation
            if elapsed_time > 2 and len(steps) == 2:
                steps.append("Preparing selected services")
                
            # Add steps for each service execution
            for i in range(service_count):
                # Safely extract service name with fallback
                try:
                    service_obj = tx["request"]["selected_services"][i] if i < len(tx["request"]["selected_services"]) else {}
                    if isinstance(service_obj, dict):
                        service_name = service_obj.get("name", "") or service_obj.get("description", f"Service {i+1}")
                    else:
                        service_name = f"Service {i+1}"
                except (IndexError, KeyError, TypeError):
                    service_name = f"Service {i+1}"
                    
                service_start_time = 4 + (i * 3)  # Start times for each service
                
                if elapsed_time > service_start_time and len(steps) == 3 + (i * 2):
                    steps.append(f"Executing service {i+1}: {service_name}")
                
                if elapsed_time > service_start_time + 2 and len(steps) == 4 + (i * 2):
                    steps.append(f"Service {i+1} execution completed")
            
            # Add final steps
            if service_count > 0:
                final_step_time = 4 + (service_count * 3)
                if elapsed_time > final_step_time and len(steps) == 3 + (service_count * 2):
                    steps.append("Aggregating service results")
                
                if elapsed_time > final_step_time + 2 and len(steps) == 4 + (service_count * 2):
                    steps.append("Generating final response")
                    
                # Complete the transaction
                if elapsed_time > final_step_time + 4 and len(steps) == 5 + (service_count * 2):
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
                                "details": []
                            }
                        }
                        
                        # Add details for each service
                        for i, service in enumerate(tx["request"]["selected_services"]):
                            service_id = service.get("service_id", f"S{i+1}")
                            service_name = service.get("name", f"Service {i+1}")
                            
                            # Extract relevant API calls for this service
                            relevant_calls = []
                            if defillama_data and "api_calls" in defillama_data:
                                # Select calls based on service type/ID
                                for call in defillama_data["api_calls"]:
                                    relevant_calls.append(call)
                            
                            # Create service-specific output
                            result["results"]["details"].append({
                                "service_id": service_id,
                                "name": service_name,
                                "output": relevant_calls[min(i, len(relevant_calls)-1)] if relevant_calls else "No data available",
                                "confidence": random.uniform(0.8, 0.99)  # Mock confidence score
                            })
                        
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
            else:
                # If no services selected, complete quickly
                if elapsed_time > 2 and len(steps) == 3:
                    steps.append("No services to execute")
                
                if elapsed_time > 4 and len(steps) == 4:
                    steps.append("Request completed")
                    tx["status"] = "completed"
                    tx["result"] = json.dumps({
                        "transaction_id": transaction_id,
                        "results": {
                            "summary": "No services were selected for execution",
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
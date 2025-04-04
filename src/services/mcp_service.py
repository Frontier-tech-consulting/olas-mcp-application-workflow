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
            # Enhanced mock services with variety for different query types
            self.services = [
                {
                    "service_id": "1722",
                    "description": "DeFi Analytics - Provides comprehensive data analysis of DeFi protocols and market trends.",
                    "mech_address": "0xf07fdfed257949e0d9c399fda361edf4f35de166",
                    "owner_address": "0x9e9d9...15565",
                    "status": "Active",
                    "version": "1.2.3",
                    "threshold": "1.5"
                },
                {
                    "service_id": "1815",
                    "description": "Token Price Analysis - Specialized in tracking and predicting price movements of crypto tokens.",
                    "mech_address": "0x478ad20ed958dcc5ad4aba6f4e4cc51e07a840e4",
                    "owner_address": "0xDFE16...b84b5",
                    "status": "Active",
                    "version": "1.0.4",
                    "threshold": "1.0"
                },
                {
                    "service_id": "1999",
                    "description": "Yield Farming Optimizer - Identifies the highest yield opportunities across different protocols.",
                    "mech_address": "0xa61026515b701c9a123b0587fd601857f368127a",
                    "owner_address": "0x6ddde...45e56",
                    "status": "Active",
                    "version": "2.1.0",
                    "threshold": "1.2"
                },
                {
                    "service_id": "2101",
                    "description": "Risk Assessment Tool - Evaluates security risks and vulnerabilities in DeFi protocols.",
                    "mech_address": "0xb87de244f368c4c4f5f0d173973dc0645a78eeae",
                    "owner_address": "0x45fa8...27cde",
                    "status": "Active",
                    "version": "1.1.5",
                    "threshold": "2.0"
                },
                {
                    "service_id": "2255",
                    "description": "NFT Market Analysis - Tracks and analyzes trends in NFT marketplaces and collections.",
                    "mech_address": "0xc72ef03f0aac890f02879d98e96ef0622f13ae4b",
                    "owner_address": "0x78ab3...9cd4f",
                    "status": "Active",
                    "version": "1.3.2",
                    "threshold": "1.0"
                },
                {
                    "service_id": "2367",
                    "description": "Stablecoin Monitor - Monitors stablecoin pegs and liquidity across different blockchains.",
                    "mech_address": "0xd16e12a23607013a18528dd96e837fff7e836454",
                    "owner_address": "0xa923c...f78e1",
                    "status": "Active",
                    "version": "1.4.0",
                    "threshold": "0.8"
                },
                {
                    "service_id": "2488",
                    "description": "Cross-Chain Bridge Analyzer - Analyzes efficiencies and security of cross-chain bridge protocols.",
                    "mech_address": "0xf92d3163ff26f9c297dc05d29fda6a2ed80279bb",
                    "owner_address": "0x39fe4...a12b8",
                    "status": "Active",
                    "version": "0.9.5",
                    "threshold": "1.3"
                }
            ]
        except json.JSONDecodeError:
            print("Error parsing services JSON file. Using default services list.")
            self.services = [
                {
                    "service_id": "1722",
                    "description": "DeFi Analytics - Provides comprehensive data analysis of DeFi protocols and market trends.",
                    "mech_address": "0xf07fdfed257949e0d9c399fda361edf4f35de166",
                    "owner_address": "0x9e9d9...15565",
                    "status": "Active",
                    "version": "1.2.3",
                    "threshold": "1.5"
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
        """Get status of a request execution"""
        if self.server_profile == "mock":
            # Get the transaction record
            transaction = self.transactions.get(transaction_id)
            if not transaction:
                print(f"Warning: Transaction {transaction_id} not found.")
                # If transaction not found, create a mock one with minimal data
                transaction = {
                    "status": "pending",
                    "steps": ["Request received"],
                    "current_step": 0,
                    "error": None,
                    "result": None,
                    "service_count": 0,
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "request": {"prompt": "Unknown request", "selected_services": []},
                    "service_results": []
                }
                self.transactions[transaction_id] = transaction
                
            # Calculate time elapsed since request creation
            time_elapsed = time.time() - transaction.get("created_at", 0)
            
            # Get request data for reference
            request_data = transaction.get("request", {})
            selected_services = request_data.get("selected_services", [])
            service_count = len(selected_services)
            
            # Initialize service results if not already present
            if "service_results" not in transaction:
                transaction["service_results"] = []
                # Create initial results for each service
                for idx, service in enumerate(selected_services):
                    service_id = service.get("service_id", f"unknown-{idx}")
                    transaction["service_results"].append({
                        "service_id": service_id,
                        "name": service.get("description", f"Service {service_id}").split(" - ")[0],
                        "status": "pending",
                        "progress": 0,
                        "start_time": None,
                        "execution_steps": [],
                        "result": None,
                        "error": None
                    })
            
            # Update the execution status based on time elapsed
            if time_elapsed < 3:
                # Initial phase - request received and validating
                transaction["status"] = "pending"
                steps = transaction.get("steps", [])
                if len(steps) == 0:
                    steps.append("Request received")
                if len(steps) == 1 and time_elapsed > 1:
                    steps.append("Validating request parameters")
                transaction["steps"] = steps
            elif time_elapsed < 30:
                # Running phase - update steps based on time elapsed
                transaction["status"] = "running"
                
                # Define the expected timeline of steps
                timeline = [
                    (3, "Query Analysis - Understanding request parameters"),
                    (6, "Parameter Inference - Determining optimal service parameters"),
                    (10, "API Execution - Connecting to external data sources"),
                    (15, "Service Processing - Running analysis on retrieved data"),
                    (20, "Data Aggregation - Combining results from different services"),
                    (25, "Result Generation - Preparing final response")
                ]
                
                # Update steps based on time
                steps = transaction.get("steps", [])
                for threshold, step in timeline:
                    if time_elapsed >= threshold and step not in steps:
                        steps.append(step)
                transaction["steps"] = steps
                
                # Update service-specific statuses
                for idx, service_result in enumerate(transaction.get("service_results", [])):
                    # Stagger service execution to make it look realistic
                    service_delay = idx * 4  # seconds between service starts
                    service_time_elapsed = time_elapsed - service_delay
                    
                    if service_time_elapsed <= 0:
                        # Service not started yet
                        continue
                        
                    # Set start time if not set
                    if not service_result["start_time"]:
                        service_result["start_time"] = time.time() - service_time_elapsed
                    
                    # Update service status based on service_time_elapsed
                    if service_time_elapsed < 2:
                        service_result["status"] = "pending"
                        service_result["progress"] = 0
                    elif service_time_elapsed < 20:
                        service_result["status"] = "running"
                        # Calculate progress as a percentage (cap at 95% until completed)
                        service_result["progress"] = min(95, int(service_time_elapsed / 20 * 100))
                        
                        # Add execution steps for this service
                        execution_steps = service_result.get("execution_steps", [])
                        service_timeline = [
                            (1, "Initializing service"),
                            (3, "Loading data sources"),
                            (6, "Processing request"),
                            (10, "Analyzing results"),
                            (15, "Preparing response")
                        ]
                        
                        for step_time, step_desc in service_timeline:
                            if service_time_elapsed >= step_time and step_desc not in execution_steps:
                                execution_steps.append(step_desc)
                        
                        service_result["execution_steps"] = execution_steps
                    else:
                        # Service complete
                        service_result["status"] = "completed"
                        service_result["progress"] = 100
                        
                        # Ensure all steps are included
                        if len(service_result.get("execution_steps", [])) < 5:
                            service_result["execution_steps"] = [
                                "Initializing service",
                                "Loading data sources",
                                "Processing request",
                                "Analyzing results",
                                "Preparing response",
                                "Finalizing"
                            ]
                        
                        # Add a result if not already present
                        if not service_result["result"]:
                            service_id = service_result["service_id"]
                            prompt = request_data.get("prompt", "")
                            
                            # Generate a relevant mock result based on service ID and prompt
                            service_result["result"] = {
                                "confidence": random.uniform(0.75, 0.98),
                                "output": self._generate_mock_output(service_id, prompt),
                                "processing_time": random.uniform(1.5, 3.5)
                            }
            else:
                # Completed phase
                transaction["status"] = "completed"
                
                # Make sure all services are completed
                for service_result in transaction.get("service_results", []):
                    service_result["status"] = "completed"
                    service_result["progress"] = 100
                    
                    # Ensure service has a result
                    if not service_result["result"]:
                        service_id = service_result["service_id"]
                        prompt = request_data.get("prompt", "")
                        service_result["result"] = {
                            "confidence": random.uniform(0.85, 0.99),
                            "output": self._generate_mock_output(service_id, prompt),
                            "processing_time": random.uniform(2.0, 4.0)
                        }
                
                # Generate an aggregated result if not already present
                if not transaction["result"]:
                    # Create a structured result combining individual service results
                    final_result = {
                        "timestamp": time.time(),
                        "transaction_id": transaction_id,
                        "status": "success",
                        "results": {
                            "summary": self._generate_summary_for_prompt(request_data.get("prompt", "")),
                            "details": [],
                            "aggregate_result": {},
                            "recommendations": []
                        }
                    }
                    
                    # Add individual service results to the details
                    for service_result in transaction.get("service_results", []):
                        service_detail = {
                            "service_id": service_result["service_id"],
                            "name": service_result["name"],
                            "confidence": service_result["result"]["confidence"],
                            "output": service_result["result"]["output"],
                            "processing_time": service_result["result"]["processing_time"]
                        }
                        final_result["results"]["details"].append(service_detail)
                    
                    # Add aggregated data
                    prompt = request_data.get("prompt", "").lower()
                    if "apy" in prompt or "yield" in prompt:
                        final_result["results"]["aggregate_result"] = {
                            "average_apy": random.uniform(3.5, 12.8),
                            "highest_apy": random.uniform(15.0, 40.0),
                            "lowest_risk": random.uniform(1.5, 4.5),
                            "timeframe": "30 days"
                        }
                    elif "price" in prompt or "value" in prompt:
                        final_result["results"]["aggregate_result"] = {
                            "price_change": random.uniform(-15.0, 25.0),
                            "market_sentiment": random.choice(["bullish", "neutral", "bearish"]),
                            "volume_change": random.uniform(-10.0, 30.0),
                            "timeframe": "7 days"
                        }
                    else:
                        final_result["results"]["aggregate_result"] = {
                            "total_tvl": f"${random.randint(50, 200)}B",
                            "protocols_analyzed": random.randint(15, 50),
                            "confidence_level": random.uniform(0.85, 0.97)
                        }
                    
                    # Add recommendations
                    recommendations = [
                        f"Consider exploring {random.choice(['Uniswap V3', 'Aave', 'Compound', 'Curve'])} for better rates",
                        f"Monitor {random.choice(['price fluctuations', 'APY changes', 'TVL shifts'])} over the next week",
                        f"Diversify across {random.randint(2, 5)} different protocols to minimize risk"
                    ]
                    final_result["results"]["recommendations"] = recommendations
                    
                    # Store the final result as JSON
                    transaction["result"] = json.dumps(final_result)
            
            # Save updates back to the transaction record
            self.transactions[transaction_id] = transaction
            
            # Return status object
            return {
                "status": transaction["status"],
                "steps": transaction["steps"],
                "service_results": transaction.get("service_results", []),
                "result": transaction["result"],
                "error": transaction["error"],
                "defillama_data": transaction.get("defillama_data", None)
            }
        else:
            # In a real implementation, this would call the actual MCP API
            # This would use the REST API to get the status of the transaction
            pass
    
    def _generate_mock_output(self, service_id: str, prompt: str) -> str:
        """Generate a mock output based on service ID and prompt"""
        prompt_lower = prompt.lower()
        
        # Different outputs based on service types
        if service_id == "1722":  # DeFi Analytics
            if "apy" in prompt_lower or "yield" in prompt_lower:
                return f"Analysis of APY rates across major DeFi protocols shows an average of {random.uniform(4.5, 15.2):.2f}% APY in the last 30 days. Uniswap V3 liquidity pools for stablecoins have shown consistent returns of {random.uniform(3.0, 8.0):.2f}% APY."
            else:
                return f"DeFi TVL analysis shows ${random.randint(40, 100)}B locked across all protocols, with a {random.uniform(-5.0, 10.0):.1f}% change in the last week. Top 3 protocols by TVL are currently MakerDAO, Aave, and Curve."
        
        elif service_id == "1815":  # Token Price Analysis
            tokens = ["ETH", "OLAS", "UNI", "AAVE", "CRV", "MKR"]
            token = random.choice(tokens)
            return f"Price analysis for {token} indicates a {random.uniform(-15.0, 25.0):.1f}% change over the past 7 days with volatility at {random.uniform(20.0, 80.0):.1f}%. Technical indicators suggest a {random.choice(['bullish', 'neutral', 'bearish'])} trend in the short term."
        
        elif service_id == "1999":  # Yield Farming Optimizer
            protocols = ["Curve", "Convex", "Yearn", "Compound", "Aave"]
            return f"Current highest yield opportunities: {random.choice(protocols)} {random.uniform(5.0, 25.0):.2f}% APY for stablecoins, {random.choice(protocols)} {random.uniform(10.0, 50.0):.2f}% APY for {random.choice(['ETH-USDC', 'BTC-ETH', 'OLAS-ETH'])} pairs."
        
        else:  # Generic response for other services
            return f"Analysis complete. Found {random.randint(3, 15)} relevant data points with {random.uniform(80.0, 98.0):.1f}% confidence. The most significant factor identified was {random.choice(['liquidity depth', 'price volatility', 'protocol adoption', 'gas costs', 'market sentiment'])}."
    
    def _generate_summary_for_prompt(self, prompt: str) -> str:
        """Generate a relevant summary based on the user's prompt"""
        prompt_lower = prompt.lower()
        
        if "apy" in prompt_lower or "yield" in prompt_lower:
            return f"Your request for yield analysis has been processed. We analyzed {random.randint(10, 50)} protocols and found APY rates ranging from {random.uniform(0.5, 5.0):.2f}% to {random.uniform(15.0, 50.0):.2f}%. The most stable yields were observed in {random.choice(['stablecoin pairs', 'ETH-based pools', 'blue-chip token farms'])}."
        
        elif "price" in prompt_lower or "value" in prompt_lower:
            return f"Price analysis complete. The requested assets have shown {random.choice(['high volatility', 'stable performance', 'upward momentum'])} over the past {random.randint(7, 30)} days. Market sentiment is currently {random.choice(['bullish', 'neutral', 'bearish'])} based on on-chain metrics and trading volumes."
            
        elif "risk" in prompt_lower:
            return f"Risk assessment complete. The analyzed protocols show {random.choice(['low', 'moderate', 'varying'])} risk profiles. Key factors affecting risk include protocol maturity, TVL stability, and audit history. Recommended diversification across {random.randint(3, 7)} different protocols to minimize exposure."
            
        else:
            return f"Analysis of your request has been completed successfully. Our services processed the data using {random.randint(3, 8)} different methodologies to ensure accuracy. The results provide a comprehensive view of the current market conditions relevant to your query." 
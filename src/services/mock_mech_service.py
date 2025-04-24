# src/services/mock_mech_service.py
import os
import json
import logging
import random
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class MockMechService:
    """Mock service that simulates mech-client library interactions using existing data files."""
    
    def __init__(self):
        """Initialize the mock mech service."""
        self.mech_services = self._load_mech_services()
        self.ethereum_components = self._load_ethereum_components()
    
    def _load_mech_services(self) -> List[Dict[str, Any]]:
        """Load mech services from the deployed_mech_services.json file."""
        try:
            # Locate the deployed_mech_services.json file
            mech_services_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "utils", 
                "deployed_mech_services.json"
            )
            
            if os.path.exists(mech_services_path):
                with open(mech_services_path, 'r') as f:
                    return json.load(f)
            else:
                logging.warning(f"Could not find {mech_services_path}. Using fallback data.")
                return self._get_fallback_mech_services()
        except Exception as e:
            logging.error(f"Error loading mech services: {e}")
            return self._get_fallback_mech_services()
    
    def _load_ethereum_components(self) -> List[Dict[str, Any]]:
        """Load Ethereum components from the olas_ethereum_components.json file."""
        try:
            # Try to locate the file in multiple possible locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             ".vscode", "spec", "v0.1", "final-manus-spec", 
                             "olas_mcp_spec", "olas_ethereum_components.json"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                             "data", "olas_ethereum_components.json")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        return data.get("components", [])
            
            logging.warning("Could not find olas_ethereum_components.json. Using fallback data.")
            return self._get_fallback_ethereum_components()
        except Exception as e:
            logging.error(f"Error loading Ethereum components: {e}")
            return self._get_fallback_ethereum_components()
    
    def _get_fallback_mech_services(self) -> List[Dict[str, Any]]:
        """Return fallback mech services data."""
        return [
            {
                "name": "gnosis",
                "chainId": "100",
                "contracts": [
                    {
                        "name": "MechMarketplace",
                        "address": "0x2b6fF14b63859ef8740eCA6A3dA01F95E19F0480"
                    },
                    {
                        "name": "MechFactoryFixedPriceNative",
                        "address": "0x8b299c20F87e3fcBfF0e1B86dC0acC06AB6993EF"
                    }
                ]
            }
        ]
    
    def _get_fallback_ethereum_components(self) -> List[Dict[str, Any]]:
        """Return fallback Ethereum components data."""
        return [
            {
                "id": "277",
                "name": "Eolas Fundamental Analysis Tool",
                "description": "A tool for analyzing the fundamentals of a single token or crypto project using multiple data sources and AI analysis.",
                "version": "1",
                "owner_address": "0xCE52C86195448598F1fc39Da058f2da075bC58cD",
                "hash": "0x1225...ce55a3",
                "service_id": "1815"
            },
            {
                "id": "276",
                "name": "Eolas Technical Analysis Tool",
                "description": "A tool for analyzing technical indicators and generating AI-powered analysis for cryptocurrency pairs using TAapi and OpenAI GPT.",
                "version": "1",
                "owner_address": "0xCE52C86195448598F1fc39Da058f2da075bC58cD",
                "hash": "0x6831...fcd86f",
                "service_id": "1961"
            }
        ]
    
    def get_available_services(self, chain_id: str = "100") -> List[Dict[str, Any]]:
        """
        Get available mech services for a specific chain.
        
        Args:
            chain_id: Chain ID to filter services (default: Gnosis Chain)
            
        Returns:
            List of mech service dictionaries
        """
        # First enrich Ethereum components with service_id if not present
        for i, component in enumerate(self.ethereum_components):
            if "service_id" not in component:
                # Assign realistic service IDs based on the Olas documentation
                service_ids = ["1815", "1961", "1966", "1722", "1999", "2010"]
                component["service_id"] = service_ids[i % len(service_ids)]
        
        # Create mock service objects from the components
        services = []
        for component in self.ethereum_components:
            service = {
                "id": component.get("id", ""),
                "name": component.get("name", "Unknown Service"),
                "description": component.get("description", "No description available"),
                "service_id": component.get("service_id", ""),
                "cost": round(random.uniform(0.001, 0.05), 3),  # Random cost between 0.001 and 0.05
                "chain_id": chain_id,
                "owner_address": component.get("owner_address", ""),
                "category": self._infer_category(component.get("description", ""))
            }
            services.append(service)
        
        return services
    
    def _infer_category(self, description: str) -> str:
        """Infer a category based on the description."""
        description = description.lower()
        if any(kw in description for kw in ["analysis", "technical", "fundamental", "analytics"]):
            return "Analysis"
        elif any(kw in description for kw in ["predict", "forecast", "prediction"]):
            return "Prediction"
        elif any(kw in description for kw in ["news", "report", "data"]):
            return "Information"
        elif any(kw in description for kw in ["security", "safety", "scan", "vulnerability"]):
            return "Security"
        else:
            return "General"
    
    def submit_request(self, prompt: str, selected_services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Submit a request to the mock mech service.
        
        Args:
            prompt: User's prompt text
            selected_services: List of selected services
            
        Returns:
            Dictionary with transaction ID and request details
        """
        # Generate a unique transaction ID
        tx_hash = f"0x{os.urandom(32).hex()}"
        request_id = f"{int(time.time())}-{random.randint(1000, 9999)}"
        
        # Create mock execution steps based on selected services
        execution_steps = []
        for i, service in enumerate(selected_services):
            execution_steps.append({
                "step": f"Step {i+1}: Processing with {service['name']}",
                "tool": service['name'],
                "status": "pending",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            })
        
        # Add verification step
        execution_steps.append({
            "step": "Final step: Verify results",
            "tool": "Verification Module",
            "status": "pending",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })
        
        # Calculate total cost
        total_cost = sum(float(service.get("cost", 0)) for service in selected_services)
        
        return {
            "transaction_id": tx_hash,
            "request_id": request_id,
            "prompt": prompt,
            "selected_services": selected_services,
            "execution_steps": execution_steps,
            "total_cost": total_cost,
            "status": "submitted",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """
        Get the status of a request.
        
        Args:
            request_id: Request ID to check
            
        Returns:
            Dictionary with request status and details
        """
        # In a real implementation, this would query the blockchain or a database
        # Here we just return a mock status
        statuses = ["pending", "in_progress", "completed", "failed"]
        return {
            "request_id": request_id,
            "status": random.choice(statuses),
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    
    def get_reasoning_feedback(self, prompt: str) -> Dict[str, Any]:
        """
        Generate agent reasoning feedback based on the prompt.
        
        Args:
            prompt: User's prompt text
            
        Returns:
            Dictionary with reasoning steps and recommendations
        """
        # Define reasoning steps based on the reasoning_spec.md
        reasoning_steps = [
            {
                "step": "Identify task type",
                "reasoning": self._generate_task_identification(prompt),
                "status": "completed"
            },
            {
                "step": "Select tools",
                "reasoning": self._generate_tool_selection(prompt),
                "status": "completed"
            },
            {
                "step": "Plan execution",
                "reasoning": self._generate_execution_plan(prompt),
                "status": "completed"
            }
        ]
        
        # Recommend services based on the prompt
        recommended_services = self._recommend_services(prompt)
        
        return {
            "reasoning_steps": reasoning_steps,
            "recommended_services": recommended_services,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    
    def _generate_task_identification(self, prompt: str) -> str:
        """Generate task identification reasoning."""
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ["price", "chart", "market", "trend", "trading"]):
            return "This appears to be a market analysis task. The prompt requests information about market trends, prices, or trading strategies."
        elif any(kw in prompt_lower for kw in ["news", "report", "update", "information"]):
            return "This appears to be an information gathering task. The prompt requests news, reports, or general information."
        elif any(kw in prompt_lower for kw in ["predict", "forecast", "future", "expect"]):
            return "This appears to be a prediction task. The prompt requests forecasts or predictions about future outcomes."
        elif any(kw in prompt_lower for kw in ["analyze", "analysis", "evaluate", "assessment"]):
            return "This appears to be an analysis task. The prompt requests detailed evaluation or assessment of data or conditions."
        else:
            return "This appears to be a general query task. I'll need to select appropriate tools based on the content."
    
    def _generate_tool_selection(self, prompt: str) -> str:
        """Generate tool selection reasoning."""
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ["price", "chart", "market", "trend", "trading"]):
            return "For market analysis, I'll need tools that can access real-time market data, analyze price charts, and identify market trends. The Eolas Technical Analysis Tool would be appropriate."
        elif any(kw in prompt_lower for kw in ["news", "report", "update", "information"]):
            return "For information gathering, I'll need tools that can aggregate news sources, filter relevant information, and present comprehensive reports. News tracking tools would be appropriate."
        elif any(kw in prompt_lower for kw in ["predict", "forecast", "future", "expect"]):
            return "For prediction tasks, I'll need tools that utilize historical data and apply predictive models. The Eolas BTC Price Prediction tool would be appropriate."
        elif any(kw in prompt_lower for kw in ["analyze", "analysis", "evaluate", "assessment"]):
            return "For analysis tasks, I'll need tools that can process large datasets, apply analytical methods, and generate insights. The Eolas Fundamental Analysis Tool would be appropriate."
        else:
            return "For this general query, I'll select a combination of tools that cover various aspects of the request to ensure comprehensive results."
    
    def _generate_execution_plan(self, prompt: str) -> str:
        """Generate execution plan reasoning."""
        steps = [
            "1. Initialize selected tools and prepare input parameters",
            "2. Execute primary data collection from relevant sources",
            "3. Process and analyze collected data",
            "4. Generate insights and recommendations",
            "5. Verify results for accuracy and completeness",
            "6. Format final output for presentation"
        ]
        return "\n".join(steps)
    
    def _recommend_services(self, prompt: str) -> List[Dict[str, Any]]:
        """Recommend services based on the prompt."""
        prompt_lower = prompt.lower()
        all_services = self.get_available_services()
        
        # Filter services based on prompt keywords
        recommended = []
        
        # Category-based matching
        if any(kw in prompt_lower for kw in ["price", "chart", "market", "trend", "trading"]):
            category = "Analysis"
        elif any(kw in prompt_lower for kw in ["news", "report", "update", "information"]):
            category = "Information"
        elif any(kw in prompt_lower for kw in ["predict", "forecast", "future", "expect"]):
            category = "Prediction"
        elif any(kw in prompt_lower for kw in ["security", "safety", "scan", "vulnerability"]):
            category = "Security"
        else:
            category = "General"
        
        # Filter by inferred category
        for service in all_services:
            if service.get("category") == category:
                recommended.append(service)
        
        # If no services match the category, recommend at least 2 random services
        if not recommended and all_services:
            recommended = random.sample(all_services, min(2, len(all_services)))
        
        return recommended
    
    def analyze_query(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze a user query and provide reasoning and recommended services.
        This is an alias for get_reasoning_feedback to maintain API compatibility.
        
        Args:
            prompt: User's prompt text
            
        Returns:
            Dictionary with reasoning steps and recommendations
        """
        # Simply call the existing get_reasoning_feedback method
        return self.get_reasoning_feedback(prompt)
import requests
import json
import time
import random
from typing import Dict, List, Optional, Union, Any

class DefiLlamaAPI:
    """
    Class to handle API calls to DeFi Llama
    Handles parameter inference and API endpoint selection based on the request
    """
    
    BASE_URL = "https://api.llama.fi"
    
    def __init__(self):
        self.session = requests.Session()
        # Add a user agent to avoid being blocked
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 OLAS MCP Integration/1.0",
            "Accept": "application/json"
        })
        # Cache for protocols data
        self.protocols_cache = None
        self.protocols_cache_time = 0
        # Cache expiry in seconds (1 hour)
        self.cache_expiry = 3600
        
        # Load protocols on initialization
        self.all_protocols = self.load_all_protocols()
    
    def load_all_protocols(self) -> List[Dict[str, Any]]:
        """
        Load all protocols from DeFi Llama API
        
        Returns:
            List of protocol dictionaries
        """
        print("Loading all protocols from DeFi Llama...")
        try:
            # Check if we have a valid cache
            current_time = time.time()
            if self.protocols_cache and (current_time - self.protocols_cache_time < self.cache_expiry):
                print("Using cached protocols data")
                return self.protocols_cache
            
            # Make the API call
            url = f"{self.BASE_URL}/protocols"
            response = self.session.get(url)
            response.raise_for_status()
            protocols = response.json()
            
            # Update cache
            self.protocols_cache = protocols
            self.protocols_cache_time = current_time
            
            print(f"Successfully loaded {len(protocols)} protocols")
            return protocols
        except Exception as e:
            print(f"Error loading protocols: {str(e)}")
            # Return empty list on error
            return []
    
    def find_protocol_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a protocol by name or slug
        
        Args:
            name: Protocol name or slug to find
            
        Returns:
            Protocol dictionary if found, None otherwise
        """
        if not self.all_protocols:
            return None
            
        name_lower = name.lower()
        
        # Try exact match first
        for protocol in self.all_protocols:
            if protocol.get("name", "").lower() == name_lower or protocol.get("slug", "").lower() == name_lower:
                return protocol
        
        # Try partial match if exact match failed
        for protocol in self.all_protocols:
            if name_lower in protocol.get("name", "").lower() or name_lower in protocol.get("slug", "").lower():
                return protocol
                
        return None
    
    def get_protocol_tvl(self, protocol_slug: str) -> float:
        """
        Get the current TVL for a protocol
        
        Args:
            protocol_slug: The slug of the protocol
            
        Returns:
            Current TVL value or 0 if not found
        """
        try:
            url = f"{self.BASE_URL}/tvl/{protocol_slug}"
            response = self.session.get(url)
            response.raise_for_status()
            return float(response.json())
        except Exception as e:
            print(f"Error getting TVL for {protocol_slug}: {str(e)}")
            return 0
    
    def infer_parameters(self, query: str) -> Dict[str, Any]:
        """
        Infer API call parameters based on the query
        
        Args:
            query: The user's query from the request form
            
        Returns:
            Dictionary with inferred parameters
        """
        # Default parameters
        params = {
            "endpoints": [],
            "protocols": [],
            "chains": [],
            "tokens": [],
            "timeframe": "7d"  # Default to 7 days
        }
        
        # Infer protocols - check against actual protocol names from the API
        for protocol in self.all_protocols:
            protocol_name = protocol.get("name", "").lower()
            protocol_slug = protocol.get("slug", "").lower()
            
            if protocol_name in query.lower() or protocol_slug in query.lower():
                params["protocols"].append(protocol.get("slug", ""))
        
        # If no protocols were identified by exact match, try common protocols
        if not params["protocols"]:
            common_protocols = ["aave", "compound", "uniswap", "curve", "maker", "sushiswap", "balancer"]
            for protocol_name in common_protocols:
                if protocol_name.lower() in query.lower():
                    # Find the protocol in our loaded protocols
                    found_protocol = self.find_protocol_by_name(protocol_name)
                    if found_protocol:
                        params["protocols"].append(found_protocol.get("slug", protocol_name))
        
        # Infer chains
        common_chains = ["ethereum", "bsc", "polygon", "avalanche", "arbitrum", "optimism", "solana"]
        for chain in common_chains:
            if chain.lower() in query.lower():
                params["chains"].append(chain)
        
        # Infer tokens
        common_tokens = [
            {"symbol": "ETH", "address": "ethereum:0x0000000000000000000000000000000000000000"},
            {"symbol": "WETH", "address": "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
            {"symbol": "USDT", "address": "ethereum:0xdac17f958d2ee523a2206206994597c13d831ec7"},
            {"symbol": "USDC", "address": "ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"},
            {"symbol": "DAI", "address": "ethereum:0x6b175474e89094c44da98b954eedeac495271d0f"}
        ]
        for token in common_tokens:
            if token["symbol"].lower() in query.lower():
                params["tokens"].append(token)
        
        # Infer timeframe
        timeframes = {
            "1d": ["1 day", "24 hours", "today", "24h", "1 day"],
            "7d": ["1 week", "7 days", "weekly", "week", "7d"],
            "30d": ["1 month", "30 days", "monthly", "month", "30d"],
            "1y": ["1 year", "yearly", "year", "365 days", "1y"]
        }
        for tf, terms in timeframes.items():
            for term in terms:
                if term.lower() in query.lower():
                    params["timeframe"] = tf
                    break
        
        # Infer endpoints based on keywords in the query
        endpoint_keywords = {
            "tvl": ["tvl", "total value locked", "value locked", "protocol value"],
            "prices": ["price", "token price", "current price", "how much is", "worth"],
            "protocols": ["protocol", "protocols list", "all protocols", "protocols overview"],
            "chains": ["chain", "chains", "blockchain", "network"],
            "stablecoins": ["stablecoin", "stable", "pegged", "usdt", "usdc", "dai"],
            "bridges": ["bridge", "bridging", "cross-chain", "transfer between"],
            "yields": ["yield", "apy", "interest", "earning", "staking returns"],
            "dexs": ["dex", "swap", "exchange", "amm", "trading", "trading volume"]
        }
        
        for endpoint, keywords in endpoint_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query.lower():
                    if endpoint not in params["endpoints"]:
                        params["endpoints"].append(endpoint)
        
        # If no specific endpoints were identified, select default ones based on the query
        if not params["endpoints"]:
            # Default to most relevant endpoints
            if any(word in query.lower() for word in ["overview", "summary", "market"]):
                params["endpoints"] = ["tvl", "protocols"]
            elif any(word in query.lower() for word in ["yield", "earn"]):
                params["endpoints"] = ["yields"]
            elif any(word in query.lower() for word in ["volume", "trading"]):
                params["endpoints"] = ["dexs"]
            else:
                # If still unclear, choose a basic set of endpoints
                params["endpoints"] = ["tvl", "protocols"]
        
        return params
    
    def get_protocols(self) -> Dict[str, Any]:
        """Get all protocols"""
        try:
            # Use cached data if available
            if self.protocols_cache:
                return {"success": True, "data": self.protocols_cache, "endpoint": "/protocols"}
                
            # Otherwise fetch from API
            url = f"{self.BASE_URL}/protocols"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": "/protocols"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/protocols"}
    
    def get_protocol_details(self, protocol: str) -> Dict[str, Any]:
        """Get details for a specific protocol"""
        try:
            url = f"{self.BASE_URL}/protocol/{protocol}"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": f"/protocol/{protocol}"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": f"/protocol/{protocol}"}
    
    def get_historical_tvl(self) -> Dict[str, Any]:
        """Get historical TVL across all chains"""
        try:
            url = f"{self.BASE_URL}/v2/historicalChainTvl"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": "/v2/historicalChainTvl"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/v2/historicalChainTvl"}
    
    def get_chain_tvl(self, chain: str) -> Dict[str, Any]:
        """Get historical TVL for a specific chain"""
        try:
            url = f"{self.BASE_URL}/v2/historicalChainTvl/{chain}"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": f"/v2/historicalChainTvl/{chain}"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": f"/v2/historicalChainTvl/{chain}"}
    
    def get_chains(self) -> Dict[str, Any]:
        """Get current TVL of all chains"""
        try:
            url = f"{self.BASE_URL}/v2/chains"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": "/v2/chains"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/v2/chains"}
    
    def get_current_prices(self, coins: List[str]) -> Dict[str, Any]:
        """Get current prices of tokens by contract address"""
        try:
            # Join coins into comma-separated string
            coins_str = ",".join(coins)
            url = f"{self.BASE_URL}/prices/current/{coins_str}"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": f"/prices/current/{coins_str}"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": f"/prices/current/..."}
    
    def get_price_chart(self, coins: List[str]) -> Dict[str, Any]:
        """Get token prices at regular time intervals"""
        try:
            # Join coins into comma-separated string
            coins_str = ",".join(coins)
            url = f"{self.BASE_URL}/chart/{coins_str}"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": f"/chart/{coins_str}"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": f"/chart/..."}
    
    def get_stablecoins(self) -> Dict[str, Any]:
        """List all stablecoins along with their circulating amounts"""
        try:
            url = f"{self.BASE_URL}/stablecoins"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": "/stablecoins"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/stablecoins"}
    
    def get_stablecoin_charts(self, chain: Optional[str] = None) -> Dict[str, Any]:
        """Get historical mcap sum of all stablecoins (optionally in a chain)"""
        try:
            if chain:
                url = f"{self.BASE_URL}/stablecoincharts/{chain}"
            else:
                url = f"{self.BASE_URL}/stablecoincharts/all"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": url.replace(self.BASE_URL, "")}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/stablecoincharts/..."}
    
    def get_bridges(self) -> Dict[str, Any]:
        """List all bridges along with summaries of recent bridge volumes"""
        try:
            url = f"{self.BASE_URL}/bridges"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": "/bridges"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/bridges"}
    
    def get_bridge_stats(self, bridge_id: str) -> Dict[str, Any]:
        """Get summary of bridge volume and volume breakdown by chain"""
        try:
            url = f"{self.BASE_URL}/bridge/{bridge_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": f"/bridge/{bridge_id}"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": f"/bridge/{bridge_id}"}
    
    def get_yields(self) -> Dict[str, Any]:
        """Retrieve the latest data for all pools, including enriched information"""
        try:
            url = f"{self.BASE_URL}/pools"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": "/pools"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/pools"}
    
    def get_dexs(self, chain: Optional[str] = None) -> Dict[str, Any]:
        """List all dexs along with summaries of their volumes"""
        try:
            if chain:
                url = f"{self.BASE_URL}/overview/dexs/{chain}"
            else:
                url = f"{self.BASE_URL}/overview/dexs"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": url.replace(self.BASE_URL, "")}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/overview/dexs/..."}
    
    def get_dex_summary(self, protocol: str) -> Dict[str, Any]:
        """Get summary of dex volume with historical data"""
        try:
            url = f"{self.BASE_URL}/summary/dexs/{protocol}"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": f"/summary/dexs/{protocol}"}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": f"/summary/dexs/{protocol}"}
    
    def get_fees(self, chain: Optional[str] = None) -> Dict[str, Any]:
        """List all protocols along with summaries of their fees and revenue"""
        try:
            if chain:
                url = f"{self.BASE_URL}/overview/fees/{chain}"
            else:
                url = f"{self.BASE_URL}/overview/fees"
            response = self.session.get(url)
            response.raise_for_status()
            return {"success": True, "data": response.json(), "endpoint": url.replace(self.BASE_URL, "")}
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": "/overview/fees/..."}
    
    def process_query(self, query: str, service_id: str) -> Dict[str, Any]:
        """
        Process a user query and return relevant DeFi Llama data
        
        Args:
            query: The user's query from the request form
            service_id: The ID of the service making the request
            
        Returns:
            Dictionary with API call results and metadata
        """
        # Infer parameters from the query
        params = self.infer_parameters(query)
        
        # Initialize results with steps for stepwise processing
        results = {
            "query": query,
            "service_id": service_id,
            "timestamp": time.time(),
            "params": params,
            "api_calls": [],
            "summary": "",
            "aggregated_data": {},
            "processing_steps": [
                {"step": "Query Analysis", "status": "complete", "detail": f"Analyzed query: {query}"},
                {"step": "Parameter Inference", "status": "complete", "detail": f"Inferred parameters for API calls"},
                {"step": "API Execution", "status": "pending", "detail": "Executing API calls..."},
                {"step": "Data Aggregation", "status": "pending", "detail": "Aggregating data..."},
                {"step": "Result Generation", "status": "pending", "detail": "Generating results..."}
            ]
        }
        
        # Add inferred parameters to the results
        step_details = []
        if params["protocols"]:
            step_details.append(f"Protocols: {', '.join(params['protocols'])}")
        if params["chains"]:
            step_details.append(f"Chains: {', '.join(params['chains'])}")
        if params["tokens"]:
            step_details.append(f"Tokens: {', '.join([t['symbol'] for t in params['tokens']])}")
        if params["endpoints"]:
            step_details.append(f"Endpoints: {', '.join(params['endpoints'])}")
            
        results["processing_steps"][1]["detail"] = f"Parameters: {'; '.join(step_details)}"
        
        # Execute relevant API calls based on inferred endpoints
        api_call_results = []
        for endpoint in params["endpoints"]:
            api_result = None
            
            if endpoint == "tvl":
                # Get TVL data
                if params["protocols"] and len(params["protocols"]) == 1:
                    # If a specific protocol is mentioned, get its details
                    api_result = self.get_protocol_details(params["protocols"][0])
                    api_call_results.append(f"Retrieved TVL data for {params['protocols'][0]}")
                else:
                    # Otherwise, get all protocols
                    api_result = self.get_protocols()
                    api_call_results.append("Retrieved TVL data for all protocols")
                
            elif endpoint == "prices":
                # Get price data
                if params["tokens"]:
                    # If specific tokens are mentioned, get their prices
                    token_addresses = [token["address"] for token in params["tokens"]]
                    api_result = self.get_current_prices(token_addresses)
                    api_call_results.append(f"Retrieved price data for {len(token_addresses)} tokens")
                else:
                    # Otherwise, use default tokens
                    default_addresses = [
                        "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
                        "ethereum:0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
                        "ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"   # USDC
                    ]
                    api_result = self.get_current_prices(default_addresses)
                    api_call_results.append("Retrieved price data for default tokens (WETH, DAI, USDC)")
            
            elif endpoint == "protocols":
                # Get all protocols
                api_result = self.get_protocols()
                api_call_results.append("Retrieved all protocol data")
            
            elif endpoint == "chains":
                # Get chain data
                if params["chains"] and len(params["chains"]) == 1:
                    # If a specific chain is mentioned, get its TVL
                    api_result = self.get_chain_tvl(params["chains"][0])
                    api_call_results.append(f"Retrieved TVL data for {params['chains'][0]} chain")
                else:
                    # Otherwise, get all chains
                    api_result = self.get_chains()
                    api_call_results.append("Retrieved TVL data for all chains")
            
            elif endpoint == "stablecoins":
                # Get stablecoin data
                api_result = self.get_stablecoins()
                api_call_results.append("Retrieved stablecoin circulation data")
            
            elif endpoint == "bridges":
                # Get bridge data
                api_result = self.get_bridges()
                api_call_results.append("Retrieved bridge volume data")
            
            elif endpoint == "yields":
                # Get yield data
                api_result = self.get_yields()
                api_call_results.append("Retrieved yield pool data")
            
            elif endpoint == "dexs":
                # Get DEX volume data
                if params["chains"] and len(params["chains"]) == 1:
                    # If a specific chain is mentioned, get DEXs for that chain
                    api_result = self.get_dexs(params["chains"][0])
                    api_call_results.append(f"Retrieved DEX volume data for {params['chains'][0]} chain")
                else:
                    # Otherwise, get all DEXs
                    api_result = self.get_dexs()
                    api_call_results.append("Retrieved DEX volume data for all chains")
                
            # Add the API call result to our list
            if api_result:
                results["api_calls"].append(api_result)
        
        # Update API execution step
        if api_call_results:
            results["processing_steps"][2]["status"] = "complete"
            results["processing_steps"][2]["detail"] = ", ".join(api_call_results)
        else:
            results["processing_steps"][2]["status"] = "error"
            results["processing_steps"][2]["detail"] = "No API calls were executed"
        
        # Generate a summary based on the API calls
        if results["api_calls"]:
            # Extract successful API calls
            successful_calls = [call for call in results["api_calls"] if call.get("success", False)]
            
            if successful_calls:
                endpoints_summary = ", ".join([call["endpoint"].split("/")[1].capitalize() 
                                              for call in successful_calls])
                results["summary"] = f"Retrieved data from {len(successful_calls)} DeFi Llama endpoints: {endpoints_summary}"
                
                # Aggregate relevant data
                aggregated_data = {}
                aggregation_details = []
                
                # Extract TVL information if available
                tvl_calls = [call for call in successful_calls if "/protocol" in call["endpoint"] or "/protocols" in call["endpoint"]]
                if tvl_calls:
                    tvl_data = tvl_calls[0]["data"]
                    if "protocols" in tvl_data:
                        # Sort protocols by TVL
                        sorted_protocols = sorted(tvl_data["protocols"], key=lambda x: x.get("tvl", 0), reverse=True)
                        top_protocols = sorted_protocols[:5]  # Get top 5
                        aggregated_data["top_protocols"] = top_protocols
                        
                        # Calculate total TVL
                        total_tvl = sum(p.get("tvl", 0) for p in tvl_data["protocols"])
                        aggregated_data["total_tvl"] = total_tvl
                        
                        aggregation_details.append(f"Identified top {len(top_protocols)} protocols by TVL")
                
                # Extract price information if available
                price_calls = [call for call in successful_calls if "/price" in call["endpoint"] or "/chart" in call["endpoint"]]
                if price_calls:
                    price_data = price_calls[0]["data"]
                    if "coins" in price_data:
                        aggregated_data["token_prices"] = price_data["coins"]
                        aggregation_details.append(f"Aggregated price data for {len(price_data['coins'])} tokens")
                
                # Extract yield information if available
                yield_calls = [call for call in successful_calls if "/pools" in call["endpoint"]]
                if yield_calls:
                    yield_data = yield_calls[0]["data"]
                    if "data" in yield_data:
                        # Sort pools by APY
                        sorted_pools = sorted(yield_data["data"], key=lambda x: x.get("apy", 0), reverse=True)
                        top_pools = sorted_pools[:5]  # Get top 5
                        aggregated_data["top_yield_pools"] = top_pools
                        aggregation_details.append(f"Identified top {len(top_pools)} yield pools by APY")
                
                # Extract DEX volume information if available
                dex_calls = [call for call in successful_calls if "/dexs" in call["endpoint"]]
                if dex_calls:
                    dex_data = dex_calls[0]["data"]
                    if "dexs" in dex_data:
                        # Sort DEXs by volume
                        sorted_dexs = sorted(dex_data["dexs"], key=lambda x: x.get("totalVolume", 0), reverse=True)
                        top_dexs = sorted_dexs[:5]  # Get top 5
                        aggregated_data["top_dexs"] = top_dexs
                        aggregation_details.append(f"Identified top {len(top_dexs)} DEXs by volume")
                
                results["aggregated_data"] = aggregated_data
                
                # Update data aggregation step
                if aggregation_details:
                    results["processing_steps"][3]["status"] = "complete"
                    results["processing_steps"][3]["detail"] = "; ".join(aggregation_details)
                else:
                    results["processing_steps"][3]["status"] = "warning"
                    results["processing_steps"][3]["detail"] = "No data could be aggregated from API calls"
                
                # Update result generation step
                results["processing_steps"][4]["status"] = "complete"
                results["processing_steps"][4]["detail"] = f"Generated summary: {results['summary']}"
            else:
                results["summary"] = "No successful API calls were made to DeFi Llama"
                results["processing_steps"][3]["status"] = "error"
                results["processing_steps"][3]["detail"] = "No successful API calls to aggregate data from"
                results["processing_steps"][4]["status"] = "error"
                results["processing_steps"][4]["detail"] = "Could not generate meaningful results"
        else:
            results["summary"] = "No relevant DeFi Llama endpoints were identified for this query"
            results["processing_steps"][3]["status"] = "error"
            results["processing_steps"][3]["detail"] = "No API call results to aggregate"
            results["processing_steps"][4]["status"] = "error"
            results["processing_steps"][4]["detail"] = "Could not generate meaningful results"
        
        return results

# Example usage:
# defillama_api = DefiLlamaAPI()
# results = defillama_api.process_query("What's the TVL of Uniswap?", "1722")
# print(results) 
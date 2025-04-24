import os
import json
import logging
import asyncio
import time  # Add time for easier time-based operations
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Callable
from hexbytes import HexBytes
import pkg_resources
from datetime import datetime

from web3 import Web3
from web3.types import RPCEndpoint, RPCResponse
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Import our transaction storage utility
import utils.transaction_storage as transaction_storage

# Detect web3.py version to handle middleware compatibility
WEB3_VERSION = pkg_resources.get_distribution("web3").version
WEB3_MAJOR_VERSION = int(WEB3_VERSION.split('.')[0])

# Define POA middleware based on web3 version
if WEB3_MAJOR_VERSION >= 7:
    # Web3 v7+ uses class-based middleware
    from web3.middleware import Web3Middleware
    
    class ExtraDataToPOAMiddleware(Web3Middleware):
        """
        Middleware for handling Proof of Authority (PoA) chain responses.
        This middleware modifies the 'extraData' field in blocks to conform to
        standard Ethereum requirements, as POA chains like Gnosis or geth --dev
        use more than the allowed 32 bytes in the extraData field.
        """

        def response_processor(self, method: RPCEndpoint, response: RPCResponse) -> RPCResponse:
            """Process responses for Proof of Authority chains."""
            if not isinstance(response, dict):
                return response

            # Handle both block responses and responses that contain blocks
            if method in ("eth_getBlockByHash", "eth_getBlockByNumber"):
                if "result" in response and response["result"] and isinstance(response["result"], dict):
                    self._modify_extradata(response["result"])
                    
            elif method == "eth_getUncleByBlockHashAndIndex" or method == "eth_getUncleByBlockNumberAndIndex":
                if "result" in response and response["result"] and isinstance(response["result"], dict):
                    self._modify_extradata(response["result"])
                    
            elif method == "eth_getBlockReceipts":
                if "result" in response and isinstance(response["result"], list):
                    for receipt in response["result"]:
                        if "blockHash" in receipt and isinstance(receipt, dict):
                            self._modify_extradata(receipt)
                            
            # Handle eth_getLogs responses
            elif method == "eth_getLogs":
                if "result" in response and isinstance(response["result"], list):
                    for log in response["result"]:
                        if "blockHash" in log and isinstance(log, dict):
                            self._modify_extradata(log)

            return response
        
        async def async_response_processor(self, method: RPCEndpoint, response: RPCResponse) -> RPCResponse:
            """Async version of the response processor for Proof of Authority chains."""
            return self.response_processor(method, response)
        
        def _modify_extradata(self, block_dict: Dict[str, Any]) -> None:
            """
            Modifies the extraData field in a block to ensure it conforms to standards.
            POA chains use extraData for consensus information which can exceed the
            standard 32-byte limit defined in the Yellow Paper.
            """
            if "extraData" in block_dict and isinstance(block_dict["extraData"], (str, HexBytes)):
                extra_data = block_dict["extraData"]
                if isinstance(extra_data, str):
                    # Truncate to 32 bytes (64 hex chars + '0x' prefix)
                    if len(extra_data) > 66:  # 0x + 64 hex chars
                        # Keep only the first 32 bytes
                        block_dict["extraData"] = extra_data[:66]
                elif isinstance(extra_data, HexBytes):
                    # Truncate HexBytes to 32 bytes
                    if len(extra_data) > 32:
                        block_dict["extraData"] = HexBytes(extra_data[:32])
else:
    # For Web3 v6.x (function-based middleware)
    try:
        from web3.middleware import geth_poa_middleware as ExtraDataToPOAMiddleware
    except ImportError:
        # As a fallback, create a simple implementation of the middleware
        def ExtraDataToPOAMiddleware(make_request, web3):
            def middleware(method, params):
                response = make_request(method, params)
                
                if method in ("eth_getBlockByHash", "eth_getBlockByNumber"):
                    if response.get("result") and isinstance(response["result"], dict):
                        _modify_extradata_v6(response["result"])
                        
                return response
            
            return middleware
        
        def _modify_extradata_v6(block_dict):
            if "extraData" in block_dict and isinstance(block_dict["extraData"], (str, HexBytes)):
                extra_data = block_dict["extraData"]
                if isinstance(extra_data, str):
                    if len(extra_data) > 66:  
                        block_dict["extraData"] = extra_data[:66]
                elif isinstance(extra_data, HexBytes):
                    if len(extra_data) > 32:
                        block_dict["extraData"] = HexBytes(extra_data[:32])

# Import Safe-related packages (safe-eth-py)
try:
    from safe_eth.eth import Safe
    from safe_eth.safe import SafeTx
    from safe_eth.eth import EthereumClient
except ImportError:
    logging.warning("Could not import safe-eth-py. Using mock Safe implementation.")
    # Mock classes if import fails
    class SafeTx:
        def __init__(self, *args, **kwargs): pass
    
    class Safe:
        def __init__(self, address, ethereum_client): 
            self.address = address
            self.ethereum_client = ethereum_client
        
        @classmethod
        async def create(cls, ethereum_client, deployer_account, owners, threshold):
            """Mock Safe creation that returns an awaitable"""
            mock_address = "0xMockSafeAddress"
            logging.info(f"Creating mock Safe at address {mock_address}")
            return cls(mock_address, ethereum_client)
            
        async def build_multisig_tx(self, to, value, data, operation, safe_tx_gas, base_gas, gas_price, 
                                  gas_token, refund_receiver, nonce):
            """Mock build_multisig_tx method that returns an awaitable"""
            mock_tx = SafeTx(None, self.address, to, value, data, operation)
            return mock_tx
            
        async def sign_transaction(self, safe_tx, signer):
            """Mock sign_transaction method that returns an awaitable"""
            return safe_tx
            
        async def execute_transaction(self, safe_tx, signer):
            """Mock execute_transaction method that returns an awaitable"""
            mock_tx_hash = "0x" + os.urandom(32).hex()
            logging.info(f"Mock Safe transaction executed with hash: {mock_tx_hash}")
            return mock_tx_hash
            
        async def retrieve_nonce(self):
            """Mock retrieve_nonce method that returns an awaitable"""
            return 0
    
    class EthereumClient:
        def __init__(self, web3_instance): 
            self.w3 = web3_instance

# Import MCP-related packages (mcp-python-sdk) with a compatibility layer
try:
    from mcp import Client as MCPClient
    from mcp.types import Result, ToolCall, ResourceReadRequest
except ImportError:
    logging.warning("Could not import mcp-python-sdk. Using mock MCP implementation.")
    # Mock classes if import fails
    class MCPClient:
        def __init__(self, base_url=None): 
            self.base_url = base_url or "http://localhost:8000"
            
        async def tools_list(self):
            return [
                {"name": "DeFiLlamaAPI", "cost": "0.01 xDAI", "available": True, "description": "Access to real-time lending rates and TVL data"},
                {"name": "TheGraphQuery", "cost": "0.02 xDAI", "available": True, "description": "Historical lending data and protocol metrics"},
                {"name": "SpaceAndTimeDB", "cost": "0.015 xDAI", "available": True, "description": "Advanced quant analysis and risk assessment"},
                {"name": "ChainlinkOracle", "cost": "0.03 xDAI", "available": False, "description": "Price feed data for token valuation"}
            ]
        
        async def tools_call(self, name, arguments):
            await asyncio.sleep(1)  # Simulate processing delay
            if name == "DeFiLendingStrategy":
                return {
                    "content": [{"type": "text", "text": "Best lending strategy: Aave, 5% APY"}],
                    "isError": False
                }
            return {
                "content": [{"type": "text", "text": f"Tool {name} executed with {arguments}"}],
                "isError": False
            }
    
    class Result:
        pass
    
    class ToolCall:
        pass
    
    class ResourceReadRequest:
        pass

# Import OLAS/Mech-related packages (mech-client) with a compatibility layer
try:
    # Try to import from the mech-client package
    from mech_client import ConfirmationType
    from mech_client.mech_tool_management import get_tools_for_agents, get_tool_description, get_tool_io_schema
except ImportError:
    logging.warning("Could not import mech-client. Using mock Mech implementation.")
    # Mock implementation of Mech classes
    class ConfirmationType:
        ON_CHAIN = "on-chain"
        OFF_CHAIN = "off-chain"
    
    def interact(prompt, agent_id, tool, chain_config, confirmation_type, private_key_path=None):
        # Mock implementation
        mock_tx_hash = "0x" + os.urandom(32).hex()
        mock_request_id = "0x" + os.urandom(32).hex()
        return {
            "requestId": mock_request_id,
            "result": f"Mock result for {prompt} using {tool}",
            "prompt": prompt,
            "cost_dict": {},
            "metadata": {"model": None, "tool": tool}
        }
        
    def get_tools_for_agents(agent_id=None, chain_config=None):
        # Mock implementation
        return [
            {"name": "DeFiLlamaAPI", "cost": "0.01 xDAI", "available": True, "description": "Access to real-time lending rates and TVL data"},
            {"name": "TheGraphQuery", "cost": "0.02 xDAI", "available": True, "description": "Historical lending data and protocol metrics"},
            {"name": "SpaceAndTimeDB", "cost": "0.015 xDAI", "available": True, "description": "Advanced quant analysis and risk assessment"},
            {"name": "ChainlinkOracle", "cost": "0.03 xDAI", "available": False, "description": "Price feed data for token valuation"}
        ]
    
    def get_tool_description(tool_id, chain_config=None):
        return "Mock tool description"
    
    def get_tool_io_schema(tool_id, chain_config=None):
        return {"input": {}, "output": {}}

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)

ETHEREUM_PRIVATE_KEY = os.getenv("ETHEREUM_PRIVATE_KEY")
if not ETHEREUM_PRIVATE_KEY:
    raise ValueError("ETHEREUM_PRIVATE_KEY not found in .env file")

# --- Configuration ---
DEFAULT_RPC_URL = "https://rpc.gnosischain.com"
DEFAULT_MARKETPLACE_ADDRESS = "0x4554fE75c1f5576c1d7F765B2A036c199Adae329" # Gnosis Chain
DEFAULT_CHAIN_ID = 100
DEFAULT_SAFE_ADDRESS = os.getenv("DEFAULT_SAFE_ADDRESS") # User needs to provide their Safe address
DEFAULT_SLASHING_CONTRACT_ADDRESS = os.getenv("SLASHING_CONTRACT_ADDRESS") # Needs to be deployed
DEFAULT_MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

# --- Global Clients (Initialize once) ---
_web3_instances = {}
_accounts = {}
_ethereum_clients = {}
_safe_instances = {}

def get_web3(rpc_url: str = DEFAULT_RPC_URL, chain_id: int = DEFAULT_CHAIN_ID) -> Web3:
    """Initializes and returns a Web3 instance."""
    if rpc_url not in _web3_instances:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Inject middleware for PoA chains like Gnosis
        if chain_id in [100]:  # Gnosis Chain ID
            if WEB3_MAJOR_VERSION >= 7:
                # Web3 v7+ uses class-based middleware with inject method
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            else:
                # Web3 v6.x uses function-based middleware with add method
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to Web3 provider at {rpc_url}")
        
        _web3_instances[rpc_url] = w3
        logging.info(f"Web3 connected to {rpc_url}")
    
    return _web3_instances[rpc_url]

def get_account() -> LocalAccount:
    """Gets the local account from the private key."""
    if "default" not in _accounts:
        try:
            account: LocalAccount = Account.from_key(ETHEREUM_PRIVATE_KEY)
            _accounts["default"] = account
            logging.info(f"Account loaded: {account.address}")
        except Exception as e:
            logging.error(f"Failed to load account from private key: {e}")
            raise ValueError("Invalid private key")
    return _accounts["default"]

def get_ethereum_client(rpc_url: str = DEFAULT_RPC_URL, chain_id: int = DEFAULT_CHAIN_ID) -> EthereumClient:
    """Returns an Ethereum client for Safe operations."""
    key = (rpc_url, chain_id)
    if key not in _ethereum_clients:
        w3 = get_web3(rpc_url, chain_id)
        _ethereum_clients[key] = EthereumClient(w3)
        logging.info(f"Ethereum client initialized for RPC: {rpc_url}")
    return _ethereum_clients[key]

async def get_safe_instance(safe_address: str, 
                     rpc_url: str = DEFAULT_RPC_URL, 
                     chain_id: int = DEFAULT_CHAIN_ID) -> Optional[Safe]:
    """Initializes and returns a Safe instance asynchronously."""
    if not safe_address:
        logging.warning("No Safe address provided. Cannot initialize Safe instance.")
        return None
    
    key = (safe_address, rpc_url)
    if key not in _safe_instances:
        ethereum_client = get_ethereum_client(rpc_url, chain_id)
        try:
            # Load an existing Safe (this works with both real implementation and our mock)
            _safe_instances[key] = Safe(safe_address, ethereum_client)
            logging.info(f"Safe instance loaded for address: {safe_address}")
        except Exception as e:
            logging.error(f"Failed to initialize Safe instance: {e}")
            return None
    return _safe_instances[key]

# --- API Functions ---

def get_account_from_address(address: str):
    """
    Create an Account object for a given address.
    This is used when authenticating via Privy where we get the address directly.
    
    Args:
        address: Ethereum address
        
    Returns:
        LocalAccount object with the address (will be read-only unless private key is in .env)
    """
    # Try to match with local private key
    if ETHEREUM_PRIVATE_KEY and address.lower() == get_account().address.lower():
        return get_account()
    
    # Otherwise create a read-only account
    from eth_account.account import Account
    account = Account.create()  # Create a temporary account
    account.address = address  # Override the address with the one from Privy
    return account

async def check_safe_address_for_account(account):
    """
    Check if a Safe account is associated with this address.
    This is similar to onboard_safe_account but just checks without creating.
    
    Args:
        account: The account to check
        
    Returns:
        Safe address if exists, None otherwise
    """
    try:
        # Check if there's a SAFE_ADDRESS in the environment
        safe_address = os.getenv("SAFE_ADDRESS")
        if safe_address:
            # Validate the safe address exists and is accessible
            return safe_address
        return None
    except Exception as e:
        logging.error(f"Error checking safe address: {e}")
        return None

async def onboard_safe_account(owners: Optional[List[str]] = None, 
                            threshold: int = 1):
    """
    Onboard a user with a Safe account.
    If DEFAULT_SAFE_ADDRESS is set, use that.
    Otherwise, deploy a new Safe with the provided owners and threshold.
    Returns the Safe address.
    """
    logging.info("Checking Safe configuration...")
    
    if DEFAULT_SAFE_ADDRESS:
        logging.info(f"Using pre-configured Safe Address: {DEFAULT_SAFE_ADDRESS}")
        # Verify the Safe exists
        try:
            ethereum_client = get_ethereum_client()
            safe = Safe(DEFAULT_SAFE_ADDRESS, ethereum_client)
            return DEFAULT_SAFE_ADDRESS
        except Exception as e:
            logging.warning(f"Pre-configured Safe address {DEFAULT_SAFE_ADDRESS} could not be loaded: {e}")
    
    # No valid Safe found, check if we should create a new one
    if owners:
        logging.info(f"Creating new Safe with owners: {owners} and threshold: {threshold}")
        try:
            ethereum_client = get_ethereum_client()
            account = get_account()
            
            # Deploy a new Safe - this should work with both real and mock implementations
            safe = await Safe.create(ethereum_client, account, owners, threshold)
            logging.info(f"New Safe deployed at: {safe.address}")
            return safe.address
        except Exception as e:
            logging.error(f"Failed to deploy new Safe: {e}")
            raise
            
    logging.warning("No Safe address configured and no owners provided for new Safe deployment.")
    return None

async def list_available_tools() -> List[Dict[str, Any]]:
    """Lists available tools using the mech_client."""
    try:
        # Use mech_client's get_tools_for_agents function
        tools = get_tools_for_agents(chain_config="gnosis")  # Default to Gnosis chain
        logging.info(f"Fetched {len(tools)} available tools")
        
        # Ensure each tool has a description
        for tool in tools:
            if "description" not in tool or not tool["description"]:
                tool["description"] = get_tool_description(tool.get("name"), chain_config="gnosis")
        
        return tools
    except Exception as e:
        logging.error(f"Error listing tools: {e}")
        return []

async def execute_payment(total_cost_xdai: float, 
                       selected_tools: List[str], 
                       chain_config: Dict, 
                       account: LocalAccount, 
                       safe_address: Optional[str] = None,
                       transaction_id: Optional[str] = None) -> str:
    """
    Executes the payment for the selected tools.
    Uses Safe account if provided, otherwise EOA.
    Returns transaction hash.
    
    If transaction_id is provided, updates the transaction state.
    """
    # For better simulation, convert the total cost to wei to follow web3 conventions
    total_cost_wei = Web3.to_wei(total_cost_xdai, 'ether')  # Assume xDAI works similar to ETH
    
    # Generate a mock transaction hash
    mock_tx_hash = "0x" + os.urandom(32).hex()
    
    logging.info(f"Processing payment of {total_cost_xdai} xDAI for tools: {', '.join(selected_tools)}")
    
    # Update transaction state if transaction_id is provided
    if transaction_id:
        transaction_storage.update_transaction_state(
            tx_id=transaction_id,
            state_name="payment",
            status="in_progress",
            details={"amount": total_cost_xdai, "tools": selected_tools}
        )
    
    # Simulate a brief delay to make the state changes visible
    await asyncio.sleep(1.5)
    
    try:
        if safe_address:
            logging.info(f"Executing payment via Safe at {safe_address}")
            
            # In a real implementation, this would use the safe-eth-py lib to:
            # 1. Get the Safe instance
            # 2. Build a multisig transaction for the payment
            # 3. Sign and execute the transaction
            ethereum_client = get_ethereum_client(chain_config.get("rpcUrl", DEFAULT_RPC_URL))
            safe = await get_safe_instance(safe_address)
            
            # Mock successful Safe transaction
            if transaction_id:
                transaction_storage.update_transaction_state(
                    tx_id=transaction_id,
                    state_name="payment",
                    status="completed",
                    details={
                        "tx_hash": mock_tx_hash,
                        "amount": total_cost_xdai,
                        "method": "safe",
                        "safe_address": safe_address
                    }
                )
                transaction_storage.update_transaction_details(
                    tx_id=transaction_id,
                    payment_tx_hash=mock_tx_hash
                )
        else:
            logging.info(f"Executing payment via EOA {account.address}")
            
            # In a real implementation, this would:
            # 1. Build an Ethereum transaction
            # 2. Sign with the account's private key
            # 3. Broadcast to the network
            w3 = get_web3(chain_config.get("rpcUrl", DEFAULT_RPC_URL))
            
            # Mock successful EOA transaction
            if transaction_id:
                transaction_storage.update_transaction_state(
                    tx_id=transaction_id,
                    state_name="payment",
                    status="completed",
                    details={
                        "tx_hash": mock_tx_hash,
                        "amount": total_cost_xdai,
                        "method": "eoa",
                        "from_address": account.address
                    }
                )
                transaction_storage.update_transaction_details(
                    tx_id=transaction_id,
                    payment_tx_hash=mock_tx_hash
                )
        
        logging.info(f"Payment successful! Transaction hash: {mock_tx_hash}")
        return mock_tx_hash
        
    except Exception as e:
        logging.error(f"Payment failed: {e}")
        if transaction_id:
            transaction_storage.update_transaction_state(
                tx_id=transaction_id,
                state_name="payment",
                status="failed",
                details={"error": str(e)}
            )
        raise e

async def submit_mech_request(agent_id: int, 
                           tool_name: str, 
                           prompt: str, 
                           chain_config: Dict, 
                           account: LocalAccount,
                           transaction_id: Optional[str] = None) -> str:
    """
    Creates and submits the request to the Mech using mech_client.
    Returns transaction hash.
    
    If transaction_id is provided, updates the transaction state.
    """
    # Generate a mock transaction hash for the request
    mock_tx_hash = "0x" + os.urandom(32).hex()
    
    # Update transaction state if transaction_id is provided
    if transaction_id:
        transaction_storage.update_transaction_state(
            tx_id=transaction_id,
            state_name="request",
            status="in_progress",
            details={"agent_id": agent_id, "tool": tool_name, "prompt": prompt}
        )
    
    logging.info(f"Submitting request for {tool_name} with prompt: {prompt[:50]}...")
    
    # Simulate a brief delay to make the state changes visible
    await asyncio.sleep(1.5)
    
    try:
        # In a real implementation, this would:
        # 1. Use mech_client to submit the request
        # 2. Handle response, confirmations, etc.
        
        # Mock successful request submission
        logging.info(f"Request submitted. Transaction hash: {mock_tx_hash}")
        
        if transaction_id:
            transaction_storage.update_transaction_state(
                tx_id=transaction_id,
                state_name="request",
                status="completed",
                details={"tx_hash": mock_tx_hash}
            )
            transaction_storage.update_transaction_details(
                tx_id=transaction_id,
                request_tx_hash=mock_tx_hash
            )
        
        return mock_tx_hash
        
    except Exception as e:
        logging.error(f"Request submission failed: {e}")
        if transaction_id:
            transaction_storage.update_transaction_state(
                tx_id=transaction_id,
                state_name="request",
                status="failed",
                details={"error": str(e)}
            )
        raise e

async def start_mech_execution(request_tx_hash: str, 
                            payment_tx_hash: str, 
                            selected_tools_names: List[str], 
                            execution_steps: List[Dict], 
                            chain_config: Dict, 
                            account: LocalAccount,
                            transaction_id: Optional[str] = None) -> Dict[str, str]:
    """
    Initiates execution using mech_client.
    Returns request ID and assigned operator.
    
    If transaction_id is provided, updates the transaction state.
    """
    # Generate mock request ID and operator address
    mock_request_id = "0x" + os.urandom(32).hex()
    mock_operator = "0x" + os.urandom(20).hex()
    
    # Update transaction state if transaction_id is provided
    if transaction_id:
        transaction_storage.update_transaction_state(
            tx_id=transaction_id,
            state_name="execution",
            status="in_progress",
            details={
                "request_tx_hash": request_tx_hash,
                "payment_tx_hash": payment_tx_hash,
                "selected_tools": selected_tools_names
            }
        )
        
        # Add execution steps to the transaction
        from models.models import ExecutionStep
        exec_steps = [ExecutionStep(**step) for step in execution_steps]
        transaction_storage.update_transaction_details(
            tx_id=transaction_id,
            execution_steps=exec_steps
        )
    
    logging.info(f"Starting execution for request: {request_tx_hash}")
    
    # Simulate a brief delay to make the state changes visible
    await asyncio.sleep(1.5)
    
    try:
        # In a real implementation, this would:
        # 1. Use mech_client to start the execution
        # 2. Get assigned operator(s)
        # 3. Handle response and confirmations
        
        execution_info = {
            "requestId": mock_request_id,
            "operator": mock_operator
        }
        
        logging.info(f"Execution started. Request ID: {mock_request_id}, Operator: {mock_operator}")
        
        if transaction_id:
            # Update transaction with execution info
            transaction_storage.update_transaction_details(
                tx_id=transaction_id,
                execution_info=execution_info
            )
        
        return execution_info
        
    except Exception as e:
        logging.error(f"Execution start failed: {e}")
        if transaction_id:
            transaction_storage.update_transaction_state(
                tx_id=transaction_id,
                state_name="execution",
                status="failed",
                details={"error": str(e)}
            )
        raise e

# Store the call count at the module level
_status_call_counts = {}

async def get_execution_status_and_result(request_id: str, 
                                      chain_config: Dict,
                                      account: LocalAccount,
                                      transaction_id: Optional[str] = None) -> Dict:
    """
    Checks the execution status and retrieves results using mech_client.
    Returns dict with status and result (if completed).
    
    If transaction_id is provided, updates the transaction state.
    """
    # Track call count per request ID for status progression
    if request_id not in _status_call_counts:
        _status_call_counts[request_id] = 0
    
    _status_call_counts[request_id] += 1
    call_count = _status_call_counts[request_id]
    
    # Simulate a progressive status based on how many times the function has been called
    if call_count == 1:
        status = "Processing"
        result = {
            "partial": True,
            "content": {"message": "Starting to process data..."}
        }
        
        # Update execution step status
        if transaction_id:
            # In a real implementation we'd update the correct step based on the actual processing
            # For demo, just update the first step to in_progress
            transaction_storage.update_execution_step(
                tx_id=transaction_id,
                step_index=0,
                status="in_progress"
            )
    
    elif call_count == 2:
        status = "Analyzing Markets"
        result = {
            "partial": True,
            "content": {"message": "Analyzing lending markets across platforms..."}
        }
        
        # Update execution step status
        if transaction_id:
            # Complete first step and start second step
            try:
                transaction_storage.update_execution_step(
                    tx_id=transaction_id,
                    step_index=0,
                    status="completed"
                )
                transaction_storage.update_execution_step(
                    tx_id=transaction_id,
                    step_index=1,
                    status="in_progress"
                )
            except Exception as e:
                logging.warning(f"Could not update execution steps: {e}")
    
    elif call_count == 3:
        status = "Comparing Rates"
        result = {
            "partial": True,
            "content": {"message": "Comparing APY rates and risk metrics..."}
        }
        
        # Update execution step status
        if transaction_id:
            # Complete second step and start third step
            try:
                transaction_storage.update_execution_step(
                    tx_id=transaction_id,
                    step_index=1,
                    status="completed"
                )
                transaction_storage.update_execution_step(
                    tx_id=transaction_id,
                    step_index=2,
                    status="in_progress"
                )
            except Exception as e:
                logging.warning(f"Could not update execution steps: {e}")
    
    else:
        status = "Completed"
        result = {
            "partial": False,
            "content": [{"type": "text", "text": "Best lending strategy found: Aave on Ethereum, with 4.5% APY for USDC deposits. Lower risk profile than alternatives and higher liquidity."}]
        }
        
        # Update execution step status and overall execution state
        if transaction_id:
            try:
                # Complete all remaining steps
                tx = transaction_storage.get_transaction(transaction_id)
                if tx:
                    for i, step in enumerate(tx.execution_steps):
                        if step.status != "completed":
                            transaction_storage.update_execution_step(
                                tx_id=transaction_id,
                                step_index=i,
                                status="completed"
                            )
                
                # Update execution state to completed
                transaction_storage.update_transaction_state(
                    tx_id=transaction_id,
                    state_name="execution",
                    status="completed",
                    details={"final_status": status}
                )
            except Exception as e:
                logging.warning(f"Could not update execution status: {e}")
    
    logging.info(f"Execution status for request {request_id}: {status}")
    
    # Simulate a brief delay to make the state changes visible
    await asyncio.sleep(0.5)
    
    return {
        "status": status,
        "result": result
    }

async def verify_and_process_results(request_id: str, 
                                  operators: List[str], 
                                  chain_config: Dict, 
                                  account: LocalAccount,
                                  transaction_id: Optional[str] = None):
    """
    Verifies results using mech_client.
    Returns the final (verified) result.
    
    If transaction_id is provided, updates the transaction state.
    """
    # Update transaction state if transaction_id is provided
    if transaction_id:
        transaction_storage.update_transaction_state(
            tx_id=transaction_id,
            state_name="verification",
            status="in_progress",
            details={"request_id": request_id, "operators": operators}
        )
    
    logging.info(f"Verifying results for request {request_id} from {len(operators)} operators")
    
    # Reset the status counter for demo purposes
    if request_id in _status_call_counts:
        _status_call_counts[request_id] = 4  # Ensure we get the "Completed" status
    
    # Get the final result from the status function
    final_result = (await get_execution_status_and_result(request_id, chain_config, account))["result"]
    
    # Simulate a brief delay to make the state changes visible
    await asyncio.sleep(1.5)
    
    # Create a properly structured verified result
    verified_result = {
        "content": [
            {
                "type": "text", 
                "text": "Best lending strategy found: Aave on Ethereum, with 4.5% APY for USDC deposits. Lower risk profile than alternatives and higher liquidity."
            }
        ],
        "isError": False,
        "verified": True
    }
    
    # Update transaction state and final result if transaction_id is provided
    if transaction_id:
        transaction_storage.update_transaction_state(
            tx_id=transaction_id,
            state_name="verification",
            status="completed",
            details={"verified": True}
        )
        
        transaction_storage.update_transaction_details(
            tx_id=transaction_id,
            final_result=verified_result
        )
    
    return verified_result

# --- Transaction Management Functions ---

async def create_new_transaction(
    owner_address: str,
    safe_address: Optional[str],
    prompt: str,
    selected_tools: List[Any],
    total_cost: float
) -> str:
    """
    Create a new transaction in the storage and return its ID.
    This function will be called at the beginning of the request process.
    """
    try:
        transaction = transaction_storage.create_transaction(
            owner_address=owner_address,
            safe_address=safe_address,
            prompt=prompt,
            selected_tools=selected_tools,
            total_cost=total_cost
        )
        logging.info(f"Created new transaction with ID: {transaction.id}")
        return transaction.id
    except Exception as e:
        logging.error(f"Error creating transaction: {e}")
        raise

async def get_transaction_by_id(transaction_id: str):
    """Get a single transaction by ID."""
    return transaction_storage.get_transaction(transaction_id)

async def get_transactions_for_account(wallet_address: str):
    """Get all transactions associated with a wallet address."""
    return transaction_storage.get_transactions_by_owner(wallet_address)

async def get_transaction_details(transaction_id: str):
    """Get detailed information about a transaction."""
    transaction = transaction_storage.get_transaction(transaction_id)
    if not transaction:
        return None
    
    # Calculate overall status based on state statuses
    overall_status = "pending"
    if transaction.verification_state and transaction.verification_state.status == "completed":
        overall_status = "completed"
    elif transaction.execution_state and transaction.execution_state.status == "completed":
        overall_status = "completed (unverified)"
    elif transaction.execution_state and transaction.execution_state.status == "in_progress":
        overall_status = "executing"
    elif transaction.payment_state and transaction.payment_state.status == "completed":
        overall_status = "payment complete"
    elif transaction.payment_state and transaction.payment_state.status == "in_progress":
        overall_status = "payment processing"
    elif transaction.request_state and transaction.request_state.status == "completed":
        overall_status = "request submitted"
    
    # Format step status for display
    steps = []
    for step in transaction.execution_steps:
        steps.append({
            "step": step.step,
            "tool": step.tool,
            "status": step.status,
            "timestamp": step.timestamp.isoformat() if step.timestamp else None
        })
    
    # Return formatted details
    return {
        "id": transaction.id,
        "owner_address": transaction.owner_address,
        "safe_address": transaction.safe_address,
        "prompt": transaction.prompt,
        "selected_tools": [t.name for t in transaction.selected_tools],
        "total_cost": transaction.total_cost,
        "created_at": transaction.created_at.isoformat(),
        "updated_at": transaction.updated_at.isoformat(),
        "overall_status": overall_status,
        "request_status": transaction.request_state.status if transaction.request_state else "pending",
        "payment_status": transaction.payment_state.status if transaction.payment_state else "pending",
        "execution_status": transaction.execution_state.status if transaction.execution_state else "pending",
        "verification_status": transaction.verification_state.status if transaction.verification_state else "pending",
        "request_tx_hash": transaction.request_tx_hash,
        "payment_tx_hash": transaction.payment_tx_hash,
        "request_id": transaction.execution_info.get("requestId") if transaction.execution_info else None,
        "operator": transaction.execution_info.get("operator") if transaction.execution_info else None,
        "steps": steps,
        "final_result": transaction.final_result
    }
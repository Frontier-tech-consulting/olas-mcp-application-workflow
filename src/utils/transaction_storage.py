"""Transaction storage utilities for the application."""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from models.models import Transaction, TransactionState, Tool, ExecutionStep
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to store transaction data
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def _load_transactions() -> Dict[str, Dict[str, Any]]:
    """Load transactions from the JSON file."""
    try:
        if os.path.exists(TRANSACTIONS_FILE):
            with open(TRANSACTIONS_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading transactions: {e}")
        return {}

def _save_transactions(transactions: Dict[str, Dict[str, Any]]) -> bool:
    """Save transactions to the JSON file."""
    try:
        with open(TRANSACTIONS_FILE, "w") as f:
            json.dump(transactions, f, default=_json_serializer, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving transactions: {e}")
        return False

def _json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (Tool, TransactionState, ExecutionStep)):
        return obj.__dict__
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Type {type(obj)} not serializable")

def _dict_to_transaction(data: Dict[str, Any]) -> Transaction:
    """Convert a dictionary to a Transaction object."""
    # Create base transaction
    transaction = Transaction(
        id=data.get("id", str(uuid.uuid4())),
        owner_address=data.get("owner_address", ""),
        safe_address=data.get("safe_address"),
        prompt=data.get("prompt", ""),
        total_cost=float(data.get("total_cost", 0.0))
    )
    
    # Add timestamps
    if "created_at" in data:
        try:
            transaction.created_at = datetime.fromisoformat(data["created_at"])
        except (ValueError, TypeError):
            transaction.created_at = datetime.now()
    
    if "updated_at" in data:
        try:
            transaction.updated_at = datetime.fromisoformat(data["updated_at"])
        except (ValueError, TypeError):
            transaction.updated_at = datetime.now()
    
    # Add tools
    if "selected_tools" in data and isinstance(data["selected_tools"], list):
        transaction.selected_tools = [
            Tool(**t) if isinstance(t, dict) else t
            for t in data["selected_tools"]
        ]
    
    # Add states
    if "request_state" in data and data["request_state"]:
        state_data = data["request_state"]
        transaction.request_state = TransactionState(
            status=state_data.get("status", "pending"),
            details=state_data.get("details", {})
        )
        if "timestamp" in state_data:
            try:
                transaction.request_state.timestamp = datetime.fromisoformat(state_data["timestamp"])
            except (ValueError, TypeError):
                pass
    
    if "payment_state" in data and data["payment_state"]:
        state_data = data["payment_state"]
        transaction.payment_state = TransactionState(
            status=state_data.get("status", "pending"),
            details=state_data.get("details", {})
        )
        if "timestamp" in state_data:
            try:
                transaction.payment_state.timestamp = datetime.fromisoformat(state_data["timestamp"])
            except (ValueError, TypeError):
                pass
    
    if "execution_state" in data and data["execution_state"]:
        state_data = data["execution_state"]
        transaction.execution_state = TransactionState(
            status=state_data.get("status", "pending"),
            details=state_data.get("details", {})
        )
        if "timestamp" in state_data:
            try:
                transaction.execution_state.timestamp = datetime.fromisoformat(state_data["timestamp"])
            except (ValueError, TypeError):
                pass
    
    if "verification_state" in data and data["verification_state"]:
        state_data = data["verification_state"]
        transaction.verification_state = TransactionState(
            status=state_data.get("status", "pending"),
            details=state_data.get("details", {})
        )
        if "timestamp" in state_data:
            try:
                transaction.verification_state.timestamp = datetime.fromisoformat(state_data["timestamp"])
            except (ValueError, TypeError):
                pass
    
    # Add execution steps
    if "execution_steps" in data and isinstance(data["execution_steps"], list):
        transaction.execution_steps = []
        for step_data in data["execution_steps"]:
            step = ExecutionStep(
                step=step_data.get("step", "Unknown Step"),
                tool=step_data.get("tool", "Unknown Tool"),
                status=step_data.get("status", "pending"),
                result=step_data.get("result")
            )
            if "timestamp" in step_data:
                try:
                    step.timestamp = datetime.fromisoformat(step_data["timestamp"])
                except (ValueError, TypeError):
                    step.timestamp = datetime.now()
            transaction.execution_steps.append(step)
    
    # Add transaction data
    transaction.request_tx_hash = data.get("request_tx_hash")
    transaction.payment_tx_hash = data.get("payment_tx_hash")
    transaction.execution_info = data.get("execution_info", {})
    transaction.final_result = data.get("final_result")
    
    return transaction

def create_transaction(
    owner_address: str,
    safe_address: Optional[str],
    prompt: str,
    selected_tools: List[Tool],
    total_cost: float
) -> Transaction:
    """
    Create a new transaction record.
    
    Args:
        owner_address: The owner's wallet address
        safe_address: Optional Safe account address
        prompt: The user's prompt
        selected_tools: List of selected Tool objects
        total_cost: The total cost in xDAI
        
    Returns:
        The created Transaction object
    """
    # Create transaction object
    transaction = Transaction(
        id=str(uuid.uuid4()),
        owner_address=owner_address,
        safe_address=safe_address,
        prompt=prompt,
        selected_tools=selected_tools,
        total_cost=total_cost,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Load existing transactions
    transactions = _load_transactions()
    
    # Add new transaction
    transactions[transaction.id] = transaction
    
    # Save updated transactions
    _save_transactions(transactions)
    
    logger.info(f"Created transaction: {transaction.id}")
    
    return transaction

def get_transaction(transaction_id: str) -> Optional[Transaction]:
    """
    Get a transaction by ID.
    
    Args:
        transaction_id: The transaction ID
        
    Returns:
        Transaction object if found, None otherwise
    """
    transactions = _load_transactions()
    
    if transaction_id in transactions:
        return _dict_to_transaction(transactions[transaction_id])
    
    return None

def get_transactions_by_owner(owner_address: str) -> List[Transaction]:
    """
    Get all transactions for a specific owner.
    
    Args:
        owner_address: The owner's wallet address
        
    Returns:
        List of Transaction objects
    """
    transactions = _load_transactions()
    
    # Filter transactions by owner
    owner_transactions = []
    for tx_data in transactions.values():
        if tx_data.get("owner_address", "").lower() == owner_address.lower():
            owner_transactions.append(_dict_to_transaction(tx_data))
    
    # Sort by created_at (newest first)
    owner_transactions.sort(key=lambda tx: tx.created_at, reverse=True)
    
    return owner_transactions

def update_transaction_state(
    tx_id: str,
    state_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update a transaction state.
    
    Args:
        tx_id: The transaction ID
        state_name: The state to update (request, payment, execution, verification)
        status: The new status (pending, in_progress, completed, failed)
        details: Additional details for the state
        
    Returns:
        True if successful, False otherwise
    """
    if state_name not in ["request", "payment", "execution", "verification"]:
        logger.error(f"Invalid state name: {state_name}")
        return False
    
    transactions = _load_transactions()
    
    if tx_id not in transactions:
        logger.error(f"Transaction not found: {tx_id}")
        return False
    
    # Get transaction
    tx_data = transactions[tx_id]
    
    # Update state
    state_key = f"{state_name}_state"
    tx_data[state_key] = {
        "status": status,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Update updated_at timestamp
    tx_data["updated_at"] = datetime.now().isoformat()
    
    # Save updated transactions
    return _save_transactions(transactions)

def update_transaction_details(
    tx_id: str,
    **kwargs
) -> bool:
    """
    Update transaction details.
    
    Args:
        tx_id: The transaction ID
        **kwargs: Fields to update (request_tx_hash, payment_tx_hash, execution_info, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    transactions = _load_transactions()
    
    if tx_id not in transactions:
        logger.error(f"Transaction not found: {tx_id}")
        return False
    
    # Get transaction
    tx_data = transactions[tx_id]
    
    # Update fields
    for key, value in kwargs.items():
        tx_data[key] = value
    
    # Update updated_at timestamp
    tx_data["updated_at"] = datetime.now().isoformat()
    
    # Save updated transactions
    return _save_transactions(transactions)

def update_execution_step(
    tx_id: str,
    step_index: int,
    status: str,
    result: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update an execution step.
    
    Args:
        tx_id: The transaction ID
        step_index: The index of the step to update
        status: The new status (pending, in_progress, completed, error)
        result: Optional result data
        
    Returns:
        True if successful, False otherwise
    """
    transactions = _load_transactions()
    
    if tx_id not in transactions:
        logger.error(f"Transaction not found: {tx_id}")
        return False
    
    # Get transaction
    tx_data = transactions[tx_id]
    
    # Check if execution_steps exists and has enough steps
    if "execution_steps" not in tx_data or not isinstance(tx_data["execution_steps"], list):
        logger.error(f"No execution steps found for transaction: {tx_id}")
        return False
    
    if step_index >= len(tx_data["execution_steps"]):
        logger.error(f"Step index out of range: {step_index}, max: {len(tx_data['execution_steps']) - 1}")
        return False
    
    # Update step
    tx_data["execution_steps"][step_index]["status"] = status
    tx_data["execution_steps"][step_index]["timestamp"] = datetime.now().isoformat()
    
    if result is not None:
        tx_data["execution_steps"][step_index]["result"] = result
    
    # Update updated_at timestamp
    tx_data["updated_at"] = datetime.now().isoformat()
    
    # Save updated transactions
    return _save_transactions(transactions)

def generate_eth_address(seed: str) -> str:
    """
    Deterministically generate a mock Ethereum address from a seed (e.g., email).
    """
    h = hashlib.sha256(seed.encode()).hexdigest()
    return "0x" + h[:40]

def generate_gnosis_safe_address(owner_address: str) -> str:
    """
    Generate a mock Gnosis Safe address based on the owner's Ethereum address.
    """
    # For demo: hash the owner address with a salt and return as a new address
    salt = "olas-gnosis-safe"
    h = hashlib.sha256((owner_address + salt).encode()).hexdigest()
    return "0x" + h[:40]
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel

@dataclass
class ChainConfig:
    """Configuration for the blockchain connection."""
    chainId: int = 100  # Default to Gnosis Chain
    rpcUrl: str = "https://rpc.gnosischain.com"
    mechMarketplace: str = "0x8b299c20f87e3fcbff0e1b86dc0acc06ab6993ef"

    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "chainId": self.chainId,
            "rpcUrl": self.rpcUrl,
            "mechMarketplace": self.mechMarketplace
        }

@dataclass
class Tool:
    """A tool that can be used for data analysis."""
    name: str
    cost: str
    description: Optional[str] = None
    available: bool = True
    
@dataclass
class ExecutionStep:
    """A step in the execution process."""
    step: str
    tool: str
    status: str = "pending"  # pending, in_progress, completed, error
    result: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

@dataclass
class PrivyUser:
    """Represents a user authenticated through Privy."""
    user_id: str
    address: str
    email: Optional[str] = None
    name: Optional[str] = None
    profile_image: Optional[str] = None
    linked_accounts: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TransactionState:
    """Represents the state of a transaction phase."""
    status: str  # pending, in_progress, completed, failed
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Transaction:
    """Represents a transaction in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner_address: str = ""
    safe_address: Optional[str] = None
    prompt: str = ""
    selected_tools: List[Tool] = field(default_factory=list)
    total_cost: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Transaction states
    request_state: Optional[TransactionState] = None
    payment_state: Optional[TransactionState] = None
    execution_state: Optional[TransactionState] = None
    verification_state: Optional[TransactionState] = None
    
    # Transaction data
    request_tx_hash: Optional[str] = None
    payment_tx_hash: Optional[str] = None
    execution_info: Dict[str, Any] = field(default_factory=dict)
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    final_result: Optional[Dict[str, Any]] = None

class PrivyUser(BaseModel):
    """Model for Privy user data."""
    user_id: str  # Supabase user ID
    privy_user_id: str  # Privy user ID
    address: str
    email: Optional[str] = None
    name: Optional[str] = None
    linked_accounts: List[Dict[str, Any]] = []

class ChainConfig(BaseModel):
    """Model for chain configuration."""
    chain_id: int = 100  # Default to Gnosis Chain
    rpc_url: str = "https://rpc.gnosischain.com"
    mech_marketplace: str = "0x4554fE75c1f5576c1d7F765B2A036c199Adae329"

class Tool(BaseModel):
    """Model for mech tools."""
    name: str
    description: str
    cost: float
    mech_address: str
    owner_address: str

class ExecutionStep(BaseModel):
    """Model for execution steps."""
    step: str
    tool: str
    status: str
    result: Optional[Dict[str, Any]] = None
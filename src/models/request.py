from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Request:
    """Model for handling MCP service requests"""
    prompt: str
    selected_services: List[dict]
    user_email: Optional[str] = None
    total_cost: Optional[str] = None
    request_tx_hash: Optional[str] = None
    payment_tx_hash: Optional[str] = None
    execution_info: Optional[dict] = None
    execution_steps: List[str] = field(default_factory=list)
    execution_status: str = "pending"
    final_result: Optional[str] = None
    error_message: Optional[str] = None
    transaction_id: Optional[str] = None
    reasoning_steps: Optional[List[str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert request to dictionary"""
        return {
            "prompt": self.prompt,
            "selected_services": self.selected_services,
            "user_email": self.user_email,
            "total_cost": self.total_cost,
            "request_tx_hash": self.request_tx_hash,
            "payment_tx_hash": self.payment_tx_hash,
            "execution_info": self.execution_info,
            "execution_steps": self.execution_steps if self.execution_steps else [],
            "execution_status": self.execution_status,
            "final_result": self.final_result,
            "error_message": self.error_message,
            "transaction_id": self.transaction_id,
            "reasoning_steps": self.reasoning_steps if self.reasoning_steps else []
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Request':
        """Create request from dictionary"""
        return cls(**data) 
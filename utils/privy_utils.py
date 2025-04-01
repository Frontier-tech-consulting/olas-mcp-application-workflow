import os
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PrivyAPI:
    """Utility class for interacting with Privy API."""
    
    BASE_URL = "https://auth.privy.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Privy API client.
        
        Args:
            api_key: Your Privy API key (if None, will try to use PRIVY_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get("PRIVY_API_KEY")
        if not self.api_key:
            raise ValueError("Privy API key must be provided either through constructor or PRIVY_API_KEY environment variable")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Privy API."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            if method.lower() == "get":
                response = requests.get(url, headers=headers, params=data or {})
            elif method.lower() == "post":
                response = requests.post(url, headers=headers, json=data or {})
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Privy API request failed: {e}")
            return {"error": str(e)}
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Privy.
        
        Args:
            user_id: The Privy user ID
            
        Returns:
            Dict containing user information
        """
        return self._make_request("get", f"users/{user_id}")
    
    def verify_wallet_ownership(self, user_id: str, address: str) -> bool:
        """
        Verify that a wallet address belongs to a user.
        
        Args:
            user_id: The Privy user ID
            address: The wallet address to verify
            
        Returns:
            True if the wallet belongs to the user, False otherwise
        """
        user_data = self.get_user(user_id)
        if "error" in user_data:
            return False
        
        linked_accounts = user_data.get("linked_accounts", [])
        for account in linked_accounts:
            if account.get("type") == "wallet" and account.get("address", "").lower() == address.lower():
                return True
        
        return False

import os
import requests
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PrivyRestAPI:
    """
    Utility class for interacting with Privy REST API.
    Documentation: https://docs.privy.io/basics/rest-api/setup
    """
    
    BASE_URL = "https://auth.privy.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None, app_id: Optional[str] = None):
        """
        Initialize the Privy REST API client.
        
        Args:
            api_key: Your Privy API key (if None, will try to use PRIVY_API_KEY environment variable)
            app_id: Your Privy App ID (if None, will try to use PRIVY_APP_ID environment variable)
        """
        self.api_key = api_key or os.environ.get("PRIVY_API_KEY") or "cm8ygineh03nub96j8exgsyat"
        self.app_id = app_id or os.environ.get("PRIVY_APP_ID") or "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEnYoI6LZihY+KBDNYxmw8Jj5UTpE9jtDm1ssanOqtUmBLggjRtFB3rq/YTlQ7u/f6V68lEye5KWwQRPCGD7Ee6Q=="
        
        if not self.api_key:
            raise ValueError("Privy API key must be provided either through constructor or PRIVY_API_KEY environment variable")
        
        if not self.app_id:
            raise ValueError("Privy App ID must be provided either through constructor or PRIVY_APP_ID environment variable")
    
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
            elif method.lower() == "put":
                response = requests.put(url, headers=headers, json=data or {})
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Privy API request failed: {e}")
            return {"error": str(e)}
    
    def create_verification_code(self, email: str) -> Dict[str, Any]:
        """
        Create a verification code for an email address.
        
        Args:
            email: The email address to send the verification code to
            
        Returns:
            Dict containing the verification request details
        """
        endpoint = "verification-codes"
        data = {
            "app_id": self.app_id,
            "email": email
        }
        return self._make_request("post", endpoint, data)
    
    def verify_code(self, email: str, code: str) -> Dict[str, Any]:
        """
        Verify a code that was sent to an email address.
        
        Args:
            email: The email address that received the code
            code: The verification code
            
        Returns:
            Dict containing the verification result and user details
        """
        endpoint = "verification-codes/verify"
        data = {
            "app_id": self.app_id,
            "email": email,
            "code": code
        }
        return self._make_request("post", endpoint, data)
    
    def create_user(self, email: str) -> Dict[str, Any]:
        """
        Create a new user with email.
        
        Args:
            email: The email address for the new user
            
        Returns:
            Dict containing the created user details
        """
        endpoint = "users"
        data = {
            "app_id": self.app_id,
            "email": email
        }
        return self._make_request("post", endpoint, data)
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details by user ID.
        
        Args:
            user_id: The Privy user ID
            
        Returns:
            Dict containing the user details
        """
        endpoint = f"users/{user_id}"
        return self._make_request("get", endpoint)
    
    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Find a user by email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            Dict containing the user details if found, or error message
        """
        endpoint = "users/by-email"
        data = {
            "app_id": self.app_id,
            "email": email
        }
        return self._make_request("get", endpoint, data)
    
    def create_embedded_wallet(self, user_id: str) -> Dict[str, Any]:
        """
        Create an embedded wallet for a user.
        
        Args:
            user_id: The Privy user ID
            
        Returns:
            Dict containing the wallet details
        """
        endpoint = f"users/{user_id}/embedded-wallets"
        data = {
            "app_id": self.app_id
        }
        return self._make_request("post", endpoint, data)
    
    def get_user_wallets(self, user_id: str) -> Dict[str, Any]:
        """
        Get all wallets for a user.
        
        Args:
            user_id: The Privy user ID
            
        Returns:
            Dict containing the user's wallets
        """
        endpoint = f"users/{user_id}/linked-accounts"
        return self._make_request("get", endpoint)
    
    def generate_auth_token(self, user_id: str) -> Dict[str, Any]:
        """
        Generate an auth token for a user.
        
        Args:
            user_id: The Privy user ID
            
        Returns:
            Dict containing the generated token
        """
        endpoint = "auth/tokens"
        data = {
            "app_id": self.app_id,
            "user_id": user_id
        }
        return self._make_request("post", endpoint, data)

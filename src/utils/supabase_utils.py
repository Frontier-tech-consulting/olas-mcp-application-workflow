import os
import dotenv
from supabase import  Client, create_client
from typing import Dict, Any, Optional
import logging
import re
from dotenv import load_dotenv
from pathlib import Path
logger = logging.getLogger(__name__)
import sys

## getting the relative path of the .env from the root using path 
# dotenv_path = Path(__file__).parent.parent.parent.resolve() / '.env'

# print(f"env file loaded: {load_dotenv(dotenv_path=dotenv_path)}")

class SupabaseObj:
    """Utility class for interacting with Supabase."""
    
    def __init__(self):
        """Initialize the Supabase client."""
        ## NOTE: based on the deployment setup, you will need to define the vars in the .env file
        supabase_url: str = os.getenv("SUPABASE_URL")
        supabase_key: str = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        try:
            # Extract project ID from the connection string
            # Format: postgresql://postgres.[PROJECT_ID]:[PASSWORD]@[HOST]:[PORT]/postgres
            #match = re.search(r'postgresql://postgres\.([^:]+):', supabase_url)
            # if match:
            #     project_id = match.group(1)
            #     # Construct the Supabase URL in the correct format
            #     supabase_url = f"https://{project_id}.supabase.co"
            #     logger.info(f"Using Supabase URL: {supabase_url}")
            # else:
            #     # If the URL is already in the correct format, use it as is
            #     if not supabase_url.startswith("https://"):
            #         supabase_url = f"{supabase_url}"
            #     logger.info(f"Using provided Supabase URL: {supabase_url}")
            
            self.client: Client = Client(supabase_url, supabase_key)
            # # Test the connection
            # self.client.table('users').select('count').limit(1).execute()
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise ValueError(f"Failed to connect to Supabase: {e}")
    
    def create_or_get_user(self, privy_user_id: str, email: str, wallet_address: str) -> Dict[str, Any]:
        """
        Create a new user or get existing user from Supabase.
        
        Args:
            privy_user_id: The Privy user ID
            email: User's email address
            wallet_address: User's wallet address
            
        Returns:
            Dict containing user information
        """
        try:
            # Check if user exists
            response = self.client.table('users').select('*').eq('privy_user_id', privy_user_id).execute()
            
            if response.data and len(response.data) > 0:
                # User exists, return user data
                return response.data[0]
            
            # Create new user
            user_data = {
                'privy_user_id': privy_user_id,
                'email': email,
                'wallet_address': wallet_address,
                'created_at': 'now()'
            }
            
            response = self.client.table('users').insert(user_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            logger.error(f"Error in create_or_get_user: {e}")
            raise
    
    def get_user_by_wallet(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """
        Get user by wallet address.
        
        Args:
            wallet_address: The wallet address to look up
            
        Returns:
            Dict containing user information or None if not found
        """
        try:
            response = self.client.table('users').select('*').eq('wallet_address', wallet_address).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error in get_user_by_wallet: {e}")
            return None
    
    def update_user_wallet(self, privy_user_id: str, wallet_address: str) -> Optional[Dict[str, Any]]:
        """
        Update user's wallet address.
        
        Args:
            privy_user_id: The Privy user ID
            wallet_address: The new wallet address
            
        Returns:
            Updated user data or None if update failed
        """
        try:
            response = self.client.table('users').update({
                'wallet_address': wallet_address,
                'updated_at': 'now()'
            }).eq('privy_user_id', privy_user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error in update_user_wallet: {e}")
            return None
    
    def save_session_state(self, privy_user_id: str, state: dict):
        """Save or update session state for a user."""
        try:
            response = self.client.table('session_state').upsert({
                'privy_user_id': privy_user_id,
                'state': state,
                'updated_at': 'now()'
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error saving session state: {e}")
            return None

    def load_session_state(self, privy_user_id: str) -> Optional[dict]:
        """Load session state for a user."""
        try:
            response = self.client.table('session_state').select('state').eq('privy_user_id', privy_user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]['state']
            return None
        except Exception as e:
            logger.error(f"Error loading session state: {e}")
            return None
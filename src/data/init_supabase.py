from dotenv import load_dotenv
from pathlib import Path
import sys
import logging
from supabase import create_client, Client
import re
import os


dotenv_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_supabase():
    """Initialize Supabase database with required tables."""
    # Get Supabase credentials from environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    try:
        # Extract project ID from the connection string
        # Format: postgresql://postgres.[PROJECT_ID]:[PASSWORD]@[HOST]:[PORT]/postgres
        match = re.search(r'postgresql://postgres\.([^:]+):', supabase_url)
        if match:
            project_id = match.group(1)
            # Construct the Supabase URL in the correct format
            supabase_url = f"https://{project_id}.supabase.co"
            logger.info(f"Using Supabase URL: {supabase_url}")
        else:
            # If the URL is already in the correct format, use it as is
            if not supabase_url.startswith("https://"):
                supabase_url = f"https://{supabase_url}"
            logger.info(f"Using provided Supabase URL: {supabase_url}")
        
        # Initialize Supabase client
        client: Client = create_client(supabase_url, supabase_key)
        logger.info("Successfully connected to Supabase")
        
        # Check if the users table exists
        try:
            # Try to select from the users table
            result = client.table('users').select('count').limit(1).execute()
            logger.info("Users table already exists and is accessible")
            return True
        except Exception as e:
            logger.warning(f"Users table does not exist or is not accessible: {e}")
            logger.info("Please follow the manual setup instructions below:")
            
            # Print instructions for manual setup
            print("\n" + "="*80)
            print("MANUAL SETUP INSTRUCTIONS")
            print("="*80)
            print("The users table does not exist in your Supabase database.")
            print("Please follow these steps to set it up manually:")
            print("\n1. Log in to your Supabase dashboard at https://app.supabase.com")
            print("2. Select your project")
            print("3. Go to the SQL Editor")
            print("4. Copy and paste the following SQL:")
            print("\n" + "-"*80)
            with open('init_supabase.sql', 'r') as f:
                print(f.read())
            print("-"*80)
            print("\n5. Run the SQL to create the users table")
            print("6. Verify the table was created by checking the Table Editor")
            print("="*80 + "\n")
            
            return False
        
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise

if __name__ == "__main__":
    try:
        success = init_supabase()
        if success:
            print("Supabase initialization completed successfully!")
        else:
            print("Supabase initialization requires manual setup. Please follow the instructions above.")
    except Exception as e:
        print(f"Error initializing Supabase: {e}")
        sys.exit(1) 
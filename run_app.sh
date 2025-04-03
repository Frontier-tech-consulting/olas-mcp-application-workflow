#!/bin/bash

# Run script for the OLAS MCP application with Privy authentication
echo "Starting OLAS MCP application..."

# Make sure the data directory exists
mkdir -p data

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file with sample values..."
    cat <<EOF > .env
# Ethereum private key (for development only, keep secure in production)
ETHEREUM_PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000001

# Privy API credentials
PRIVY_APP_ID=your-privy-app-id
PRIVY_API_KEY=your-privy-api-key

# Supabase credentials
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-anon-key

# Optional Safe address (if you have an existing Safe)
# SAFE_ADDRESS=0xYourSafeAddress

# MCP Server URL (default is local)
MCP_SERVER_URL=http://localhost:8000
EOF
    echo "Created .env file with sample values. Please edit with your actual credentials."
fi

# Run the Streamlit app
streamlit run app.py

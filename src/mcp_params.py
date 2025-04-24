from mcp.server import MCPServer
from src.services.mcp_service import MCPService
import os

def instantiate_mock_mcp_server_instance(mpc_url=None):
    """
    Instantiate the MCP server instance.
    """
    # Initialize MCP service
    try:
        server_url = mpc_url or os.getenv("MCP_SERVER_URL")
        if server_url:
            print(f"Initializing MCP service with server URL: {server_url}")
            mcp_service = MCPService(server_url)
        else:
            print("Initializing MCP service with mock profile")
            mcp_service = MCPService("mock")
    except Exception as e:
        print(f"Error initializing MCP service: {str(e)}")
        # Fallback to mock service
        mcp_service = MCPService("mock")

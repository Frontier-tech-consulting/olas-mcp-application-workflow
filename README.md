# OLAS MCP Documentation

## Overview
The OLAS MCP project is the swiss knife orchestration framework on running reasoning agents on realiable ecosystem 
## System Architecture
The system is designed with a microservices architecture, including:
1. **User Interface Layer**: A Streamlit-based interface for query submission and result display.
2. **MCP Orchestration Service**: Coordinates the overall query processing workflow.
3. **RAG Pipeline**: Analyzes queries and selects appropriate tools and services.
4. **Olas Integration Service**: Connects to Olas mech services via blockchain.
5. **Verification Service**: Validates responses and ensures accuracy.
6. **Token Management Service**: Handles payments and token operations.

## Features
- **Query Processing Module**: Implements a lightweight RAG pipeline for analyzing user prompts.
- **MCP Client Module**: Manages communication with MCP servers.
- **Olas Integration Module**: Connects to Gnosis Chain and interacts with MechMarketplace contracts.
- **Payment Module**: Calculates service costs and manages xDAI transactions.
- **Verification Module**: Validates results and implements a basic slashing mechanism.
- **Streamlit UI**: Provides an intuitive interface for users.

## Setup Instructions
### Prerequisites
- Python 3.11+
- Node.js and npm
- Supabase account

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd olas-mcp
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Node.js dependencies:
   ```bash
   cd docs
   npm install
   ```
4. Set up Supabase:
   Follow the instructions in `SUPABASE_SETUP.md` to configure your Supabase project.

## Running the Application
1. Start the backend services:
   ```bash
   python app.py
   ```
2. Start the frontend:
   ```bash
   cd docs
   npm run dev
   ```

## Build and Deployment

### Local Development
1. Ensure you’ve set the required environment variables (see the `Setup Instructions` section).
2. Launch the Streamlit app:
   ```bash
   streamlit run app.py
   ```
3. Access the application at `http://localhost:8501` in your browser.

### Docker Deployment
1. Build the Docker image:
   ```bash
   docker build -t olas-mcp:latest .
   ```
2. Run the container:
   ```bash
   docker run -p 8501:8501 --env-file .env olas-mcp:latest
   ```
3. Access the application at `http://localhost:8501`.

### Cloud Deployment
1. Use a cloud platform like AWS, GCP, or Azure to host the application.
2. For containerized deployment, use Kubernetes or a container orchestration service.
3. Set up monitoring and logging for production environments to ensure high availability and reliability.

## Deployment
- Use Docker and Kubernetes for containerization and scaling.
- Set up monitoring and logging for production environments.

## Security Considerations
- Use secure key management systems.
- Encrypt sensitive data at rest and in transit.
- Audit all smart contracts before deployment.

## Future Enhancements
- Implement vector-based retrieval for better tool selection.
- Extend support to additional blockchain networks.
- Introduce demand-based pricing using oracles.

## License
This project is licensed under the MIT License.
# MCP Orchestration Service for User Prompts

## Overview

The MCP Orchestration Service provides end-to-end processing of user prompts by leveraging the Olas protocol's Mech services and the Model Context Protocol. This implementation guide describes how to build a complete workflow for submitting user queries, processing them with AI agents, and delivering verified results.

## System Architecture

The system follows a microservices architecture with these core components:

1. **User Interface Layer**: Streamlit-based interface for query submission and result display
2. **MCP Orchestration Service**: Coordinates the overall query processing workflow
3. **RAG Pipeline**: Analyzes queries and selects appropriate tools and services
4. **Olas Integration Service**: Connects to Olas mech services via blockchain
5. **Verification Service**: Validates responses and ensures accuracy
6. **Token Management Service**: Handles payments and token operations


## 2.1 Component Structure

The service follows a modular design with the following key components:

- **Query Processing Module**
  - Implements a lightweight RAG pipeline
  - Analyzes user prompts to extract entities and intents
  - Maps queries to appropriate Olas services and tools

- **MCP Client Module**
  - Manages communication with MCP servers
  - Formats requests according to MCP specifications
  - Handles tools/call, tools/list, and resources/read operations

- **Olas Integration Module**
  - Connects to Gnosis Chain (Chain ID: 100)
  - Interacts with MechMarketplace contract (0x4554fE75c1f5576c1d7F765B2A036c199Adae329)
  - Retrieves available mech services (using data from list-mech.json & enriched_services_data.json)

- **Payment Module**
  - Calculates service costs based on selected tools
  - Manages xDAI transactions via Web3.py
  - Implements basic timelock functionality for funds

- **Verification Module**
  - Validates results from multiple operators
  - Detects inconsistencies and potential hallucinations
  - Implements a basic slashing mechanism

- **Streamlit UI**
  - Provides intuitive input forms for queries
  - Displays execution status and results
  - Manages user authentication via Supabase


## Detailed Workflow

### 1. Create a Request

**User Goal:** Submit a natural language prompt requesting DeFi strategy analysis.

#### Implementation Details

```python
import streamlit as st
from web3 import Web3
from mech_client import MechClient
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize web3 connection
web3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL", "https://rpc.gnosischain.com")))
mech_marketplace_address = os.getenv("MECH_MARKETPLACE", "0x4554fE75c1f5576c1d7F765B2A036c199Adae329")

# Initialize mech client
mech_client = MechClient(
    web3=web3,
    mech_marketplace_address=mech_marketplace_address
)

def create_request(account, chain_config, prompt):
    """Create a new request for DeFi strategy analysis."""
    # Format the request according to MCP protocol
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "DeFiLendingStrategy",
            "arguments": {
                "account": account,
                "chainConfig": chain_config,
                "prompt": prompt
            }
        }
    }
    
    # Submit request to mech marketplace
    tx_hash = mech_client.submit_request(json.dumps(request), sender=account)
    return tx_hash
```

#### UI Components

```python
def request_ui():
    st.title("OLAS DeFi Strategy Finder")
    st.write("Submit a prompt to find the best DeFi lending strategy")
    
    # Account selection
    account = st.text_input("Wallet Address")
    
    # Chain configuration
    st.subheader("Chain Configuration")
    chain_id = st.number_input("Chain ID", value=100, min_value=1)
    rpc_url = st.text_input("RPC URL", value="https://rpc.gnosischain.com")
    mech_marketplace = st.text_input(
        "Mech Marketplace Contract", 
        value="0x4554fE75c1f5576c1d7F765B2A036c199Adae329"
    )
    
    # Prompt input
    st.subheader("Strategy Prompt")
    prompt = st.text_area(
        "Describe your DeFi strategy requirements",
        placeholder="Example: Analyze lending strategies across Aave, Compound, and Maker using DeFiLlama, TheGraph, and Space and Time datasets, then perform quant analysis to recommend the best option."
    )
    
    # Submit button
    if st.button("Submit Request"):
        if not account or not prompt:
            st.error("Please provide wallet address and prompt")
            return
        
        chain_config = {
            "chainId": chain_id,
            "rpcUrl": rpc_url,
            "mechMarketplace": mech_marketplace
        }
        
        with st.spinner("Creating request..."):
            tx_hash = create_request(account, chain_config, prompt)
            st.success(f"Request submitted! Transaction hash: {tx_hash}")
            st.session_state.tx_hash = tx_hash
            st.session_state.prompt = prompt
            st.session_state.step = "tool_selection"
```

### 2. Mock Simulation of Reasoning Steps

**User Goal:** Visualize the reasoning steps streaming to understand the decision-making process.

#### Implementation Details

```python
reasoning_steps = ["Identify task type", "Select tools", "Plan execution"]
for step in reasoning_steps:
    with st.expander(f"Simulating: {step}", expanded=True):
        st.write(f"Simulating {step}...")
```

#### UI Components

```python
def reasoning_simulation_ui():
    st.title("Reasoning Simulation")
    st.write("Visualize the reasoning steps for your request")
    
    reasoning_steps = ["Identify task type", "Select tools", "Plan execution"]
    for step in reasoning_steps:
        with st.expander(f"Simulating: {step}", expanded=True):
            st.write(f"Simulating {step}...")
```

### 3. Service Selection

**User Goal:** Select appropriate mech services for execution.

#### Implementation Details

```python
def load_services_from_json():
    # Load services from enriched_services_data.json and olas_ethereum_components.json
    enriched_services = json.load(open('enriched_services_data.json'))['services']
    ethereum_components = json.load(open('olas_ethereum_components.json'))['components']
    return enriched_services + ethereum_components

services = load_services_from_json()
for service in services:
    with st.expander(f"Service: {service['description']}", expanded=True):
        st.checkbox(f"Select {service['service_id']} - Cost: {service.get('cost', 'N/A')}")
```

#### UI Components

```python
def service_selection_ui():
    st.title("Select Services")
    st.write("Choose the mech services needed for your strategy analysis")
    
    services = load_services_from_json()
    for service in services:
        with st.expander(f"Service: {service['description']}", expanded=True):
            st.checkbox(f"Select {service['service_id']} - Cost: {service.get('cost', 'N/A')}")
```

### 4. Execution

**User Goal:** Execute the strategy analysis and monitor progress.

#### Implementation Details

```python
def start_execution(payment_tx_hash, selected_tools):
    """Start execution of the strategy analysis."""
    # Prepare execution steps based on selected tools
    execution_steps = []
    for tool in selected_tools:
        if tool["name"] == "DeFiLlamaAPI":
            execution_steps.append({"step": "Fetch lending rates", "tool": "DeFiLlamaAPI"})
        elif tool["name"] == "TheGraphQuery":
            execution_steps.append({"step": "Query historical data", "tool": "TheGraphQuery"})
        elif tool["name"] == "SpaceAndTimeDB":
            execution_steps.append({"step": "Analyze with quant model", "tool": "SpaceAndTimeDB"})
    
    # Format the execution request according to MCP protocol
    execution_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "DeFiLendingStrategy",
            "arguments": {
                "tools": [t["name"] for t in selected_tools],
                "executionSteps": execution_steps
            }
        }
    }
    
    # Submit execution request
    # In production, this would call the mech client
    # Here we simulate a response
    response = {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "requestId": f"0x{''.join([format(x, '02x') for x in os.urandom(32)])}",
            "operator": f"0x{''.join([format(x, '02x') for x in os.urandom(20)])}",
            "promptLoaded": True,
            "onchainRequestCreated": True
        }
    }
    
    return response["result"], execution_steps


def check_execution_status(request_id, execution_steps):
    """Check the status of execution steps."""
    # In production, this would query the actual status
    # Here we simulate progress based on elapsed time
    import time
    
    elapsed = time.time() - st.session_state.get("execution_start_time", time.time())
    
    updated_steps = []
    for i, step in enumerate(execution_steps):
        if elapsed < 10:  # First 10 seconds
            status = "completed" if i == 0 else "pending"
            if i == 0:
                status = "completed"
            elif i == 1:
                status = "in_progress" 
            else:
                status = "pending"
        elif elapsed < 20:  # Next 10 seconds
            status = "completed" if i <= 1 else "pending"
            if i == 2:
                status = "in_progress"
        else:  # After 20 seconds
            status = "completed"
        
        updated_steps.append({**step, "status": status})
    
    # Determine overall status
    all_completed = all(step["status"] == "completed" for step in updated_steps)
    overall_status = "completed" if all_completed else "in_progress"
    
    return updated_steps, overall_status
```

#### UI Components

```python
def execution_ui():
    st.title("Execution Progress")
    st.write("Monitoring the execution of your strategy analysis")
    
    if "execution_info" not in st.session_state:
        import time
        # Start execution
        execution_info, execution_steps = start_execution(
            st.session_state.payment_tx_hash,
            st.session_state.selected_tools
        )
        st.session_state.execution_info = execution_info
        st.session_state.execution_steps = execution_steps
        st.session_state.execution_start_time = time.time()
    
    # Display execution information
    st.subheader("Execution Details")
    st.write(f"Request ID: {st.session_state.execution_info['requestId']}")
    st.write(f"Operator: {st.session_state.execution_info['operator']}")
    
    # Check and update execution status
    updated_steps, overall_status = check_execution_status(
        st.session_state.execution_info["requestId"],
        st.session_state.execution_steps
    )
    
    # Display steps with status
    st.subheader("Execution Steps")
    for step in updated_steps:
        status_emoji = {
            "pending": "⏱️",
            "in_progress": "⏳",
            "completed": "✅"
        }.get(step["status"], "❓")
        
        st.write(f"{status_emoji} {step['step']} ({step['tool']})")
    
    # Progress bar
    completed_steps = len([s for s in updated_steps if s["status"] == "completed"])
    total_steps = len(updated_steps)
    progress = completed_steps / total_steps
    
    st.progress(progress)
    
    # Auto-refresh
    st.button("Refresh Status")
    
    if overall_status == "completed":
        st.success("Execution completed!")
        if st.button("View Results"):
            st.session_state.step = "results"
```

### 5. Verification and Results Display

**User Goal:** View verified results of the analysis.

#### Implementation Details

```python
def get_execution_results(request_id):
    """Get and verify execution results."""
    # In production, this would fetch actual results from operators
    # Here we simulate results
    results = [
        {
            "requestId": request_id,
            "operator": st.session_state.execution_info["operator"],
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Based on our analysis of current market conditions and historical data, we recommend using Aave for your lending strategy. Aave offers the best combination of risk and reward, with a current APY of 5.2% for stablecoin deposits. This rate is 0.8% higher than Compound and 1.2% higher than Maker for similar risk profiles."
                    }
                ],
                "isError": False
            },
            "signature": f"0x{''.join([format(x, '02x') for x in os.urandom(65)])}"
        }
    ]
    
    # Verify results (in production, implement proper verification logic)
    verified_result = {
        "platform": "Aave",
        "apy": 5.2,
        "risk_level": "Low",
        "tvl": "$6.5B",
        "confidence": 0.92,
        "recommendation": results[0]["result"]["content"][0]["text"]
    }
    
    return verified_result


def implement_slashing_mechanism(request_id, results):
    """Implement slashing for incorrect or fraudulent results."""
    # In production, this would interact with a slashing contract
    # Here we simply demonstrate the concept
    
    # Example slashing condition: APY deviation >10%
    baseline_apy = 5.2  # From first operator
    
    slashed_operators = []
    for i, result in enumerate(results[1:], 1):
        try:
            result_text = result["result"]["content"][0]["text"]
            # Extract APY using regex (simplistic)
            import re
            apy_match = re.search(r'(\d+\.?\d*)%', result_text)
            if apy_match:
                reported_apy = float(apy_match.group(1))
                if abs(reported_apy - baseline_apy) / baseline_apy > 0.1:  # >10% deviation
                    slashed_operators.append(result["operator"])
        except (KeyError, IndexError):
            # Malformed result structure
            slashed_operators.append(result["operator"])
    
    return slashed_operators
```

#### UI Components

```python
def results_ui():
    st.title("Strategy Results")
    st.write("Your personalized lending strategy recommendation")
    
    if "verified_result" not in st.session_state:
        # Get and verify results
        verified_result = get_execution_results(
            st.session_state.execution_info["requestId"]
        )
        st.session_state.verified_result = verified_result
    
    # Display main result
    st.subheader(f"Best Strategy: {st.session_state.verified_result['platform']}")
    
    # Create key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Expected APY", f"{st.session_state.verified_result['apy']}%")
    with col2:
        st.metric("Risk Level", st.session_state.verified_result['risk_level'])
    with col3:
        st.metric("Total Value Locked", st.session_state.verified_result['tvl'])
    
    # Display recommendation text
    st.subheader("Recommendation")
    st.write(st.session_state.verified_result['recommendation'])
    
    # Verification confidence
    st.subheader("Verification")
    st.write(f"Confidence score: {st.session_state.verified_result['confidence']:.2f}")
    
    # User feedback on result quality
    st.subheader("Feedback")
    quality_rating = st.slider(
        "Rate the quality of this result", 
        min_value=1, 
        max_value=5, 
        value=4
    )
    
    if st.button("Submit Feedback"):
        # In production, save this feedback
        st.success("Thank you for your feedback!")
    
    # Create a new request button
    if st.button("Create New Request"):
        # Reset session state for new request
        for key in ['prompt', 'tx_hash', 'payment_tx_hash', 'selected_tools', 
                   'execution_info', 'execution_steps', 'verified_result']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.step = "request"
        st.rerun()
```

## Main Application Flow

```python
def main():
    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = "request"
    
    # Display current step
    current_step = st.session_state.step
    
    # Progress indicator
    steps = ["request", "tool_selection", "execution", "results"]
    step_names = ["Create Request", "Tool Selection", "Execution", "Results"]
    
    st.sidebar.progress(steps.index(current_step) / (len(steps) - 1))
    st.sidebar.write(f"Current step: {step_names[steps.index(current_step)]}")
    
    # Display the appropriate UI based on the current step
    if current_step == "request":
        request_ui()
    elif current_step == "tool_selection":
        tool_selection_ui()
    elif current_step == "execution":
        execution_ui()
    elif current_step == "results":
        results_ui()

if __name__ == "__main__":
    main()
```

## Integration with Olas Mech Services

This implementation interfaces with Olas mech services available on the Gnosis Chain. The current list of active mechs includes:

| Service ID | Description                                                          | Mech Address                                 |
|------------|----------------------------------------------------------------------|----------------------------------------------|
| 1815       | AI tasks requested on-chain with results delivered to the requester  | 0x478ad20ed958dcc5ad4aba6f4e4cc51e07a840e4  |
| 1961       | AI tasks requested on-chain with results delivered to the requester  | 0xf2574ffbadf37afc878616b8b2f77fa1d20bb4b4  |
| 1966       | AI tasks requested on-chain with results delivered to the requester  | 0x895c50590a516b451668a620a9ef9b8286b9e72d  |
| 1983       | AI tasks requested on-chain with results delivered to the requester  | 0xce90357349f87b72dbca6078a0ebf39fddd417fa  |
| 1999       | Mech for useful tools                                                | 0xa61026515b701c9a123b0587fd601857f368127a  |
| 2010       | A Mech using Nevermined subscriptions for payments                   | 0x61b962bf1cf91224b0967c7e726c8ce597569983  |

## Dependencies and Setup

Required Python packages:
```
streamlit>=1.24.0
web3>=6.0.0
hexbytes
eth-account
safe-eth-py
python-dotenv
requests
pydantic
pandas
mech_client
```

Environment variables:
```
RPC_URL=https://rpc.gnosischain.com
MECH_MARKETPLACE=0x4554fE75c1f5576c1d7F765B2A036c199Adae329
WEB3_PRIVATE_KEY=your_private_key_here  # For testing only, use secure key management in production
```

## Deployment and Scaling

1. **Development Environment**:
   - Set up a local development environment with Streamlit
   - Use mock responses for testing

2. **Staging Environment**:
   - Deploy to a staging server
   - Connect to a test Gnosis Chain node
   - Integrate with test instances of Olas mech services

3. **Production Environment**:
   - Deploy using containerization (Docker + Kubernetes)
   - Implement auto-scaling based on usage
   - Set up monitoring and logging
   - Implement high availability with redundant components

## Security Considerations

1. **Secure Key Management**:
   - Use proper key management systems, never hardcode private keys
   - Implement a secure wallet connection flow

2. **Data Protection**:
   - Encrypt sensitive data at rest and in transit
   - Implement proper access controls

3. **Transaction Security**:
   - Implement transaction signing confirmation
   - Set up gas limits and other safeguards

4. **Smart Contract Auditing**:
   - Ensure all interacting contracts are audited
   - Test extensively on testnets before mainnet deployment

## Future Enhancements

1. **Advanced RAG Pipeline**:
   - Implement vector-based retrieval for better tool selection
   - Use LLMs for more intelligent query parsing

2. **Multi-Chain Support**:
   - Extend beyond Gnosis Chain to support additional networks

3. **Enhanced Verification**:
   - Implement more sophisticated verification algorithms
   - Support human-in-the-loop verification for critical cases

4. **Dynamic Pricing**:
   - Implement demand-based pricing using oracles
   - Support multiple payment tokens

5. **Result Aggregation**:
   - Implement advanced techniques for combining results from multiple operators
   - Improve conflict resolution between divergent results 
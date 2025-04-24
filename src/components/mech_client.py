import streamlit as st
import subprocess
import shlex
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

def mech_client_workflow():
    """
    Component for Mech Client workflow that:
    1. Accepts a user prompt
    2. Uses LLM to automatically select the best tool
    3. Shows a staking button (0.001 OLAS)
    4. On click, runs mechx interact with the selected tool
    5. Streams output logs to the UI
    """
    st.markdown("""
    <h2>Mech Client: On-Chain AI Request</h2>
    <p>Enter your prompt, let the AI select the best tool, and execute the request on-chain.</p>
    """, unsafe_allow_html=True)
    
    prompt = st.text_area("Prompt", placeholder="Enter your AI task prompt here...")
    agent_id = 6  # Default for your use case
    chain_config = "gnosis"
    private_key_path = "./ethereum_private_key.txt"
    confirm_type = "on-chain"
    
    # Example available tools for agent 6 (could be fetched dynamically)
    available_tools = [
        "prediction-request-rag",
        "prediction-request-reasoning",
        "superforcaster",
        "prediction-offline",
        "prediction-online",
        "prediction-offline-sme",
        "prediction-online-sme"
    ]
    
    # Step 1: Use LLM to select the best tool
    selected_tool = None
    if prompt:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        reasoning_prompt = ChatPromptTemplate.from_template(
            """You are an expert AI agent. Given the following user prompt and the available tools, select the best tool for the task.\n\nUser Prompt: {prompt}\nAvailable Tools: {tools}\n\nRespond ONLY with the tool name from the list that is the best fit."""
        )
        chain = reasoning_prompt | llm
        tool_response = chain.invoke({"prompt": prompt, "tools": ", ".join(available_tools)})
        
        # Extract the tool name from the LLM response
        for tool in available_tools:
            if tool in tool_response.content:
                selected_tool = tool
                break
        if not selected_tool:
            selected_tool = available_tools[0]  # fallback
        st.success(f"Selected Tool: {selected_tool}")
    else:
        st.info("Enter a prompt to select a tool.")
        return
    
    # Step 2: Show staking button
    if st.button("Amount Staked: 0.001 OLAS (Click to Execute)"):
        st.info(f"Running Mech request with tool: {selected_tool} ... streaming output below:")
        
        # Build the mechx command
        cmd = f"mechx interact {shlex.quote(prompt)} --agent_id {agent_id} --key {shlex.quote(private_key_path)} --tool {shlex.quote(selected_tool)} --chain-config {shlex.quote(chain_config)} --confirm {shlex.quote(confirm_type)}"
        
        # Run subprocess and stream output
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output_box = st.empty()
        output_lines = []
        
        for line in process.stdout:
            output_lines.append(line.rstrip())
            output_box.code("\n".join(output_lines), language="bash")
        
        process.stdout.close()
        process.wait()
        st.success("Mech request complete.")

def mech_client_interact_ui():
    """
    Component for advanced Mech Client interaction allowing:
    1. Custom selection of tool and agent
    2. Fetching available tools from mechx CLI
    3. Streaming subprocess output to the UI
    """
    st.markdown("""
    <h2>Mech Client: Submit On-Chain AI Request</h2>
    <p>Enter your prompt, select an agent and tool, and stream the result from the Mech network.</p>
    """, unsafe_allow_html=True)
    
    prompt = st.text_area("Prompt", placeholder="Enter your AI task prompt here...")
    agent_id = st.selectbox("Agent ID", options=[3, 6], index=0)
    chain_config = st.text_input("Chain Config", value="gnosis")
    private_key_path = st.text_input("Private Key File Path", value="./ethereum_private_key.txt")
    confirm_type = st.selectbox("Confirmation Type", options=["on-chain", "off-chain", "wait-for-both"], index=0)

    # Step 1: Fetch available tools for the agent
    tool_options = []
    if st.button("Fetch Tools for Agent"):
        try:
            # Use the CLI to fetch tools for the agent
            cmd = f"mechx tools-for-agents --agent-id {agent_id} --chain-config {chain_config}"
            proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate(timeout=30)
            
            # Parse tool names from the output table
            tool_options = []
            for line in stdout.splitlines():
                if "|" in line and str(agent_id) in line:
                    parts = [x.strip() for x in line.split("|") if x.strip()]
                    if len(parts) >= 3:
                        tool_options.append(parts[1])
            
            if not tool_options:
                st.warning("No tools found for this agent.")
            else:
                st.session_state["mech_tool_options"] = tool_options
        except Exception as e:
            st.error(f"Error fetching tools: {e}")

    # Step 2: Let user select tool
    tool_options = st.session_state.get("mech_tool_options", [])
    selected_tool = st.selectbox("Select Tool", options=tool_options) if tool_options else st.text_input("Tool Name (manual entry)")

    # Step 3: Submit request and stream output
    if st.button("Submit Mech Request") and prompt and (selected_tool or tool_options):
        st.info("Submitting request to Mech... streaming output below:")
        cmd = f"mechx interact {shlex.quote(prompt)} --agent_id {agent_id} --key {shlex.quote(private_key_path)} --tool {shlex.quote(selected_tool)} --chain-config {shlex.quote(chain_config)} --confirm {shlex.quote(confirm_type)}"
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output_box = st.empty()
        output_lines = []
        
        for line in process.stdout:
            output_lines.append(line.rstrip())
            output_box.code("\n".join(output_lines), language="bash")
        
        process.stdout.close()
        process.wait()
        st.success("Mech request complete.")



def submit_mech_request_ui():
    st.markdown("""
    <h2>Submit New Mech Request</h2>
    <p>Send a prompt to a Mech agent on-chain and stream the result below.</p>
    """, unsafe_allow_html=True)
    prompt = st.text_area("Prompt", placeholder="Enter your AI task prompt here...")
    agent_id = st.text_input("Agent ID", placeholder="e.g. 6")
    tool = st.text_input("Tool Name (optional)", placeholder="e.g. openai-gpt-3.5-turbo")
    chain_config = st.text_input("Chain Config (default: gnosis)", value="gnosis")
    private_key_path = st.text_input("Private Key File Path", value="ethereum_private_key.txt")
    submit_btn = st.button("Submit Mech Request")
    output_box = st.empty()
    if submit_btn and prompt and agent_id:
        st.info("Submitting request to Mech... streaming output below:")
        cmd = f"mechx interact {shlex.quote(prompt)} --agent_id {shlex.quote(agent_id)} --chain-config {shlex.quote(chain_config)} --key {shlex.quote(private_key_path)}"
        if tool:
            cmd += f" --tool {shlex.quote(tool)}"
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output_lines = []
        for line in process.stdout:
            output_lines.append(line.rstrip())
            output_box.code("\n".join(output_lines), language="bash")
        process.stdout.close()
        process.wait()
        st.success("Mech request complete.")



def mech_client_interact_ui():
    st.markdown("""
    <h2>Mech Client: Submit On-Chain AI Request</h2>
    <p>Enter your prompt, select an agent and tool, and stream the result from the Mech network.</p>
    """, unsafe_allow_html=True)
    prompt = st.text_area("Prompt", placeholder="Enter your AI task prompt here...")
    agent_id = st.selectbox("Agent ID", options=[3, 6], index=0)
    chain_config = st.text_input("Chain Config", value="gnosis")
    private_key_path = st.text_input("Private Key File Path", value="./ethereum_private_key.txt")
    confirm_type = st.selectbox("Confirmation Type", options=["on-chain", "off-chain", "wait-for-both"], index=0)

    # Step 1: Fetch available tools for the agent
    tool_options = []
    if st.button("Fetch Tools for Agent"):
        try:
            # Use the CLI to fetch tools for the agent
            cmd = f"mechx tools-for-agents --agent-id {agent_id} --chain-config {chain_config}"
            proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate(timeout=30)
            # Parse tool names from the output table
            tool_options = []
            for line in stdout.splitlines():
                if "|" in line and agent_id in line:
                    parts = [x.strip() for x in line.split("|") if x.strip()]
                    if len(parts) >= 3:
                        tool_options.append(parts[1])
            if not tool_options:
                st.warning("No tools found for this agent.")
            else:
                st.session_state["mech_tool_options"] = tool_options
        except Exception as e:
            st.error(f"Error fetching tools: {e}")

    # Step 2: Let user select tool
    tool_options = st.session_state.get("mech_tool_options", [])
    selected_tool = st.selectbox("Select Tool", options=tool_options) if tool_options else st.text_input("Tool Name (manual entry)")

    # Step 3: Submit request and stream output
    if st.button("Submit Mech Request") and prompt and (selected_tool or tool_options):
        st.info("Submitting request to Mech... streaming output below:")
        cmd = f"mechx interact {shlex.quote(prompt)} --agent_id {agent_id} --key {shlex.quote(private_key_path)} --tool {shlex.quote(selected_tool)} --chain-config {shlex.quote(chain_config)} --confirm {shlex.quote(confirm_type)}"
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output_box = st.empty()
        output_lines = []
        for line in process.stdout:
            output_lines.append(line.rstrip())
            output_box.code("\n".join(output_lines), language="bash")
        process.stdout.close()
        process.wait()
        st.success("Mech request complete.")


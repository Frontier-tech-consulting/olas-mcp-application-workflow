import streamlit as st
import shlex
import subprocess
import json

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

def run_mech_job_with_agent_history(
    agent_history_json,
    prompt=None,
    agent_id="6",
    tool=None,
    chain_config="gnosis",
    private_key_path="ethereum_private_key.txt",
    confirm_type="on-chain",
):
    """
    Run a Mech client job using the actual CLI, passing the extracted content from AgentHistoryList as the prompt.
    Returns the parsed output (dict or string).
    """
    import tempfile
    import os
    import shlex
    import subprocess
    import streamlit as st
    # 1. Extract content from AgentHistoryList
    steps = agent_history_json
    extracted_contents = []
    
    # 2. Write the prompt to a temp file if needed (or pass as arg)
    mech_prompt = steps
    # 3. Build the mechx interact command
    cmd = f"mechx interact {shlex.quote(mech_prompt)} --agent_id {shlex.quote(str(agent_id))} --chain-config {shlex.quote(chain_config)} --key {shlex.quote(private_key_path)} --confirm {shlex.quote(confirm_type)}"
    if tool:
        cmd += f" --tool {shlex.quote(tool)}"
    st.info(f"Running Mech job: `{cmd}`")
    # 4. Run the command and stream output
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    output_lines = []
    output_box = st.empty()
    for line in process.stdout:
        output_lines.append(line.rstrip())
        output_box.code("\n".join(output_lines), language="bash")
    process.stdout.close()
    process.wait()
    st.success("Mech job complete.")
    # 5. Try to parse the last JSON object in the output (if any)
    mech_result = None
    for line in reversed(output_lines):
        try:
            parsed = json.loads(line)
            mech_result = parsed
            break
        except Exception:
            continue
    if mech_result:
        st.json(mech_result)
    else:
        st.info("Raw Mech output:")
        st.code("\n".join(output_lines), language="bash")
    return mech_result or output_lines


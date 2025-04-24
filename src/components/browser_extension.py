import streamlit as st
import json
import subprocess
import shlex

def browser_extension_workflow():
    st.markdown("""
    <h2 style='text-align:center;'>MCP browser </h2>
    <p style='text-align:center;'>Configure and run browser automation tasks using the MCP browser agent.</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        headless = st.checkbox("Run in headless mode", value=True)
        additional_details = st.text_area("Additional Details", placeholder="Provide any extra details for the automation task...", height=80)
    with col2:
        steps = st.text_area("Automation Steps / Context", placeholder="Describe the browser automation steps or context here...", height=120)
    
    scrollable_browser_output = st.empty()
    if st.button("Back to Main Page", key="back_to_mainpage"):
        st.session_state.page = 'app_storefront'
        st.rerun()
    if st.button("Run Automation (Stream Output)"):
        st.info("Streaming browser-use output... (see below)")
        payload = {
            "task": steps or "Open google.com and search for OLAS.",
            "headless": headless,
            "steps": steps,
            "context": steps,
            "additional_details": additional_details
        }
        browser_chunks = []
        try:
            curl_cmd = f"curl -N -X POST -H 'Content-Type: application/json' --data '{json.dumps(payload)}' http://localhost:8888/browser-automation-stream"
            process = subprocess.Popen(shlex.split(curl_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            for line in process.stdout:
                if line.strip():
                    try:
                        if line.startswith("data: "):
                            data = json.loads(line.replace("data: ", "").strip())
                            if data.get("type") == "browser-use":
                                chunk = data.get("output")
                                browser_chunks.append(str(chunk))
                                scrollable_browser_output.markdown(
                                    f"<div style='max-height:300px;overflow-y:auto;background:#f8f8f8;padding:10px;border-radius:6px;font-family:monospace;font-size:0.95em;'>{'<br>'.join(browser_chunks)}</div>",
                                    unsafe_allow_html=True
                                )
                            elif data.get("type") == "done":
                                st.success("Streaming complete.")
                                break
                    except Exception as e:
                        st.warning(f"Stream parse error: {e}")
            process.stdout.close()
            process.wait()
        except Exception as e:
            st.error(f"Streaming error: {e}")
    if st.session_state.get("browser_mcp_result"):
        st.markdown("---")
        st.markdown("**Automation Result:**")
        st.text_area("Result", st.session_state.browser_mcp_result, height=200)

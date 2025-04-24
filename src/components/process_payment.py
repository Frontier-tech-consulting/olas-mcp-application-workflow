import streamlit as st
import time

def process_payment(request):
    """
    Process payment for a service request
    
    This function simulates a blockchain transaction with progress updates
    
    Args:
        request: The request object containing services and cost
    """
    # Set initial payment state if not already done
    if 'payment_step' not in st.session_state:
        st.session_state.payment_step = 0
    
    if 'payment_messages' not in st.session_state:
        st.session_state.payment_messages = []
    
    # Steps in payment process
    steps = [
        "Creating transaction...",
        "Submitting to Gnosis Safe...",
        "Broadcasting to blockchain network...",
        "Waiting for block inclusion...",
        "Transaction confirmed!"
    ]
    
    # Get current step
    current_step = st.session_state.payment_step
    
    # Display payment processing UI
    st.markdown("### Processing Payment")
    
    # Show progress bar
    if current_step < len(steps) - 1:
        progress = (current_step + 1) / len(steps)
        st.progress(progress)
    else:
        st.progress(1.0)
    
    # Display current step
    if current_step < len(steps):
        st.markdown(f"**Status:** {steps[current_step]}")
    
    # Log message for this step if new
    if len(st.session_state.payment_messages) <= current_step:
        if current_step == 0:
            message = f"Creating transaction to send {request.get('total_cost', 0)} OLAS from your Gnosis Safe"
        elif current_step == 1:
            message = "Requesting signature from Gnosis Safe wallet"
        elif current_step == 2:
            message = f"Transaction hash: {request.get('transaction_id', '0xdd9b42c0f72fbda6b01746b10e2e2bd4506819c65b156e2817f0b9c0e5f5d86a')}"
        elif current_step == 3:
            message = "Estimated confirmation time: 15-30 seconds"
        else:
            message = "Payment successful! Your request is now being processed."
        
        st.session_state.payment_messages.append(message)
    
    # Show all messages so far
    for msg in st.session_state.payment_messages:
        st.info(msg)
    
    # Advance to next step after delay
    if current_step < len(steps) - 1:
        # Simulate blockchain confirmation times with appropriate delays
        if current_step == 3:  # Waiting for block inclusion is longest step
            time.sleep(10)  # 10 seconds for block confirmation
        else:
            time.sleep(3)  # 3 seconds for other steps
        
        st.session_state.payment_step += 1
        st.rerun()
    else:
        # Payment complete, wait briefly then set payment completed
        time.sleep(3)
        st.session_state.payment_processing = False
        st.session_state.payment_completed = True
        st.session_state.payment_step = 0
        st.session_state.payment_messages = []
        st.rerun()
    

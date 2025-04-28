# src/components/execution_status.py
import streamlit as st
import time
import random
from typing import Dict, Any, Optional, Callable
import pandas as pd
from datetime import datetime, timedelta

class ExecutionStatus:
    """Component for displaying execution status and collecting feedback."""
    
    def __init__(self, on_new_request: Optional[Callable] = None):
        """
        Initialize the execution status component.
        
        Args:
            on_new_request: Callback function when user clicks "New Request"
        """
        self.on_new_request = on_new_request
        
        # Initialize feedback history in session state
        if "result_feedback_history" not in st.session_state:
            st.session_state.result_feedback_history = []
    
    def render(self):
        """Render the execution status component."""
        st.markdown("## Execution Status")
        
        # Get the current request from session state
        request = st.session_state.get("request", None)
        
        if not request:
            st.error("No active request found. Please create a request first.")
            if st.button("Back to Request Form", use_container_width=True):
                if self.on_new_request:
                    self.on_new_request()
                else:
                    st.session_state.page = "create_request"
                    st.rerun()
            return
        
        # Display request details
        self._display_request_details(request)
        
        # Display execution steps
        self._display_execution_steps(request)
        
        # Allow refreshing status
        self._display_refresh_controls(request)
        
        # Display final result if execution is complete
        self._display_final_result(request)
    
    def _display_request_details(self, request):
        """Display request details."""
        st.markdown("### Request Details")
        
        # Create columns for different details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Prompt:** {request.get('prompt', 'N/A')}")
            
            # Get selected services
            selected_services = request.get("selected_services", [])
            st.markdown(f"**Services Selected:** {len(selected_services)}")
        
        with col2:
            # Show timestamp if available
            if "timestamp" in request:
                st.markdown(f"**Submitted:** {request.get('timestamp', 'N/A')}")
            
            # Show transaction ID if available
            if "transaction_id" in request:
                tx_id = request.get("transaction_id")
                st.markdown(f"**Transaction ID:** [{tx_id[:10]}...{tx_id[-6:]}](https://gnosisscan.io/tx/{tx_id})")
            
            # Show total cost
            st.markdown(f"**Total Cost:** {request.get('total_cost', 0):.3f} xDAI")
    
    def _display_execution_steps(self, request):
        """Display execution steps."""
        st.markdown("### Execution Progress")
        
        # Get execution steps
        execution_steps = request.get("execution_steps", [])
        
        if not execution_steps:
            st.warning("No execution steps found.")
            return
        
        # Update execution steps based on time
        updated_steps = self._update_execution_steps(execution_steps)
        
        # Calculate progress
        completed = sum(1 for step in updated_steps if step.get("status") == "completed")
        in_progress = sum(1 for step in updated_steps if step.get("status") == "in_progress")
        total_steps = len(updated_steps)
        
        # Show progress bar
        if total_steps > 0:
            progress_value = (completed + 0.5 * in_progress) / total_steps
            st.progress(progress_value)
        
        # Display each step
        for i, step in enumerate(updated_steps):
            step_name = step.get("step", f"Step {i+1}")
            status = step.get("status", "pending")
            
            # Use icons to indicate status
            if status == "completed":
                icon = "✅"
            elif status == "in_progress":
                icon = "⏳"
            elif status == "error":
                icon = "❌"
            else:
                icon = "⏱️"
            
            st.markdown(f"{icon} **{step_name}** - _{status.title()}_")
            
            # If step has result, show it in an expander
            if status in ["completed", "in_progress"] and "result" in step:
                with st.expander("Result" if status == "completed" else "Partial Result"):
                    st.write(step["result"])
        
        # Store updated steps back in request
        request["execution_steps"] = updated_steps
        
        # Update session state
        st.session_state.request = request
    
    def _update_execution_steps(self, steps):
        """Update execution steps based on elapsed time."""
        # Get current auto-refresh setting
        auto_refresh = st.session_state.get("auto_refresh", False)
        
        # If not auto-refreshing, only update steps on manual refresh
        if not auto_refresh and not st.session_state.get("manual_refresh", False):
            return steps
        
        # Reset manual refresh flag
        st.session_state.manual_refresh = False
        
        # Create a copy of steps to modify
        updated_steps = steps.copy()
        
        # Find the first non-completed step
        next_step_index = next((i for i, step in enumerate(updated_steps) 
                               if step.get("status") != "completed"), None)
        
        # If all steps are completed or no steps found, return unchanged
        if next_step_index is None:
            return updated_steps
        
        # Update the next step to in-progress if it's pending
        if updated_steps[next_step_index].get("status") == "pending":
            updated_steps[next_step_index]["status"] = "in_progress"
            updated_steps[next_step_index]["start_time"] = time.time()
            return updated_steps
        
        # If the step is already in progress, check if it should be completed
        if updated_steps[next_step_index].get("status") == "in_progress":
            # Check if step has been in progress long enough (3-7 seconds)
            start_time = updated_steps[next_step_index].get("start_time", 0)
            elapsed = time.time() - start_time
            
            # Determine completion time based on step index (later steps take longer)
            completion_time = 3 + (next_step_index * 0.5)
            
            if elapsed >= completion_time:
                # Generate a result for the step
                step_name = updated_steps[next_step_index].get("step", "")
                tool_name = updated_steps[next_step_index].get("tool", "")
                
                if "Verification" in step_name or "Verification" in tool_name:
                    result = "All results verified successfully. Confidence score: 0.92"
                else:
                    result = self._generate_mock_result(step_name, tool_name)
                
                # Mark the step as completed with a result
                updated_steps[next_step_index]["status"] = "completed"
                updated_steps[next_step_index]["result"] = result
                updated_steps[next_step_index]["end_time"] = time.time()
        
        return updated_steps
    
    def _generate_mock_result(self, step_name, tool_name):
        """Generate a mock result based on the step and tool names."""
        if "Technical Analysis" in tool_name:
            return {
                "trend": "bullish" if random.random() > 0.5 else "bearish",
                "indicators": {
                    "RSI": round(random.uniform(30, 70), 2),
                    "MACD": round(random.uniform(-0.5, 0.5), 2),
                    "Moving Average": f"{round(random.uniform(100, 200), 2)} (50-day)",
                    "Support Level": round(random.uniform(900, 1000), 2),
                    "Resistance Level": round(random.uniform(1100, 1200), 2)
                },
                "confidence": round(random.uniform(0.7, 0.95), 2)
            }
        elif "Fundamental Analysis" in tool_name:
            return {
                "market_cap": f"${round(random.uniform(1, 100), 2)}B",
                "trading_volume": f"${round(random.uniform(100, 1000), 2)}M",
                "tokenomics": {
                    "total_supply": f"{round(random.uniform(10, 100), 2)}M",
                    "circulating_supply": f"{round(random.uniform(5, 50), 2)}M",
                    "token_utility": random.choice(["Governance", "Utility", "Payment", "Security"])
                },
                "risk_score": round(random.uniform(3, 8), 1),
                "recommendation": random.choice(["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"])
            }
        else:
            # Generic result
            return f"Completed analysis of {tool_name}. Found relevant insights that will contribute to the final result."
    
    def _display_refresh_controls(self, request):
        """Display refresh controls."""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Refresh Status", use_container_width=True):
                st.session_state.manual_refresh = True
                st.rerun()
        
        with col2:
            # Determine if auto-refresh should be shown
            execution_steps = request.get("execution_steps", [])
            all_completed = all(step.get("status") == "completed" for step in execution_steps)
            
            if not all_completed:
                auto_refresh = st.toggle("Auto Refresh", value=st.session_state.get("auto_refresh", False))
                st.session_state.auto_refresh = auto_refresh
                
                if auto_refresh:
                    time.sleep(2)  # Wait for 2 seconds before refreshing
                    st.rerun()
    
    def _display_final_result(self, request):
        """Display final result if execution is complete with feedback option."""
        # Get execution steps
        execution_steps = request.get("execution_steps", [])
        
        # Check if all steps are completed
        all_completed = all(step.get("status") == "completed" for step in execution_steps)
        
        if all_completed and execution_steps:
            st.markdown("### Final Result")
            
            # Simulate aggregating results from all steps
            step_results = [step.get("result") for step in execution_steps if "result" in step]
            
            # Generate a final result based on the individual step results
            final_result = self._generate_final_result(request.get("prompt", ""), step_results)
            
            # Display the final result
            st.markdown("#### Best Strategy")
            st.markdown(final_result.get("best_strategy", "No clear strategy found."))
            
            # Display metrics in columns
            metrics = final_result.get("metrics", {})
            if metrics:
                cols = st.columns(len(metrics))
                for i, (metric_name, metric_value) in enumerate(metrics.items()):
                    cols[i].metric(metric_name, metric_value)
            
            # Display additional information
            st.markdown("#### Recommendation")
            st.markdown(final_result.get("recommendation", ""))
            
            # Display confidence score
            confidence = final_result.get("confidence", 0.8)
            st.progress(confidence)
            st.caption(f"Confidence Score: {confidence:.2f}")
            
            # Save feedback function for the final result
            def save_result_feedback():
                feedback_value = st.session_state.get("result_feedback", None)
                if feedback_value is not None:
                    # Add to history
                    st.session_state.result_feedback_history.append({
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "request_id": request.get("request_id", "unknown"),
                        "feedback": feedback_value
                    })
                    
                    # Display a toast notification
                    feedback_type = "👍 Positive" if feedback_value > 0 else "👎 Negative"
                    st.toast(f"Thanks for your {feedback_type} feedback on the result!", icon="🎯")
            
            # Display feedback component for the final result
            st.markdown("#### Was this result helpful?")
            
            # Get previous feedback from session state
            previous_feedback = next(
                (item["feedback"] for item in st.session_state.result_feedback_history 
                if item.get("request_id") == request.get("request_id")),
                None
            )
            
            # Set the session state variable for this feedback widget
            st.session_state["result_feedback"] = previous_feedback
            
            # Add feedback widget
            st.feedback(
                "thumbs",
                key="result_feedback",
                on_change=save_result_feedback
            )
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("View Detailed Report", use_container_width=True):
                    # In a real app, this would navigate to a detailed report view
                    st.info("Detailed report would be displayed here.")
            
            with col2:
                if st.button("New Request", use_container_width=True):
                    # Reset relevant session state
                    for key in ["request", "prompt", "reasoning_complete", "selected_services"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Navigate to create request page
                    if self.on_new_request:
                        self.on_new_request()
                    else:
                        st.session_state.page = "create_request"
                        st.rerun()
    
    def _generate_final_result(self, prompt, step_results):
        """Generate a final aggregated result."""
        # For a realistic mock, we'll create a strategy analysis result
        prompt_lower = prompt.lower()
        
        # Determine what type of analysis this is
        if any(kw in prompt_lower for kw in ["yield", "apy", "interest", "earn"]):
            strategy_type = "Yield Optimization"
            best_strategy = random.choice([
                "Provide liquidity to Uniswap V3 DAI/USDC pool and stake LP tokens in the Olas Farm",
                "Deposit stablecoins into Aave for lending APY and borrow against them for leveraged yield",
                "Stake ETH in the Rocket Pool for liquid staking rewards",
                "Use Curve's stablecoin pools combined with Convex to maximize CRV and CVX rewards"
            ])
            metrics = {
                "Estimated APY": f"{round(random.uniform(3, 25), 2)}%",
                "Risk Level": random.choice(["Low", "Medium", "High"]),
                "Gas Costs": f"${round(random.uniform(5, 50), 2)}",
                "Lockup Period": random.choice(["None", "7 days", "30 days"])
            }
        elif any(kw in prompt_lower for kw in ["trend", "price", "chart", "technical"]):
            strategy_type = "Trading Strategy"
            best_strategy = random.choice([
                "Accumulate at support level with stop-loss 5% below entry",
                "Wait for confirmation of trend reversal before entering position",
                "Implement a dollar-cost averaging strategy over the next 30 days",
                "Enter position with 40% capital now, add remaining positions on pullbacks"
            ])
            metrics = {
                "Entry Price": f"${round(random.uniform(900, 1100), 2)}",
                "Target Price": f"${round(random.uniform(1200, 1500), 2)}",
                "Stop Loss": f"${round(random.uniform(800, 900), 2)}",
                "Time Horizon": random.choice(["Short-term", "Medium-term", "Long-term"])
            }
        else:
            strategy_type = "Portfolio Management"
            best_strategy = random.choice([
                "Diversify holdings with 40% large caps, 30% mid caps, 20% small caps, and 10% stablecoins",
                "Focus on layer-1 protocols with strong developer activity and growing TVL",
                "Maintain a 60% core position with 40% tactical allocation for market opportunities",
                "Implement a barbell strategy with stablecoins and high-conviction altcoins"
            ])
            metrics = {
                "Risk-Adjusted Return": f"{round(random.uniform(0.5, 2.5), 2)}",
                "Volatility": f"{round(random.uniform(30, 80), 2)}%",
                "Drawdown Protection": random.choice(["Strong", "Moderate", "Limited"]),
                "Rebalance Period": random.choice(["Weekly", "Monthly", "Quarterly"])
            }
        
        # Generate a recommendation based on the strategy type
        recommendations = {
            "Yield Optimization": "Consider the liquidity and withdrawal terms before committing funds. Monitor protocol changes and governance proposals that could impact rewards.",
            "Trading Strategy": "Set firm entry and exit points. Consider using limit orders to automatically execute at target prices and prevent emotional trading decisions.",
            "Portfolio Management": "Regular rebalancing is key to maintaining your target allocation. Consider tax implications of frequent trading and focus on long-term portfolio health."
        }
        
        # Generate a final confidence score
        confidence = round(random.uniform(0.75, 0.95), 2)
        
        return {
            "strategy_type": strategy_type,
            "best_strategy": best_strategy,
            "metrics": metrics,
            "recommendation": recommendations.get(strategy_type, "Implement the strategy with proper risk management."),
            "confidence": confidence
        }

def generate_mock_agent_daa_data(days: int = 30):
    """Generate mock daily active agent (DAA) data for the past N days."""
    today = datetime.utcnow().date()
    data = []
    for i in range(days):
        date = today - timedelta(days=days - i - 1)
        daa = random.randint(15, 120)  # Number of daily active agents
        data.append({"date": date, "DAA": daa})
    return pd.DataFrame(data)

def generate_mock_usecase_data():
    """Generate mock use case distribution data."""
    use_cases = [
        "Prediction",
        "Optimization",
        "Portfolio Management",
        "Trading",
        "Yield Farming",
        "Analytics",
        "Automation"
    ]
    proportions = [random.uniform(0.05, 0.25) for _ in use_cases]
    total = sum(proportions)
    proportions = [p / total for p in proportions]
    data = [{"use_case": uc, "proportion": p} for uc, p in zip(use_cases, proportions)]
    return pd.DataFrame(data)
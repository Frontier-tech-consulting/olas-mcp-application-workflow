import streamlit as st
import time
import random
import uuid
from datetime import datetime, timedelta
import traceback
import json
import re
import os
import sys
import pandas as pd
import copy
from langchain.schema.output_parser import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Import utility functions from the utils folder
from src.utils.execution_utils import (
    deep_copy_request, 
    generate_random_transaction_id, 
    get_service_name, 
    generate_pipeline_steps, 
    get_default_pipeline_steps,
    generate_fallback_steps,
    determine_result_type, 
    generate_mock_data_for_defillama, 
    format_eth_address
)
from src.utils.data_generators import (
    generate_analytics_result,
    generate_prediction_result, 
    generate_token_result, 
    generate_data_feed_result, 
    generate_optimization_result
)

class ExecutionStatus:
    """Component that displays the execution status of a service request"""
    
    def __init__(self):
        """Initialize execution status component"""
        # Initialize service name mapping
        self.service_name_map = {
            "1722": "DeFi Analytics Service",
            "1815": "Token Price Analysis Service", 
            "1966": "AI Task Execution Service",
            "1961": "AI Task Execution Service",
            "1983": "AI Task Processing Mech",
            "1993": "Task Execution Mech Service",
            "1999": "Yield Farming Optimizer",
            "2010": "Nevermined Subscription Mech"
        }
        
        # Initialize services data
        self.services_data = []
        self.service_map = {}
        self.load_services_data()
        
        # Load request from session state
        self.request = None
        if "request" in st.session_state:
            self.request = st.session_state.request
        elif "current_request" in st.session_state:
            self.request = st.session_state.current_request
            # Also set it in the standard location
            st.session_state.request = self.request
    
    def load_services_data(self):
        """Load services data from session state or JSON file"""
        try:
            # Try to get from session state first
            if 'services' in st.session_state and st.session_state.services:
                self.services = st.session_state.services
            else:
                # Try to load from file if not in session state
                try:
                    with open('enriched_services_data.json', 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "services" in data:
                            self.services = data["services"]
                            # Store in session state for future use
                            st.session_state.services = self.services
                        else:
                            self.services = []
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error loading services data: {str(e)}")
                    self.services = []
        except Exception as e:
            print(f"Error in load_services_data: {str(e)}")
            self.services = []
            
        # Create a map of service ID to full service data for quicker lookups
        self.service_map = {}
        for service in self.services:
            service_id = service.get('service_id')
            if service_id:
                self.service_map[service_id] = service

    def get_service_details(self, service_id):
        """
        Get detailed metadata for a service.
        
        Args:
            service_id: The ID of the service
            
        Returns:
            Dictionary with service details
        """
        # First check if we have it in our service map
        if hasattr(self, 'service_map') and service_id in self.service_map:
            return self.service_map[service_id]
            
        # Next check the full services list
        if hasattr(self, 'services'):
            for service in self.services:
                if service.get('service_id') == service_id or service.get('id') == service_id:
                    return service
        
        # Finally check session state
        if 'services' in st.session_state:
            for service in st.session_state.services:
                if service.get('service_id') == service_id or service.get('id') == service_id:
                    return service
        
        # Return a basic structure if nothing found
        return {
            "service_id": service_id,
            "description": f"Service {service_id}",
            "mech_address": "0x0000000000000000000000000000000000000000",
            "status": "Unknown"
        }
    
    def ensure_transaction(self, request):
        """Ensure the request has a transaction ID, submitting if needed"""
        if not request:
            st.error("No request data available")
            return None
            
        # Make a copy of the request to avoid modifying the original
        request_copy = deep_copy_request(request)
        
        # If transaction hasn't been submitted yet (no TX ID), create one
        tx_id = None
        if isinstance(request_copy, dict):
            tx_id = request_copy.get("transaction_id")
        else:
            tx_id = getattr(request_copy, "transaction_id", None)
            
        if not tx_id:
            # Generate a random transaction hash that looks like Gnosis Chain tx
            tx_hash = generate_random_transaction_id()
            
            # Handle both dictionary and object types
            if isinstance(request_copy, dict):
                request_copy["transaction_id"] = tx_hash
                request_copy["submitted_at"] = datetime.now().isoformat()
            else:
                # Handle Request object type
                try:
                    request_copy.transaction_id = tx_hash
                    request_copy.submitted_at = datetime.now().isoformat()
                except AttributeError:
                    # Convert to dict if attribute setting fails
                    request_copy = {
                        "prompt": getattr(request_copy, "prompt", ""),
                        "selected_services": getattr(request_copy, "selected_services", []),
                        "total_cost": getattr(request_copy, "total_cost", 0),
                        "transaction_id": tx_hash,
                        "submitted_at": datetime.now().isoformat()
                    }
            
            # Add to session state if not already there
            if "submitted_requests" not in st.session_state:
                st.session_state.submitted_requests = []
            
            # Add to submitted requests for history
            st.session_state.submitted_requests.append(deep_copy_request(request_copy))
            
            # Store updated request in session state
            st.session_state.current_request = request_copy
            self.request = request_copy  # Update our instance variable
        
        return tx_id or (request_copy.get("transaction_id") if isinstance(request_copy, dict) 
                         else getattr(request_copy, "transaction_id", None))
    
    def get_service_execution_result(self, service_id):
        """
        Generate execution result for a specific service by checking the defillama data and also adding mcp metrics.
        
        Args:
            service_id: The ID of the service to generate execution result for
            
        Returns:
            Dictionary with mock execution result data
        """
        try:
            # Get service name
            service_name = get_service_name(service_id, service_name_map=self.service_name_map)
            
            # Get request information for context
            request_prompt = ""
            if "request" in st.session_state and st.session_state.request:
                request_prompt = getattr(st.session_state.request, "prompt", "")
                if isinstance(st.session_state.request, dict):
                    request_prompt = st.session_state.request.get("prompt", "")
            
            # Determine the result type based on service name
            result_type = determine_result_type(service_name, "analytics")
            
            # Generate result based on result type
            if result_type == "analytics":
                result = generate_analytics_result(service_name, request_prompt)
            elif result_type == "prediction":
                result = generate_prediction_result(service_name, request_prompt)
            elif result_type == "token":
                result = generate_token_result(service_name, request_prompt)
            elif result_type == "data_feed":
                result = generate_data_feed_result(service_name, request_prompt)
            elif result_type == "optimization":
                result = generate_optimization_result(service_name, request_prompt)
            else:
                # Fallback to analytics if type is unknown
                result = generate_analytics_result(service_name, request_prompt)
            
            # Set the result type explicitly
            result["result_type"] = result_type
            
            # Add execution metadata to the result
            result["service_id"] = service_id
            result["service_name"] = service_name
            result["execution_time"] = f"{random.uniform(1.5, 8.2):.2f} seconds"
            result["timestamp"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            print(f"Error generating service execution result: {str(e)}")
            traceback.print_exc()
            
            # Return a basic error result
            return {
                "result_type": "error",
                "service_id": service_id,
                "service_name": get_service_name(service_id, service_name_map=self.service_name_map),
                "error": str(e)
            }
    
    def get_mock_execution_data(self, request):
        """Generate mock execution data for the request"""
        if not request:
            return None
            
        # Extract service IDs and request text from the request
        service_ids = []
        request_text = ""
        
        try:
            # Extract request_text
            if isinstance(request, dict):
                request_text = request.get('prompt', "")
                services = request.get('selected_services', [])
            else:
                request_text = getattr(request, 'prompt', "")
                services = getattr(request, 'selected_services', [])
                
            # If we don't have a request text, check session state - try all possible locations
            if not request_text:
                if "request_text" in st.session_state:
                    request_text = st.session_state.request_text
                elif "request_textarea" in st.session_state:
                    request_text = st.session_state.request_textarea
                
            print(f"Extracted request text: {request_text}")
                
            # Extract service IDs from the services
            for service in services:
                if isinstance(service, dict):
                    service_id = service.get('id') or service.get('service_id')
                    if service_id:
                        service_ids.append(service_id)
                else:
                    service_id = getattr(service, 'id', None) or getattr(service, 'service_id', None)
                    if service_id:
                        service_ids.append(service_id)
                    
            # Filter out None values
            service_ids = [sid for sid in service_ids if sid]
        except Exception as e:
            st.error(f"Error extracting service IDs and request text: {str(e)}")
            service_ids = []
            
        # Make sure we have at least default service IDs if none were provided
        if not service_ids:
            print("No service IDs found. Using default service IDs.")
            service_ids = ["1722", "1815", "1966", "1983"]
            
        # If we still don't have a request text, use a default
        if not request_text:
            request_text = "Analyze current DeFi market trends and recommend investment strategies"
            print(f"Using default request text: {request_text}")
            
        # Generate pipeline steps using the request text
        pipeline_steps = generate_pipeline_steps(service_ids, request_text)
            
        # Generate execution results for each service using the request text
        execution_results = {}
        
        # Distribute different types of results across the services
        result_types = ["analytics", "prediction", "token", "data_feed", "optimization"]
        result_type_index = 0
        
        for service_id in service_ids:
            # Get the service name to make the output more specific
            service_name = get_service_name(service_id, service_name_map=self.service_name_map)
            
            # Choose a result type based on service name or cycling through types
            result_type = determine_result_type(service_name, result_types[result_type_index % len(result_types)])
            result_type_index += 1
            
            # Generate result based on result type
            if result_type == "analytics":
                result = generate_analytics_result(service_name, request_text)
            elif result_type == "prediction":
                result = generate_prediction_result(service_name, request_text)
            elif result_type == "token":
                result = generate_token_result(service_name, request_text)
            elif result_type == "data_feed":
                result = generate_data_feed_result(service_name, request_text)
            elif result_type == "optimization":
                result = generate_optimization_result(service_name, request_text)
            else:
                # Fallback to analytics if type is unknown
                result = generate_analytics_result(service_name, request_text)
            
            # Set the result type explicitly
            result["result_type"] = result_type
            
            # Add execution metadata to the result
            result["service_id"] = service_id
            result["service_name"] = service_name
            result["execution_time"] = f"{random.uniform(1.5, 8.2):.2f} seconds"
            result["timestamp"] = datetime.now().isoformat()
            
            # Store in the execution results
            execution_results[service_id] = result
                
        # Return the execution data
        return {
            "status": "complete",
            "overall_progress": 1.0,
            "pipeline_steps": pipeline_steps,
            "execution_results": execution_results
        }
    
    def render_service_execution_results(self, execution_results):
        """Render service execution results in the UI"""
        if not execution_results:
            st.info("No service execution results are available yet.")
            return
        
        # Counter for services with results
        results_count = 0
        
        # Iterate through each service result
        for service_id, result in execution_results.items():
            if not result:
                continue
            
            results_count += 1
            
            # Get service name
            service_name = self.get_service_name(service_id)
            
            # Create an expandable section for this service
            with st.expander(f"🔹 **{service_name}** (Service ID: {service_id})", expanded=True):
                # Add metadata if available
                if "metadata" in result:
                    metadata = result["metadata"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"⏱️ Execution time: {metadata.get('execution_time', 'N/A')}")
                    with col2:
                        st.caption(f"📆 Timestamp: {metadata.get('timestamp', 'N/A')}")
                    with col3:
                        st.caption(f"🌐 Source: {metadata.get('source', 'Unknown')}")
                    
                    st.markdown("---")
                
                # Determine result type and render accordingly
                result_type = result.get("result_type", "generic")
                
                try:
                    if result_type == "analytics":
                        self.render_analytics_data(result)
                    elif result_type == "prediction":
                        self.render_prediction_data(result)
                    elif result_type == "token_analysis":
                        self.render_token_data(result)
                    elif result_type == "data_feed":
                        self.render_feed_data(result)
                    elif result_type == "structured_data":
                        self.render_structured_data(result)
                    else:
                        # For unknown types, render as JSON
                        st.json(result)
                except Exception as e:
                    st.error(f"Error rendering result: {str(e)}")
                    # Fallback to JSON rendering
                    st.json(result)
        
        # If no results were rendered
        if results_count == 0:
            st.info("No service execution results are available yet.")

    def render_analytics_data(self, result):
        """Render analytics data with visualizations"""
        # Display title if available
        if "title" in result:
            st.subheader(result["title"])
        
        # Display market overview if available
        if "market_overview" in result:
            st.markdown("### Market Overview")
            overview = result["market_overview"]
            
            # Create metrics display
            cols = st.columns(3)
            metrics_data = [
                {"label": "Total TVL", "value": overview.get("total_tvl", "N/A")},
                {"label": "Daily Change", "value": overview.get("daily_change", "N/A")},
                {"label": "Dominant Chain", "value": overview.get("dominant_chain", "N/A")}
            ]
            
            for i, metric in enumerate(metrics_data):
                with cols[i % 3]:
                    st.metric(label=metric["label"], value=metric["value"])
        
        # Display protocol analysis if available
        if "protocol_analysis" in result:
            st.markdown("### Protocol Analysis")
            protocols = result["protocol_analysis"]
            
            # Create a DataFrame for better display
            if protocols:
                try:
                    df = pd.DataFrame(protocols)
                    st.dataframe(df, use_container_width=True)
                except Exception:
                    # Fallback if DataFrame creation fails
                    for p in protocols:
                        st.write(f"**{p.get('name', 'Unknown')}**: TVL {p.get('tvl', 'N/A')}, Growth {p.get('growth', 'N/A')}")
        
        # Display chart data if available
        if "chart_data" in result and "tvl_over_time" in result["chart_data"]:
            st.markdown("### TVL Trend")
            chart_data = result["chart_data"]["tvl_over_time"]
            
            try:
                # Convert to DataFrame for charting
                df = pd.DataFrame(chart_data)
                # Create a chart
                st.line_chart(df.set_index("date"))
            except Exception as e:
                st.error(f"Could not render chart: {str(e)}")
                st.write(chart_data)
        
        # Display any additional sections in the result
        for key, value in result.items():
            if key not in ["title", "market_overview", "protocol_analysis", "chart_data", "result_type", "metadata"]:
                st.markdown(f"### {key.replace('_', ' ').title()}")
                
                if isinstance(value, dict):
                    # For dictionary values, extract key points
                    for k, v in value.items():
                        st.write(f"**{k.replace('_', ' ').title()}**: {v}")
                elif isinstance(value, list):
                    # For list values, create bullet points
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                st.write(f"- **{k.replace('_', ' ').title()}**: {v}")
                        else:
                            st.write(f"- {item}")
                else:
                    # For simple values
                    st.write(value)

    def render_prediction_data(self, result):
        """Render price prediction data with visualizations"""
        # Display title if available
        if "title" in result:
            st.subheader(result["title"])
        
        # Display current prices if available
        if "current_prices" in result:
            st.markdown("### Current Prices")
            current = result["current_prices"]
            
            # Create metrics for current prices
            if isinstance(current, dict):
                cols = st.columns(len(current) if len(current) <= 4 else 4)
                i = 0
                for token, price in current.items():
                    with cols[i % len(cols)]:
                        st.metric(label=token, value=price)
                    i += 1
            elif isinstance(current, list):
                cols = st.columns(len(current) if len(current) <= 4 else 4)
                for i, item in enumerate(current):
                    if isinstance(item, dict) and "token" in item and "price" in item:
                        with cols[i % len(cols)]:
                            st.metric(label=item["token"], value=item["price"])
        
        # Display predictions if available
        if "predictions" in result:
            st.markdown("### Price Predictions")
            predictions = result["predictions"]
            
            # Check if predictions is a list of forecast points
            if isinstance(predictions, list):
                try:
                    # Create a DataFrame for the predictions
                    df = pd.DataFrame(predictions)
                    
                    # Check if we have date and value columns for charting
                    if "date" in df.columns and any(col in df.columns for col in ["price", "value", "prediction"]):
                        value_col = next(col for col in ["price", "value", "prediction"] if col in df.columns)
                        
                        # Create a chart
                        st.line_chart(df.set_index("date")[value_col])
                        
                        # Show the data table
                        st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Could not render predictions chart: {str(e)}")
                    # Fall back to listing the predictions
                    for pred in predictions:
                        if isinstance(pred, dict):
                            pred_str = ", ".join([f"{k}: {v}" for k, v in pred.items()])
                            st.write(f"- {pred_str}")
                        else:
                            st.write(f"- {pred}")
        
        # Display technical indicators if available
        if "technical_indicators" in result:
            st.markdown("### Technical Indicators")
            indicators = result["technical_indicators"]
            
            if isinstance(indicators, dict):
                # Create two columns
                col1, col2 = st.columns(2)
                
                # Split indicators between columns
                items = list(indicators.items())
                mid = len(items) // 2
                
                with col1:
                    for k, v in items[:mid]:
                        st.write(f"**{k.replace('_', ' ').title()}**: {v}")
                
                with col2:
                    for k, v in items[mid:]:
                        st.write(f"**{k.replace('_', ' ').title()}**: {v}")
            elif isinstance(indicators, list):
                for indicator in indicators:
                    if isinstance(indicator, dict):
                        name = indicator.get("name", "Indicator")
                        value = indicator.get("value", "N/A")
                        signal = indicator.get("signal", "")
                        
                        # Display with color based on signal
                        if signal.lower() in ["buy", "bullish", "positive"]:
                            st.markdown(f"**{name}**: {value} 🟢 {signal}")
                        elif signal.lower() in ["sell", "bearish", "negative"]:
                            st.markdown(f"**{name}**: {value} 🔴 {signal}")
                        else:
                            st.markdown(f"**{name}**: {value} ⚪ {signal}")
                    else:
                        st.write(f"- {indicator}")
        
        # Display any recommendation if available
        if "recommendation" in result:
            st.markdown("### Recommendation")
            rec = result["recommendation"]
            
            if isinstance(rec, str):
                st.info(rec)
            elif isinstance(rec, dict):
                action = rec.get("action", "").upper()
                reason = rec.get("reason", "")
                confidence = rec.get("confidence", "")
                
                # Display with appropriate styling
                if action in ["BUY", "STRONG BUY"]:
                    st.success(f"**{action}** - {reason}")
                elif action in ["SELL", "STRONG SELL"]:
                    st.error(f"**{action}** - {reason}")
                elif action == "HOLD":
                    st.warning(f"**{action}** - {reason}")
                else:
                    st.info(f"**{action}** - {reason}")
                
                if confidence:
                    st.write(f"Confidence: {confidence}")

    def render_token_data(self, result):
        """Render token or NFT data with visualizations"""
        # Display title if available
        if "title" in result:
            st.subheader(result["title"])
        
        # Display token fundamentals if available
        if "fundamentals" in result:
            st.markdown("### Token Fundamentals")
            fundamentals = result["fundamentals"]
            
            if isinstance(fundamentals, dict):
                # Create a styled card for token info
                st.markdown("""
                <style>
                .token-card {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 20px;
                    margin-bottom: 20px;
                    background-color: #f8f9fa;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Format the card content
                card_content = "<div class='token-card'>"
                for k, v in fundamentals.items():
                    card_content += f"<p><strong>{k.replace('_', ' ').title()}</strong>: {v}</p>"
                card_content += "</div>"
                
                st.markdown(card_content, unsafe_allow_html=True)
            elif isinstance(fundamentals, list):
                for item in fundamentals:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            st.write(f"**{k.replace('_', ' ').title()}**: {v}")
                    else:
                        st.write(f"- {item}")
        
        # Display market positioning if available
        if "market_positioning" in result:
            st.markdown("### Market Positioning")
            positioning = result["market_positioning"]
            
            if isinstance(positioning, dict):
                for k, v in positioning.items():
                    st.write(f"**{k.replace('_', ' ').title()}**: {v}")
            elif isinstance(positioning, list):
                for item in positioning:
                    if isinstance(item, dict):
                        # Try to format as competitor comparison
                        if "name" in item and "advantage" in item:
                            st.write(f"**{item['name']}**: {item['advantage']}")
                        else:
                            for k, v in item.items():
                                st.write(f"- **{k.replace('_', ' ').title()}**: {v}")
                    else:
                        st.write(f"- {item}")
        
        # Display risk evaluation if available
        if "risk_evaluation" in result:
            st.markdown("### Risk Evaluation")
            risks = result["risk_evaluation"]
            
            if isinstance(risks, dict):
                # Create a table for risk factors
                risk_data = []
                for factor, rating in risks.items():
                    risk_data.append({"Factor": factor.replace("_", " ").title(), "Rating": rating})
                
                try:
                    df = pd.DataFrame(risk_data)
                    st.dataframe(df, use_container_width=True)
                except Exception:
                    # Fallback if DataFrame creation fails
                    for factor, rating in risks.items():
                        st.write(f"**{factor.replace('_', ' ').title()}**: {rating}")
            elif isinstance(risks, list):
                for risk in risks:
                    if isinstance(risk, dict):
                        factor = risk.get("factor", "Risk Factor")
                        level = risk.get("level", "Medium")
                        description = risk.get("description", "")
                        
                        # Style based on risk level
                        if level.lower() in ["high", "severe", "critical"]:
                            st.error(f"**{factor}**: {level} - {description}")
                        elif level.lower() in ["medium", "moderate"]:
                            st.warning(f"**{factor}**: {level} - {description}")
                        else:
                            st.info(f"**{factor}**: {level} - {description}")
                    else:
                        st.write(f"- {risk}")
        
        # Display investment rating if available
        if "investment_rating" in result:
            st.markdown("### Investment Rating")
            rating = result["investment_rating"]
            
            if isinstance(rating, dict):
                # Overall rating
                overall = rating.get("overall", "N/A")
                
                # Create gauge chart for overall rating if it's a number
                try:
                    overall_num = float(overall) if isinstance(overall, str) else overall
                    if isinstance(overall_num, (int, float)):
                        # Create a simple gauge
                        st.markdown(f"**Overall Rating**: {overall_num}/10")
                        st.progress(min(overall_num / 10, 1.0))
                    else:
                        st.markdown(f"**Overall Rating**: {overall}")
                except (ValueError, TypeError):
                    st.markdown(f"**Overall Rating**: {overall}")
                
                # Display other ratings
                for k, v in rating.items():
                    if k != "overall":
                        st.write(f"**{k.replace('_', ' ').title()}**: {v}")
            else:
                st.write(rating)

    def render_feed_data(self, result):
        """Render data feed results with visualizations"""
        # Display title if available
        if "title" in result:
            st.subheader(result["title"])
        
        # Display time series data if available
        if "time_series_data" in result:
            st.markdown("### Time Series Data")
            time_series = result["time_series_data"]
            
            # Check if it's a list that can be converted to a DataFrame
            if isinstance(time_series, list) and time_series:
                try:
                    df = pd.DataFrame(time_series)
                    
                    # If we have date/timestamp column
                    time_cols = [col for col in df.columns if col.lower() in ["date", "timestamp", "time"]]
                    if time_cols:
                        time_col = time_cols[0]
                        
                        # Get value columns (excluding the time column)
                        value_cols = [col for col in df.columns if col != time_col]
                        
                        # Display as line chart
                        st.line_chart(df.set_index(time_col)[value_cols])
                    
                    # Display raw data
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Could not render time series data: {str(e)}")
                    
                    # Fallback to listing
                    for entry in time_series[:10]:  # Limit to first 10
                        if isinstance(entry, dict):
                            entry_str = ", ".join([f"{k}: {v}" for k, v in entry.items()])
                            st.write(f"- {entry_str}")
                        else:
                            st.write(f"- {entry}")
        
        # Display KPIs if available
        if "kpis" in result:
            st.markdown("### Key Performance Indicators")
            kpis = result["kpis"]
            
            if isinstance(kpis, dict):
                # Create metrics display
                cols = st.columns(len(kpis) if len(kpis) <= 4 else 4)
                i = 0
                for name, value in kpis.items():
                    with cols[i % len(cols)]:
                        st.metric(label=name.replace("_", " ").title(), value=value)
                    i += 1
            elif isinstance(kpis, list):
                # Create a grid of metrics
                cols = st.columns(min(len(kpis), 4))
                for i, kpi in enumerate(kpis):
                    if isinstance(kpi, dict):
                        name = kpi.get("name", f"KPI {i+1}")
                        value = kpi.get("value", "N/A")
                        with cols[i % len(cols)]:
                            st.metric(label=name, value=value)
                    else:
                        st.write(f"- {kpi}")
        
        # Display anomalies if available
        if "anomalies" in result:
            st.markdown("### Anomaly Detection")
            anomalies = result["anomalies"]
            
            if isinstance(anomalies, list):
                if not anomalies:
                    st.success("No anomalies detected")
                else:
                    for anomaly in anomalies:
                        if isinstance(anomaly, dict):
                            description = anomaly.get("description", "Unknown anomaly")
                            severity = anomaly.get("severity", "medium")
                            timestamp = anomaly.get("timestamp", "")
                            
                            # Style based on severity
                            if severity.lower() in ["high", "critical", "severe"]:
                                st.error(f"**{description}** {timestamp if timestamp else ''}")
                            elif severity.lower() == "medium":
                                st.warning(f"**{description}** {timestamp if timestamp else ''}")
                            else:
                                st.info(f"**{description}** {timestamp if timestamp else ''}")
                        else:
                            st.write(f"- {anomaly}")
            elif isinstance(anomalies, dict):
                detected = anomalies.get("detected", False)
                if not detected:
                    st.success("No anomalies detected")
                else:
                    details = anomalies.get("details", [])
                    if details:
                        for detail in details:
                            if isinstance(detail, str):
                                st.warning(detail)
                            elif isinstance(detail, dict):
                                desc = detail.get("description", "")
                                time = detail.get("time", "")
                                st.warning(f"{desc} ({time})" if time else desc)

    def render_structured_data(self, result):
        """Render generic structured data results"""
        # Display title if available
        if "title" in result:
            st.subheader(result["title"])
        
        # Initialize tabs for different sections
        tabs = []
        tab_titles = []
        
        # Identify main sections to create tabs
        for key, value in result.items():
            if key not in ["title", "result_type", "metadata"] and isinstance(value, (dict, list)) and value:
                tabs.append((key, value))
                tab_titles.append(key.replace("_", " ").title())
        
        # If we have multiple meaningful sections, create tabs
        if len(tabs) > 1:
            streamlit_tabs = st.tabs(tab_titles)
            
            for i, (key, value) in enumerate(tabs):
                with streamlit_tabs[i]:
                    if isinstance(value, dict):
                        # Render dictionary as sections
                        for k, v in value.items():
                            if isinstance(v, (dict, list)) and v:
                                st.markdown(f"**{k.replace('_', ' ').title()}**")
                                st.json(v)
                            else:
                                st.write(f"**{k.replace('_', ' ').title()}**: {v}")
                    elif isinstance(value, list):
                        # Render list content
                        if all(isinstance(item, dict) for item in value):
                            # Try to create a DataFrame
                            try:
                                df = pd.DataFrame(value)
                                st.dataframe(df, use_container_width=True)
                            except Exception:
                                # Fallback to listing
                                for item in value:
                                    item_str = ", ".join([f"{k}: {v}" for k, v in item.items()])
                                    st.write(f"- {item_str}")
                        else:
                            # Simple list
                            for item in value:
                                st.write(f"- {item}")
        else:
            # For simple structures or single sections, render without tabs
            for key, value in result.items():
                if key not in ["title", "result_type", "metadata"]:
                    st.markdown(f"### {key.replace('_', ' ').title()}")
                    
                    if isinstance(value, dict):
                        # Render dictionary content
                        for k, v in value.items():
                            if isinstance(v, (dict, list)) and v:
                                st.markdown(f"**{k.replace('_', ' ').title()}**")
                                st.json(v)
                            else:
                                st.write(f"**{k.replace('_', ' ').title()}**: {v}")
                    elif isinstance(value, list):
                        # Render list content
                        if all(isinstance(item, dict) for item in value):
                            # Try to create a DataFrame
                            try:
                                df = pd.DataFrame(value)
                                st.dataframe(df, use_container_width=True)
                            except Exception:
                                # Fallback to listing
                                for item in value:
                                    item_str = ", ".join([f"{k}: {v}" for k, v in item.items()])
                                    st.write(f"- {item_str}")
                        else:
                            # Simple list
                            for item in value:
                                st.write(f"- {item}")
                    else:
                        # Simple value
                        st.write(value)

    def display_verification_results(self, verification_results):
        """
        Display the verification results in the UI
        
        Args:
            verification_results: Dictionary with verification results
        """
        if not verification_results:
            return
            
        st.subheader("🧪 AI Output Verification")
        
        # Display overall verification status
        if verification_results.get("verified", False):
            st.success("✅ All outputs successfully verified")
            
            # Show verification source if available
            if "verification_source" in verification_results:
                st.info(verification_results["verification_source"])
        else:
            st.warning("⚠️ Some outputs failed verification")
            
            # Show refund information if available
            if "refund" in verification_results:
                refund = verification_results["refund"]
                st.info(f"💰 Eligible for {refund.get('percent', 0)}% refund ({refund.get('amount', 0)} OLAS)")
        
        # Show verification details for each service
        verification_details = verification_results.get("verification_details", [])
        
        if verification_details:
            # Create a column for each service (up to 3 per row)
            cols = st.columns(min(3, len(verification_details)))
            
            for i, detail in enumerate(verification_details):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    service_id = detail.get("service_id", "Unknown")
                    service_name = self.get_service_name(service_id)
                    verified = detail.get("verified", False)
                    confidence = detail.get("confidence", 0)
                    
                    # Create a card-like container
                    with st.container():
                        # Title with service name and status icon
                        if verified:
                            st.markdown(f"#### ✅ {service_name}")
                        else:
                            st.markdown(f"#### ❌ {service_name}")
                        
                        st.markdown(f"**Service ID:** {service_id}")
                        st.markdown(f"**Confidence:** {confidence:.2f}")
                        
                        # Show recommendation
                        if "recommendation" in detail:
                            st.markdown(f"**Assessment:** {detail['recommendation']}")
                        
                        # Show DeFi Llama data comparisons if available
                        if "data_comparisons" in detail and detail["data_comparisons"]:
                            st.markdown("**Data Verification:**")
                            for comparison in detail["data_comparisons"]:
                                st.markdown(f"- {comparison}")
                        
                        # Show issues if any
                        if not verified and "issues" in detail and detail["issues"]:
                            st.markdown("**Issues:**")
                            for issue in detail["issues"]:
                                st.markdown(f"- {issue}")
        
        # Show verification endpoints if available
        if "verification_endpoints" in verification_results and verification_results["verification_endpoints"]:
            with st.expander("Verification Data Sources"):
                st.markdown("**Data was verified using the following DeFi Llama endpoints:**")
                for endpoint in verification_results["verification_endpoints"]:
                    st.markdown(f"- `{endpoint}`")
        
        # Provide explanation about verification process
        with st.expander("About AI Output Verification"):
            st.markdown("""
            ### How Verification Works

            Output verification compares generated results against benchmark standards like DeFi Llama to ensure quality and accuracy.
            
            **Verification Process:**
            1. Results are analyzed for structural integrity
            2. Content relevance to the original request is evaluated
            3. Factual consistency is checked against DeFi Llama API data
            4. Confidence scores are calculated based on multiple factors
            
            **Data Sources:**
            - [DeFi Llama API](https://defillama.com/docs/api) - For protocol TVL, prices, and market data
            - Standard financial metrics and indicators
            - Historical performance data
            
            **Verification Methodology:**
            The system cross-references AI-generated outputs with real-time DeFi data to ensure accuracy and reliability of recommendations and analytics.
            """)
        
        # Add a clear separator
        st.markdown("---")

    def render(self):
        """Render the execution status UI"""
        try:
            # Get request from session state
            request = None
            if "request" in st.session_state:
                request = st.session_state.request
            elif "current_request" in st.session_state:
                request = st.session_state.current_request
                # Also update the standard location
                st.session_state.request = request
            
            # Ensure we have a request
            if not request:
                print("No request found in session state. Creating a default request.")
                # Create a default request for demo purposes
                default_request = {
                    "prompt": "Analyze current DeFi market trends and recommend investment strategies",
                    "selected_services": [],  # Empty services list, our mock data will handle this
                    "total_cost": 0,
                    "submitted_at": datetime.now().isoformat()
                }
                request = default_request
                st.session_state.request = request
            
            # Store the request in the instance as well
            self.request = request
            
            # Copy request for safe modification
            local_request = self.deep_copy_request(request)
            
            # Ensure the request has a transaction ID
            transaction_id = self.ensure_transaction(local_request)
            
            # Get the execution status
            status = self.get_execution_status(local_request)
            
            # Get the total cost
            total_cost = 0
            if isinstance(local_request, dict):
                total_cost = local_request.get("total_cost", 0)
            else:
                total_cost = getattr(local_request, "total_cost", 0)
                
            if total_cost and isinstance(total_cost, str):
                try:
                    total_cost = float(total_cost)
                except ValueError:
                    total_cost = 0
            
            # Extract service IDs
            service_ids = []
            if isinstance(local_request, dict) and "selected_services" in local_request and local_request["selected_services"]:
                selected_services = local_request["selected_services"]
                if isinstance(selected_services, list):
                    service_ids = [s.get("id", s) if isinstance(s, dict) else s for s in selected_services]
                elif isinstance(selected_services, dict):
                    service_ids = list(selected_services.keys())
            elif hasattr(local_request, "selected_services") and local_request.selected_services:
                if isinstance(local_request.selected_services, list):
                    service_ids = [s.get("id", s) if isinstance(s, dict) else s for s in local_request.selected_services]
                elif isinstance(local_request.selected_services, dict):
                    service_ids = list(local_request.selected_services.keys())
                    
            # If no services were selected, use default ones
            if not service_ids:
                print("No service IDs found in the request. Using default service IDs.")
                service_ids = ["1722", "1815", "1966", "1983"]
                # Update the request with default services to avoid "No services selected" message
                if isinstance(local_request, dict):
                    local_request["selected_services"] = [{"id": sid, "description": f"Service {sid}"} for sid in service_ids]
                elif hasattr(local_request, "selected_services"):
                    local_request.selected_services = [{"id": sid, "description": f"Service {sid}"} for sid in service_ids]
            
            # Display request details
            self.display_request_details(local_request)
            
            # Overall progress section
            st.subheader("⏱️ Overall Progress")
            progress_percent = status.get('progress', 0)
            if isinstance(progress_percent, str):
                try:
                    progress_percent = float(progress_percent)
                except ValueError:
                    progress_percent = 0
            
            # Calculate ETA
            eta_seconds = round((100 - progress_percent) * 0.3)
            eta_text = f"Estimated time remaining: {eta_seconds} seconds" if eta_seconds > 0 else "Completed"
            
            # Progress bar
            st.progress(progress_percent / 100)
            
            # Status message
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Status:** {status.get('status', 'Unknown').title()}")
            with col2:
                st.markdown(f"**ETA:** {eta_text}")
            
            # Processing Pipeline section
            st.subheader("⚙️ Processing Pipeline")
            
            # Get pipeline steps
            pipeline_steps = status.get('pipeline_steps', [])
            
            # If no pipeline steps and we have service IDs, generate them
            if not pipeline_steps and service_ids:
                request_text = ""
                if isinstance(local_request, dict):
                    request_text = local_request.get("prompt", "")
                else:
                    request_text = getattr(local_request, "prompt", "")
                    
                pipeline_steps = self.generate_pipeline_steps(service_ids, request_text)
            
            # Display pipeline steps
            self.display_pipeline_steps(pipeline_steps)
            
            # Service Results section
            st.subheader("📊 Service Execution Results")
            
            # Get execution results
            execution_results = status.get('execution_results', {})
            
            # If no execution results and we have service IDs, generate mock results
            if not execution_results and service_ids:
                # Generate mock execution data that includes results for each service
                mock_data = self.get_mock_execution_data(local_request)
                if mock_data and "execution_results" in mock_data:
                    execution_results = mock_data["execution_results"]
            
            # Render service execution results
            self.render_service_execution_results(execution_results)
            
            # Verification Results section
            if execution_results:
                # Perform verification on results and display
                verification_results = self.verify_service_results(execution_results)
                self.display_verification_results(verification_results)
            
            # Navigation buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("New Request", type="primary"):
                    st.session_state.page = "create_request"
                    st.rerun()
            with col2:
                if st.button("Back to Dashboard", type="secondary"):
                    st.session_state.page = "dashboard"
                    st.rerun()
                    
        except Exception as e:
            # Display error with traceback for debugging
            st.error(f"Error displaying execution status: {str(e)}")
            st.error(traceback.format_exc())
            
            # Add a re-try button
            if st.button("Retry"):
                st.rerun()
                
            # Add return to dashboard button
            if st.button("Return to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()
        
    def get_execution_status(self, request):
        """
        Get the execution status for a request
        
        Args:
            request: A Request object or dictionary with transaction_id
        
        Returns:
            Dictionary with execution status information
        """
        try:
            # Get transaction ID from request
            if isinstance(request, dict):
                transaction_id = request.get('transaction_id', '')
            else:
                transaction_id = getattr(request, 'transaction_id', '')
                
            if not transaction_id:
                # Create a fallback status with minimal info
                return {
                    'status': 'pending',
                    'progress': 10,
                    'message': 'Waiting for transaction confirmation',
                    'pipeline_steps': self.get_default_pipeline_steps(),
                    'execution_results': {}
                }
                
            # For now, this is a mock function that returns randomized status
            # In a real implementation, this would query a backend API
            
            # Get current timestamp for deterministic but "random" progress
            timestamp = int(time.time())
            # Use the transaction ID as a seed with the day timestamp
            # This ensures the same transaction shows consistent progress within each day
            day_seconds = timestamp % (24 * 60 * 60)
            
            # Generate a deterministic random progress based on transaction ID and time
            progress_base = (int(day_seconds / 300) * 10) % 100  # Changes every 5 minutes
            
            # If the transaction ID is longer than 10 chars, use its hash as a seed
            if len(transaction_id) > 10:
                import hashlib
                tx_seed = int(hashlib.md5(transaction_id.encode()).hexdigest(), 16) % 100
                progress = min(100, progress_base + tx_seed % 20)  # Add a transaction-specific offset
            else:
                progress = progress_base
                
            # After 80% progress, slow down to simulate final confirmation
            if progress > 80:
                progress = 80 + (progress - 80) / 4
                
            # Status is complete once progress reaches 100%
            status = 'complete' if progress >= 100 else 'processing' if progress > 10 else 'pending'
            
            # Generate pipeline steps if progress is sufficient
            pipeline_steps = []
            if progress > 20:
                # Get service IDs from the request
                service_ids = []
                if isinstance(request, dict) and 'selected_services' in request:
                    selected_services = request['selected_services']
                    if isinstance(selected_services, list):
                        service_ids = [s.get('id', s) if isinstance(s, dict) else s for s in selected_services]
                    elif isinstance(selected_services, dict):
                        service_ids = list(selected_services.keys())
                elif hasattr(request, 'selected_services') and request.selected_services:
                    selected_services = request.selected_services
                    if isinstance(selected_services, list):
                        service_ids = [s.get('id', s) if isinstance(s, dict) else s for s in selected_services]
                    elif isinstance(selected_services, dict):
                        service_ids = list(selected_services.keys())
                        
                # Generate pipeline steps for the services
                pipeline_steps = self.generate_pipeline_steps(service_ids)
                
                # Update step status based on progress
                completed_steps = int((len(pipeline_steps) * progress) / 100)
                for i, step in enumerate(pipeline_steps):
                    if i < completed_steps:
                        step['status'] = 'complete'
                        # Set a realistic duration
                        step['duration'] = f"{random.randint(2, 15)} seconds"
                    elif i == completed_steps:
                        step['status'] = 'in_progress'
                        step['duration'] = ''
                    else:
                        step['status'] = 'pending'
                        step['duration'] = ''
            else:
                # Default pipeline for early stages
                pipeline_steps = self.get_default_pipeline_steps()
                
            # Generate execution results if complete
            execution_results = {}
            if status == 'complete':
                execution_results = self.get_mock_execution_data(request)
                
            # Return combined status
            return {
                'status': status,
                'progress': progress,
                'transaction_id': transaction_id,
                'timestamp': datetime.now().isoformat(),
                'pipeline_steps': pipeline_steps,
                'execution_results': execution_results,
                'message': f"Transaction {status}"
            }
        except Exception as e:
            # Log error and return error status
            print(f"Error getting execution status: {str(e)}")
            traceback.print_exc()
            
            # Return error status
            return {
                'status': 'error',
                'progress': 0,
                'message': f"Error: {str(e)}",
                'pipeline_steps': self.get_default_pipeline_steps(),
                'execution_results': {},
                'error': str(e)
            }
        
    def display_execution_header(self, transaction_id):
        """Display the execution status header with transaction ID"""
        st.markdown("## Execution Status")
        
        # Format the transaction ID for display
        if transaction_id:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                <strong>Transaction ID:</strong> 
                <a href="https://gnosisscan.io/tx/{transaction_id}" target="_blank" style="font-family: monospace;">
                    {transaction_id[:10]}...{transaction_id[-6:]}
                </a>
            </div>
            """, unsafe_allow_html=True)
            
    def display_request_details(self, request):
        """Display the request details section"""
        if not request:
            return
            
        st.markdown("### Request Details")
        
        # Extract details whether request is dict or object
        if isinstance(request, dict):
            prompt = request.get('prompt', 'No prompt provided')
            submitted_at = request.get('submitted_at', 'Unknown')
            total_cost = request.get('total_cost', 0)
        else:
            prompt = getattr(request, 'prompt', 'No prompt provided')
            submitted_at = getattr(request, 'submitted_at', 'Unknown')
            total_cost = getattr(request, 'total_cost', 0)
            
        # Format date if it's in ISO format
        if isinstance(submitted_at, str) and 'T' in submitted_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                submitted_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
                
        # Display the details
        st.markdown(f"**Prompt:** {prompt}")
        st.markdown(f"**Submitted:** {submitted_at}")
        st.markdown(f"**Total Cost:** {total_cost} OLAS")
        
        # Display selected services with rich metadata
        st.markdown("### Selected Services")
        
        if isinstance(request, dict):
            services = request.get('selected_services', [])
        else:
            services = getattr(request, 'selected_services', [])
            
        if not services:
            # Create default sample services for demo purposes
            default_services = [
                {"id": "1722", "cost": 15, "service_id": "1722"},
                {"id": "1815", "cost": 10, "service_id": "1815"},
                {"id": "1966", "cost": 12, "service_id": "1966"}
            ]
            
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #ffc107;">
                <p style="margin: 0; color: #856404;"><b>Note:</b> No services were explicitly selected. Displaying demo services.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Use the default services
            services = default_services
            
            # Update the request with these services
            if isinstance(request, dict):
                request['selected_services'] = services
                # Update total cost
                total_cost = sum(s.get('cost', 0) for s in services)
                request['total_cost'] = total_cost
                st.markdown(f"**Updated Total Cost:** {total_cost} OLAS")
            else:
                # Only update if we have a proper object with attributes
                try:
                    request.selected_services = services
                    # Update total cost
                    total_cost = sum(s.get('cost', 0) for s in services)
                    request.total_cost = total_cost
                    st.markdown(f"**Updated Total Cost:** {total_cost} OLAS")
                except:
                    pass
            
        # Display each service with full metadata
        for service in services:
            if isinstance(service, dict):
                service_id = service.get('id') or service.get('service_id')
                service_cost = service.get('cost', 0) or service.get('price', 0)
            else:
                service_id = getattr(service, 'id', None) or getattr(service, 'service_id', None)
                service_cost = getattr(service, 'cost', 0) or getattr(service, 'price', 0)
                
            # Get full service details
            service_details = self.get_service_details(service_id)
            service_name = service_details.get('name', self.get_service_name(service_id))
            mech_address = service_details.get('mech_address', 'N/A')
            status = service_details.get('status', 'Unknown')
            description = service_details.get('description', 'No description available')
            
            # Display service card with rich metadata
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #007bff;">
                <h4 style="margin-top: 0; color: #333;">{service_name}</h4>
                <p style="margin-bottom: 10px; color: #666; font-size: 0.9em;">{description}</p>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 5px;">
                    <div style="background-color: #e9f5ff; padding: 5px 10px; border-radius: 3px; font-size: 0.8em;">
                        <strong>ID:</strong> {service_id}
                    </div>
                    <div style="background-color: #f0fff0; padding: 5px 10px; border-radius: 3px; font-size: 0.8em;">
                        <strong>Cost:</strong> {service_cost} OLAS
                    </div>
                    <div style="background-color: #fff8e6; padding: 5px 10px; border-radius: 3px; font-size: 0.8em;">
                        <strong>Status:</strong> {status}
                    </div>
                </div>
                <div style="font-family: monospace; font-size: 0.8em; color: #666; margin-top: 5px;">
                    <strong>Mech:</strong> {mech_address}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    def display_overall_progress(self, status):
        """Display the overall progress section"""
        if not status:
            st.warning("No status information available.")
            return
            
        st.markdown("### Overall Progress")
        
        # Get progress value from status
        progress = status.get('progress', 0)
        status_text = status.get('status', 'unknown').upper()
        
        # Display progress bar
        st.progress(progress)
        
        # Display status text with appropriate styling
        status_color = "#4CAF50" if status_text == "COMPLETE" else "#FFC107"
        st.markdown(f"""
        <div style="display: inline-block; background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">
            {status_text}
        </div>
        """, unsafe_allow_html=True)
        
    def display_processing_pipeline(self, status):
        """Display the processing pipeline section"""
        if not status or 'pipeline_steps' not in status:
            st.warning("No pipeline information available.")
            return
            
        st.markdown("### Processing Pipeline")
        
        # Get pipeline steps from status
        steps = status.get('pipeline_steps', [])
        
        if not steps:
            st.info("No processing steps available.")
            return
            
        # Display each step
        for i, step in enumerate(steps):
            step_name = step.get('name', f"Step {i+1}")
            step_description = step.get('description', '')
            step_status = step.get('status', 'unknown')
            step_duration = step.get('duration', '')
            
            # Determine step status color
            status_color = "#4CAF50" if step_status == "complete" else "#FFC107"
            
            # Create an expander for each step
            with st.expander(f"{step_name}", expanded=i==0):
                st.markdown(f"""
                <div style="margin-bottom: 10px;">
                    <span style="display: inline-block; background-color: {status_color}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; margin-bottom: 10px;">
                        {step_status.upper()}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**Description:** {step_description}")
                
                if step_duration:
                    st.markdown(f"**Duration:** {step_duration}")
                else:
                    st.markdown("**Duration:** Not available")

    def display_pipeline_steps(self, pipeline_steps):
        """
        Display the processing pipeline steps in the UI
        
        Args:
            pipeline_steps: List of pipeline step dictionaries
        """
        if not pipeline_steps:
            st.info("No processing steps available.")
            return
        
        # Display each step as an expander
        for i, step in enumerate(pipeline_steps):
            step_name = step.get('name', f"Step {i+1}")
            step_description = step.get('description', 'No description available')
            step_status = step.get('status', 'pending')
            step_duration = step.get('duration', '')
            
            # Determine step status color and icon
            if step_status == 'complete':
                status_color = "#4CAF50"  # Green
                status_icon = "✅"
            elif step_status == 'in_progress':
                status_color = "#FFC107"  # Yellow/amber
                status_icon = "⏳"
            elif step_status == 'error':
                status_color = "#F44336"  # Red
                status_icon = "❌"
            else:
                status_color = "#9E9E9E"  # Gray
                status_icon = "⏱️"
            
            # Create an expander for this step
            with st.expander(f"{status_icon} {step_name}", expanded=step_status == 'in_progress'):
                # Show status badge
                st.markdown(f"""
                <div style="margin-bottom: 10px;">
                    <span style="display: inline-block; background-color: {status_color}; color: white; 
                    padding: 2px 8px; border-radius: 3px; font-size: 0.8em; margin-bottom: 10px;">
                        {step_status.upper()}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # Show description
                st.markdown(f"**Description:** {step_description}")
                
                # Show duration if available
                if step_duration:
                    st.markdown(f"**Duration:** {step_duration}")
                    
                # If in progress, show spinner
                if step_status == 'in_progress':
                    st.spinner("Processing...")
    
    def deep_copy_request(self, request):
        """Safely deep copy a request object (dict or custom class)."""
        try:
            return copy.deepcopy(request)
        except Exception:
            # Fallback: shallow copy
            return dict(request) if hasattr(request, 'items') else request
        
    def run_mechx_interact(self, prompt, agent_id, tool_name, key_path, chain_config="gnosis", confirm_type="on-chain"):
        """
        Run the mechx interact command with the given parameters and stream the output to the UI.
        """
        import subprocess
        import shlex
        st.markdown("### Mech Client Execution Log")
        cmd = f"mechx interact {shlex.quote(prompt)} --agent_id {shlex.quote(str(agent_id))} --key {shlex.quote(key_path)} --tool {shlex.quote(tool_name)} --chain-config {shlex.quote(chain_config)} --confirm {shlex.quote(confirm_type)}"
        st.info(f"Running: `{cmd}`")
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output_box = st.empty()
        output_lines = []
        for line in process.stdout:
            output_lines.append(line.rstrip())
            output_box.code("\n".join(output_lines), language="bash")
        process.stdout.close()
        process.wait()
        st.success("Mech request complete.")
"""Utility functions for generating mock data for different result types"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

def generate_analytics_result(service_name, request_text=""):
    """Generate mock analytics results based on the request text"""
    current_date = datetime.now()
    data_points = []
    
    # Generate 10 data points for the past 10 days
    for i in range(10):
        date_point = current_date - timedelta(days=i)
        value_point = random.uniform(80, 120)
        change_pct = random.uniform(-5, 5)
        data_points.append({
            "date": date_point.strftime("%Y-%m-%d"),
            "value": round(value_point, 2),
            "change_pct": round(change_pct, 2)
        })
    
    # Reverse to get chronological order
    data_points.reverse()
    
    # Create a prompt for the LLM to generate detailed analysis
    if request_text:
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
            analytics_prompt = ChatPromptTemplate.from_template(
                """You are a DeFi analytics service providing insights on market trends.
                Based on this request, generate a detailed market analysis:
                
                Request: {request_text}
                Service: {service_name}
                
                Format your response as a JSON object with these sections:
                - title: A descriptive title for the analysis
                - summary: A concise overview (3-4 sentences)
                - key_metrics: An object with 4-5 important metrics relevant to the request
                - trends: An array of 3-4 observed market trends
                - insights: An array of 3-4 actionable insights
                - risks: An array of 2-3 risk factors to consider
                
                All sections should be specific to the request provided.
                """
            )
            
            analytics_chain = analytics_prompt | llm | JsonOutputParser()
            result = analytics_chain.invoke({
                "request_text": request_text,
                "service_name": service_name
            })
            
            # Add chart data to the result
            result["chart_data"] = data_points
            
            return result
        except Exception as e:
            print(f"Error generating analytics content: {str(e)}")
            # Fall through to default
    
    # Default analytics result if no request text or if generation fails
    return {
        "title": f"{service_name} Market Analysis",
        "summary": "Analysis of current market trends and key metrics across DeFi protocols.",
        "chart_data": data_points,
        "key_metrics": {
            "total_tvl": f"${random.randint(40, 200)}B",
            "daily_volume": f"${random.randint(5, 30)}B",
            "avg_yield": f"{random.uniform(2, 8):.2f}%",
            "volatility_index": round(random.uniform(20, 60), 1)
        },
        "trends": [
            "Increased adoption of Layer 2 solutions for reduced gas fees",
            "Growing interest in decentralized derivatives platforms",
            "Yield farming opportunities shifting to newer protocols"
        ],
        "insights": [
            "Consider diversifying liquidity across multiple protocols to mitigate risk",
            "Monitor regulatory developments that may impact protocol governance",
            "Focus on protocols with sustainable tokenomics and real yield"
        ],
        "risks": [
            "Smart contract vulnerabilities remain a significant concern",
            "Market volatility could impact capital efficiency",
            "Regulatory uncertainties in major markets"
        ]
    }

def generate_prediction_result(service_name, request_text=""):
    """Generate mock prediction results based on the request text"""
    # Define token names and current prices
    tokens = {
        "ETH": round(random.uniform(1500, 3500), 2),
        "BTC": round(random.uniform(25000, 60000), 2),
        "MATIC": round(random.uniform(0.5, 1.5), 4),
        "LINK": round(random.uniform(5, 15), 2),
        "UNI": round(random.uniform(3, 10), 2),
        "AAVE": round(random.uniform(50, 200), 2)
    }
    
    # Generate prediction percentages for different timeframes
    predictions = {}
    for token, price in tokens.items():
        predictions[token] = {
            "current_price": price,
            "prediction_24h": round(price * (1 + random.uniform(-0.05, 0.07)), 2),
            "prediction_7d": round(price * (1 + random.uniform(-0.15, 0.2)), 2),
            "prediction_30d": round(price * (1 + random.uniform(-0.25, 0.35)), 2),
            "confidence": round(random.uniform(0.6, 0.9), 2)
        }
    
    # Create forecast data for chart
    forecast_data = []
    current_date = datetime.now()
    
    for i in range(30):
        date_point = current_date + timedelta(days=i)
        forecast_data.append({
            "date": date_point.strftime("%Y-%m-%d"),
            "eth_price": round(tokens["ETH"] * (1 + 0.01 * i * random.uniform(0.8, 1.2)), 2),
            "btc_price": round(tokens["BTC"] * (1 + 0.01 * i * random.uniform(0.8, 1.2)), 2)
        })
    
    # If we have a request text, try to generate relevant content
    if request_text:
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
            prediction_prompt = ChatPromptTemplate.from_template(
                """You are a price prediction service for cryptocurrency markets.
                Based on this request, generate a market forecast and analysis:
                
                Request: {request_text}
                Service: {service_name}
                
                Format your response as a JSON object with these sections:
                - title: A descriptive title for the forecast
                - summary: A concise overview of the forecast (3-4 sentences)
                - market_sentiment: Overall market sentiment (bullish, bearish, or neutral) with explanation
                - key_indicators: Array of 3-4 technical indicators supporting the forecast
                - catalysts: Array of 3-4 potential market catalysts that could impact prices
                - recommendations: Array of 2-3 strategic recommendations
                
                All sections should be specific to the request provided.
                """
            )
            
            prediction_chain = prediction_prompt | llm | JsonOutputParser()
            result = prediction_chain.invoke({
                "request_text": request_text,
                "service_name": service_name
            })
            
            # Add predictions and forecast data to the result
            result["predictions"] = predictions
            result["forecast_data"] = forecast_data
            
            return result
        except Exception as e:
            print(f"Error generating prediction content: {str(e)}")
            # Fall through to default
    
    # Default prediction result if no request text or if generation fails
    return {
        "title": f"{service_name} Market Forecast",
        "summary": "Forecast of cryptocurrency price movements based on technical and fundamental analysis.",
        "predictions": predictions,
        "forecast_data": forecast_data,
        "market_sentiment": {
            "overall": random.choice(["Bullish", "Neutral", "Slightly Bullish", "Slightly Bearish"]),
            "explanation": "Market indicators suggest cautious optimism with momentum building in major assets."
        },
        "key_indicators": [
            "Moving Average Convergence Divergence (MACD) showing positive momentum",
            "Relative Strength Index (RSI) in neutral territory with room for growth",
            "Support levels holding firm across major assets"
        ],
        "catalysts": [
            "Upcoming protocol upgrades for Ethereum",
            "Institutional adoption continuing to increase",
            "Regulatory developments in key markets"
        ],
        "recommendations": [
            "Consider dollar-cost averaging into major assets",
            "Set stop-losses to protect against market volatility",
            "Monitor on-chain metrics for early signs of trend changes"
        ]
    }

def generate_token_result(service_name, request_text=""):
    """Generate mock token analysis results based on the request text"""
    # Create token analysis data
    token_data = {
        "name": random.choice(["ETH", "BTC", "AAVE", "UNI", "LINK", "SNX"]),
        "price": round(random.uniform(10, 3000), 2),
        "market_cap": f"${random.randint(1, 500)}B",
        "volume_24h": f"${random.randint(100, 5000)}M",
        "circulating_supply": f"{random.randint(10, 500)}M",
        "max_supply": f"{random.randint(50, 1000)}M",
        "holders": random.randint(10000, 1000000),
        "risk_score": round(random.uniform(1, 10), 1)
    }
    
    # Create price history data
    price_history = []
    current_date = datetime.now()
    base_price = token_data["price"] * 0.7  # Start at 70% of current price
    
    for i in range(90):
        date_point = current_date - timedelta(days=90-i)
        daily_change = random.uniform(-0.05, 0.05)
        base_price = base_price * (1 + daily_change)
        
        price_history.append({
            "date": date_point.strftime("%Y-%m-%d"),
            "price": round(base_price, 2),
            "volume": round(random.uniform(token_data["price"] * 1000000, token_data["price"] * 10000000), 0)
        })
    
    # If we have a request text, try to generate relevant content
    if request_text:
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
            token_prompt = ChatPromptTemplate.from_template(
                """You are a token analysis service providing insights on cryptocurrencies.
                Based on this request, generate a token analysis:
                
                Request: {request_text}
                Service: {service_name}
                
                Format your response as a JSON object with these sections:
                - title: A descriptive title for the token analysis
                - summary: A concise overview of the token (3-4 sentences)
                - strengths: Array of 3-4 strengths of the token/project
                - weaknesses: Array of 2-3 weaknesses or concerns
                - technical_indicators: Object with 3-4 technical indicators and their values
                - fundamental_factors: Array of 3-4 fundamental factors affecting the token
                - investment_outlook: Short, medium, and long-term outlook
                
                All sections should be specific to the request provided.
                """
            )
            
            token_chain = token_prompt | llm | JsonOutputParser()
            result = token_chain.invoke({
                "request_text": request_text,
                "service_name": service_name
            })
            
            # Add token data and price history to the result
            result["token_data"] = token_data
            result["price_history"] = price_history
            
            return result
        except Exception as e:
            print(f"Error generating token analysis content: {str(e)}")
            # Fall through to default
    
    # Default token result if no request text or if generation fails
    return {
        "title": f"{token_data['name']} Token Analysis",
        "summary": f"Comprehensive analysis of {token_data['name']} token fundamentals, technicals, and market positioning.",
        "token_data": token_data,
        "price_history": price_history,
        "strengths": [
            "Strong development team with consistent delivery",
            "Growing ecosystem and partnerships",
            "Solid tokenomics with deflationary mechanism",
            "High security rating from multiple audit firms"
        ],
        "weaknesses": [
            "Increasing competition in the same market segment",
            "Regulatory uncertainty in key markets",
            "Concentration of tokens among few large holders"
        ],
        "technical_indicators": {
            "RSI": round(random.uniform(30, 70), 1),
            "MACD": "Bullish crossover forming",
            "Moving Averages": "Trading above 50-day MA, approaching 200-day MA",
            "Bollinger Bands": "Contracting, suggesting decreased volatility"
        },
        "fundamental_factors": [
            "Upcoming protocol upgrade scheduled for next quarter",
            "Increasing institutional interest and adoption",
            "Growing TVL across protocol's applications",
            "Expansion into additional blockchain networks"
        ],
        "investment_outlook": {
            "short_term": random.choice(["Neutral", "Slightly Bullish", "Bullish", "Slightly Bearish"]),
            "mid_term": random.choice(["Neutral", "Bullish", "Very Bullish"]),
            "long_term": random.choice(["Bullish", "Very Bullish", "Extremely Bullish"])
        }
    }

def generate_data_feed_result(service_name, request_text=""):
    """Generate mock data feed results based on the request text"""
    # Define popular tokens and their recent price ranges
    tokens = {
        "ETH": {"min": 1500, "max": 3500, "decimals": 2},
        "BTC": {"min": 25000, "max": 65000, "decimals": 2},
        "MATIC": {"min": 0.5, "max": 1.5, "decimals": 4},
        "AAVE": {"min": 50, "max": 200, "decimals": 2},
        "UNI": {"min": 3, "max": 8, "decimals": 3}
    }
    
    # Determine what tokens to use based on request text
    selected_tokens = []
    
    if not request_text:
        # Default selection
        selected_tokens = ["ETH", "BTC", "AAVE", "UNI"]
    else:
        request_lower = request_text.lower()
        # Check for specific tokens in the request
        for token in tokens.keys():
            if token.lower() in request_lower:
                selected_tokens.append(token)
        
        # Add major tokens by default
        if "bitcoin" in request_lower or "btc" in request_lower:
            if "BTC" not in selected_tokens:
                selected_tokens.append("BTC")
        
        if "ethereum" in request_lower or "eth" in request_lower:
            if "ETH" not in selected_tokens:
                selected_tokens.append("ETH")
        
        # Ensure we have at least 3 tokens
        if len(selected_tokens) < 3:
            remaining = ["ETH", "BTC", "AAVE", "UNI"]
            for token in remaining:
                if token not in selected_tokens:
                    selected_tokens.append(token)
                    if len(selected_tokens) >= 3:
                        break
    
    # Determine feed type based on request
    feed_type = "price"
    if request_text and any(term in request_text.lower() for term in ["volume", "liquidity", "trading"]):
        feed_type = "market"
    elif request_text and any(term in request_text.lower() for term in ["yield", "apr", "apy", "interest"]):
        feed_type = "yield"
    elif request_text and any(term in request_text.lower() for term in ["gas", "fee", "transaction"]):
        feed_type = "gas"
    
    # Generate feed title and description based on type
    if feed_type == "price":
        title = "Token Price Data Feed"
        description = f"Real-time price data for {', '.join(selected_tokens[:-1])} and {selected_tokens[-1]}"
    elif feed_type == "market":
        title = "Market Volume & Liquidity Feed"
        description = f"Trading volume, liquidity depth, and market activity for {', '.join(selected_tokens)}"
    elif feed_type == "yield":
        title = "DeFi Yield & APY Feed"
        description = f"Current yield rates, APR/APY metrics for staking and lending protocols"
    elif feed_type == "gas":
        title = "Ethereum Gas Price Feed"
        description = "Real-time gas prices for Ethereum network transactions across priority levels"
    
    # Generate appropriate feed items based on type
    feed_items = []
    
    if feed_type == "price" or feed_type == "market":
        # Generate price/market data for selected tokens
        for token in selected_tokens:
            token_config = tokens[token]
            base_price = random.uniform(token_config["min"], token_config["max"])
            
            # Generate several time points
            for i in range(3):
                timestamp = datetime.now() - timedelta(minutes=i*15)
                
                # Add slight variations for each time point
                price_variation = base_price * random.uniform(-0.02, 0.02)
                current_price = round(base_price + price_variation, token_config["decimals"])
                
                # Create data point
                data_point = {
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "token": token,
                    "price": current_price,
                    "change_24h": f"{random.uniform(-5, 5):.2f}%"
                }
                
                if feed_type == "market":
                    # Add market specific metrics
                    data_point.update({
                        "volume_24h": f"${random.uniform(5, 500):.2f}M",
                        "liquidity": f"${random.uniform(10, 1000):.2f}M",
                        "trades": random.randint(1000, 50000)
                    })
                
                feed_items.append(data_point)
                
    elif feed_type == "yield":
        # Generate yield data for various protocols
        protocols = ["Aave", "Compound", "Curve", "Uniswap", "MakerDAO", "Lido", "Convex"]
        assets = ["ETH", "BTC", "USDC", "DAI", "USDT"]
        
        for protocol in protocols[:4]:  # Take first 4 protocols
            for asset in assets[:3]:  # Take first 3 assets
                timestamp = datetime.now() - timedelta(minutes=random.randint(5, 60))
                
                feed_items.append({
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "protocol": protocol,
                    "asset": asset,
                    "apy": f"{random.uniform(0.5, 15):.2f}%",
                    "tvl": f"${random.uniform(10, 500):.2f}M",
                    "strategy": random.choice(["Lending", "Staking", "Liquidity Mining"])
                })
                
    elif feed_type == "gas":
        # Generate gas price data
        for i in range(10):
            timestamp = datetime.now() - timedelta(minutes=i*6)
            base_gwei = random.randint(20, 80)
            
            feed_items.append({
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "network": "Ethereum",
                "base_fee": f"{base_gwei} gwei",
                "priority_fee": {
                    "slow": f"{random.randint(1, 3)} gwei",
                    "standard": f"{random.randint(2, 5)} gwei",
                    "fast": f"{random.randint(5, 10)} gwei"
                },
                "estimated_confirmation": {
                    "slow": f"{random.randint(3, 10)} mins",
                    "standard": f"{random.randint(1, 3)} mins",
                    "fast": "< 1 min"
                },
                "block_number": 17000000 + i*5
            })
    
    # Sort by timestamp (newest first)
    feed_items = sorted(feed_items, key=lambda x: x["timestamp"], reverse=True)
    
    # If we have a request text, try to generate relevant content
    if request_text:
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
            feed_prompt = ChatPromptTemplate.from_template(
                """You are a DeFi data feed service. Generate details for a data feed based on this request:
                
                Request: {request_text}
                Feed Type: {feed_type}
                Selected Tokens: {tokens}
                
                Respond with a JSON object containing:
                - title: A title for the data feed
                - description: A detailed description of what data is being provided
                - source: The name of a realistic DeFi data aggregator (like "DeFi Pulse Analytics")
                - update_frequency: How often the data is updated (e.g., "5 minutes", "hourly")
                - data_quality_score: A quality score between 0.85 and 0.99
                - recommendation: A brief analysis of the data (2-3 sentences)
                """
            )
            
            feed_chain = feed_prompt | llm | JsonOutputParser()
            feed_result = feed_chain.invoke({
                "request_text": request_text,
                "feed_type": feed_type,
                "tokens": ", ".join(selected_tokens)
            })
            
            # Merge the generated content with our feed items
            feed_result["feed_items"] = feed_items
            feed_result["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            feed_result["data_source"] = "DeFi Llama API"
            return feed_result
        except Exception as e:
            print(f"Error generating feed content: {str(e)}")
            # Fallback to default if generation fails
            pass
            
    # Default response if no request text or if generation fails
    return {
        "title": title,
        "description": description,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "update_frequency": "5 minutes",
        "feed_items": feed_items,
        "data_quality_score": round(random.uniform(0.85, 0.99), 2),
        "source": "DeFi Llama Data Feed",
        "data_source": "DeFi Llama API",
        "recommendation": f"Based on current data trends, consider monitoring {selected_tokens[0]} and {selected_tokens[1]} for potential opportunities."
    }

def generate_optimization_result(service_name, request_text=""):
    """Generate mock optimization results based on the request text"""
    # Create optimization scenarios
    scenarios = []
    
    for i in range(3):
        protocol_name = random.choice(["Aave", "Compound", "Uniswap", "Curve", "Balancer"])
        asset_type = random.choice(["Lending", "Staking", "Liquidity Provision"])
        current_apy = round(random.uniform(1, 8), 2)
        optimized_apy = round(current_apy * random.uniform(1.1, 1.6), 2)
        
        scenario = {
            "name": f"Scenario {i+1}: {protocol_name} {asset_type} Optimization",
            "protocol": protocol_name,
            "asset_type": asset_type,
            "current_apy": f"{current_apy}%",
            "optimized_apy": f"{optimized_apy}%",
            "improvement": f"{round((optimized_apy - current_apy), 2)}%",
            "risk_level": random.choice(["Low", "Medium", "Medium-Low", "Medium-High"]),
            "complexity": random.choice(["Simple", "Moderate", "Complex"]),
            "timeframe": random.choice(["Short-term", "Medium-term", "Long-term"]),
            "capital_required": f"${random.randint(500, 10000)}",
            "current_cost": random.randint(100, 500),
            "optimized_cost": random.randint(50, 90)
        }
        
        scenarios.append(scenario)
    
    # Sort by improvement (best first)
    scenarios.sort(key=lambda x: float(x["improvement"].replace("%", "")), reverse=True)
    
    # If we have a request text, try to generate relevant content
    if request_text:
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
            optimization_prompt = ChatPromptTemplate.from_template(
                """You are a DeFi optimization service suggesting improvements to yield strategies.
                Based on this request, generate optimization recommendations:
                
                Request: {request_text}
                Service: {service_name}
                
                Format your response as a JSON object with these sections:
                - title: A descriptive title for the optimization recommendation
                - summary: A concise overview of the optimization strategy (3-4 sentences)
                - current_strategy: Description of typical current approach
                - optimized_strategy: Detailed explanation of the recommended optimized approach
                - benefits: Array of 3-4 specific benefits
                - considerations: Array of 2-3 important considerations or risks
                - implementation_steps: Array of 4-5 steps to implement the optimization
                
                All sections should be specific to the request provided.
                """
            )
            
            optimization_chain = optimization_prompt | llm | JsonOutputParser()
            result = optimization_chain.invoke({
                "request_text": request_text,
                "service_name": service_name
            })
            
            # Add scenarios to the result
            result["scenarios"] = scenarios
            
            return result
        except Exception as e:
            print(f"Error generating optimization content: {str(e)}")
            # Fall through to default
    
    # Default optimization result if no request text or if generation fails
    return {
        "title": f"{service_name} Yield Optimization",
        "summary": "Analysis of current yield strategies with optimization recommendations to maximize returns while managing risk.",
        "scenarios": scenarios,
        "current_strategy": "Basic single-protocol deposit strategy with standard parameters and manual rebalancing.",
        "optimized_strategy": "Multi-protocol strategy utilizing optimal asset allocation, automated rebalancing, and leveraging governance token incentives.",
        "benefits": [
            "Increase in overall APY by 20-30% compared to standard approaches",
            "Reduced impermanent loss through dynamic position management",
            "Better risk distribution across multiple protocols",
            "Potential for additional governance token rewards"
        ],
        "considerations": [
            "Higher gas costs due to more frequent transactions",
            "Increased complexity requiring monitoring tools",
            "Smart contract risk spread across multiple protocols"
        ],
        "implementation_steps": [
            "Audit current positions and calculate baseline performance",
            "Set up wallets and establish positions in recommended protocols",
            "Configure automation tools for rebalancing and harvesting",
            "Monitor performance and adjust parameters as needed",
            "Periodically review strategy against market conditions"
        ],
        "recommended_scenario": scenarios[0]["name"],
        "estimated_annual_savings": f"${round(scenarios[0]['original_cost'] - scenarios[0]['optimized_cost'], 2) * 12}",
        "implementation_notes": "Implementation can begin immediately after approval. Expected completion within 2-4 weeks."
    } 
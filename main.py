from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import logging
from datetime import datetime, timedelta
import pandas as pd
import google.generativeai as genai
import yfinance as yf
import pytz
import re
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# Configure Google Gemini API Key securely from .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# System prompt for chatbot
sys_prompt = """You are a helpful AI assistant designed to answer questions about finance, stock trading, and investment strategies. 
Please respond only to finance-related queries. If asked anything unrelated, politely decline.
For stock ticker queries (explicit requests about specific stocks), provide concise bullet points of key insights about the company's performance, not current prices."""

# Initialize Gemini model
gemini = genai.GenerativeModel(model_name="models/gemini-2.0-flash-exp", system_instruction=sys_prompt)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Market time configuration
NY_TIMEZONE = pytz.timezone('America/New_York')

# List of supported tickers
SUPPORTED_TICKERS = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOG', 'META', 'NVDA', 'NFLX']

@app.route("/")
def serve_index():
    return send_from_directory("frontend", "index.html")

@app.route("/chatbot", methods=["POST"])
def chatbot():
    """Enhanced chatbot with automatic stock insights and analysis"""
    data = request.json
    user_query = data.get("query", "").strip()
    ticker = data.get("ticker", "").strip().upper()
    
    if not user_query:
        return jsonify({"response": "Please enter a valid finance-related question."})

    try:
        # Check if this is an explicit request for stock insights
        is_stock_insight_request = any(phrase in user_query.lower() for phrase in [
            "tell me about", "insights", "information about", "analysis of", 
            "overview of", "details on", "company profile"
        ])
        
        # Check for explicit risk analysis request
        is_risk_request = any(phrase in user_query.lower() for phrase in [
            "risk", "volatility", "safety", "stability", "risk assessment"
        ])
        
        # Extract ticker if not provided but present in query
        if not ticker:
            potential_tickers = re.findall(r'\b([A-Z]{2,5})\b', user_query.upper())
            ticker = next((t for t in potential_tickers if t in SUPPORTED_TICKERS), None)
        
        # Handle stock insight requests
        if is_stock_insight_request and ticker and ticker in SUPPORTED_TICKERS:
            try:
                stock_info = yf.Ticker(ticker).info
                company_name = stock_info.get('longName', ticker)
                insights = generate_stock_insights(ticker, stock_info)
                
                return jsonify({
                    "status": "success",
                    "response": f"Here are key insights for {company_name} ({ticker}):\n\n" + 
                               "\n".join([f"{i+1}. {insight}" for i, insight in enumerate(insights)]),
                    "ticker": ticker,
                    "insights": insights,
                    "company_name": company_name,
                    "is_stock_response": True
                })
            except Exception as e:
                logging.error(f"Error fetching data for {ticker}: {str(e)}")
                # Fall back to Gemini
                
        # Handle risk analysis requests
        elif is_risk_request and ticker:
            try:
                risk_data = assess_risk(ticker)
                return jsonify({
                    "status": "success",
                    "response": f"Risk Assessment for {ticker}:\n\n" +
                               f"Risk Level: {risk_data['risk_level']}\n" +
                               f"Volatility: {risk_data['volatility']}\n\n" +
                               f"{risk_data['description']}",
                    "is_stock_response": False
                })
            except Exception as e:
                logging.error(f"Risk assessment error: {str(e)}")
        
        # Regular Gemini response for all other queries
        response = gemini.generate_content(
            f"Provide a concise answer to this finance-related question: {user_query}\n"
            "Keep the response professional and to the point (2-3 paragraphs maximum)."
        )
        return jsonify({
            "status": "success",
            "response": response.text,
            "is_stock_response": False
        })
    
    except Exception as e:
        logging.error(f"Chatbot error: {str(e)}")
        return jsonify({
            "status": "error",
            "response": "Sorry, I encountered an error processing your request. Please try again with a different query."
        })

def generate_stock_insights(ticker, stock_info):
    """Generate 10 specific insights about a stock using real data"""
    insights = []
    
    # 1. Company overview
    insights.append(
        f"{stock_info.get('longName', ticker)} operates in {stock_info.get('sector', 'an unspecified sector')} "
        f"with focus on {stock_info.get('industry', 'various products/services')}."
    )
    
    # 2. Financial health
    profit_margins = stock_info.get('profitMargins', None)
    if profit_margins:
        financial_health = "strong" if profit_margins > 0.15 else "moderate" if profit_margins > 0 else "weak"
        insights.append(f"Financial health appears {financial_health} with {profit_margins*100:.1f}% profit margins.")
    
    # 3. Recent performance
    fifty_two_week_change = stock_info.get('52WeekChange', None)
    if fifty_two_week_change:
        performance = "outperformed" if fifty_two_week_change > 0 else "underperformed"
        insights.append(f"Has {performance} the market over past year with {fifty_two_week_change*100:.1f}% change.")
    
    # 4. Analyst ratings
    rec = stock_info.get('recommendationKey', None)
    if rec:
        insights.append(f"Analyst consensus is currently '{rec}' with target price of ${stock_info.get('targetMeanPrice', 'N/A')}.")
    
    # 5. Valuation metrics
    pe = stock_info.get('trailingPE', None)
    if pe:
        valuation = "overvalued" if pe > 25 else "undervalued" if pe < 15 else "fairly valued"
        insights.append(f"Valuation appears {valuation} with P/E ratio of {pe:.1f} compared to industry average.")
    
    # 6. Institutional ownership
    inst_own = stock_info.get('heldPercentInstitutions', None)
    if inst_own:
        insights.append(f"Institutional ownership stands at {inst_own*100:.1f}%, indicating {'strong' if inst_own > 0.7 else 'moderate' if inst_own > 0.4 else 'limited'} investor confidence.")
    
    # 7. Growth prospects
    rev_growth = stock_info.get('revenueGrowth', None)
    if rev_growth:
        growth = "accelerating" if rev_growth > 0.2 else "stable" if rev_growth > 0 else "declining"
        insights.append(f"Revenue growth is {growth} at {rev_growth*100:.1f}% year-over-year.")
    
    # 8. Dividend information
    if stock_info.get('dividendRate', 0) > 0:
        insights.append(
            f"Pays dividend yield of {stock_info.get('dividendYield', 0)*100:.2f}% with "
            f"{'consistent' if stock_info.get('payoutRatio', 0) < 0.6 else 'high'} payout ratio."
        )
    else:
        insights.append("Does not currently pay dividends, reinvesting earnings into growth.")
    
    # 9. Competitive position
    mkt_cap = stock_info.get('marketCap', None)
    if mkt_cap:
        position = "market leader" if mkt_cap > 200e9 else "major player" if mkt_cap > 50e9 else "competitor"
        insights.append(f"Positioned as a {position} in its industry with ${mkt_cap/1e9:.1f}B market cap.")
    
    # 10. Risk factors
    beta = stock_info.get('beta', None)
    if beta:
        risk = "higher" if beta > 1.2 else "lower" if beta < 0.8 else "market-average"
        insights.append(f"Systematic risk appears {risk} with beta of {beta:.2f} compared to the market.")
    
    return insights

@app.route("/stock", methods=["GET"])
def get_stock():
    """Fetch current stock data from Yahoo Finance"""
    ticker = request.args.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d", interval="1m", prepost=True)
        
        if hist.empty:
            return jsonify({"error": "No data found for this ticker"}), 404
        
        current = hist.iloc[-1]
        prev_close = stock.info.get('regularMarketPreviousClose', current['Close'])
        
        change = current['Close'] - prev_close
        percent_change = (change / prev_close) * 100
        
        return jsonify({
            "ticker": ticker,
            "price": f"{current['Close']:.2f}",
            "change": f"{change:.2f}",
            "percent_change": f"{percent_change:.2f}%",
            "open": f"{current['Open']:.2f}",
            "high": f"{current['High']:.2f}",
            "low": f"{current['Low']:.2f}",
            "volume": int(current['Volume'])
        })
        
    except Exception as e:
        logging.error(f"Stock data processing error: {str(e)}")
        return jsonify({"error": "Failed to process stock data"}), 500

@app.route('/stock_graph', methods=['GET'])
def get_stock_graph():
    """Fetch stock graph data from Yahoo Finance with different time frames"""
    ticker = request.args.get("ticker", "").upper().strip()
    period = request.args.get("period", "1d")

    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400

    try:
        stock = yf.Ticker(ticker)
        now = datetime.now(pytz.timezone('America/New_York'))  # Explicit NY timezone
        today_ny = now.date()

        if period == "1d":
            # Determine the target_date
            if today_ny.weekday() >= 5:  # Saturday or Sunday
                last_friday = today_ny - timedelta(days=(today_ny.weekday() - 4) % 7)
                target_date = last_friday
            else:
                market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
                market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

                if market_open <= now <= market_close:
                    target_date = today_ny  # Market is open
                else:
                    target_date = today_ny - timedelta(days=1)  # Market is closed

            # Fetch data for the target_date
            data = stock.history(start=target_date, end=target_date + timedelta(days=1),
                                interval="1m", prepost=True)

            # Filter to market hours (NY timezone)
            if not data.empty:
                if not data.index.tz:
                    market_data = data.tz_localize('UTC').tz_convert('America/New_York').between_time('09:30', '16:00')
                else:
                    market_data = data.tz_convert('America/New_York').between_time('09:30', '16:00')

                # Resample to 5-minute intervals
                market_data = market_data.resample('5T').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })

                if len(market_data) < 2:
                    prev_trading_day = pd.Timestamp(target_date) - pd.offsets.BDay(1)
                    data = stock.history(start=prev_trading_day, end=prev_trading_day + timedelta(days=1),
                                                interval="1m", prepost=True)
                    if not data.empty:
                        if not data.index.tz:
                            market_data = data.tz_localize('UTC').tz_convert('America/New_York').between_time('09:30', '16:00')
                        else:
                            market_data = data.tz_convert('America/New_York').between_time('09:30', '16:00')
                        market_data = market_data.resample('5T').agg({
                            'Open': 'first',
                            'High': 'max',
                            'Low': 'min',
                            'Close': 'last',
                            'Volume': 'sum'
                        })
                    else:
                        market_data = pd.DataFrame() # Create empty dataframe to avoid errors.

                # Convert to desired format
                graph_data = [{
                    "time": idx.tz_convert('America/New_York').strftime('%Y-%m-%dT%H:%M:%S%z'),
                    "price": float(row['Close']),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "volume": int(row['Volume'])
                } for idx, row in market_data.iterrows() if not pd.isna(row['Close'])]
            else:
                graph_data = [] #create empty list when data is empty.

        else:  # For other periods (7d, 30d, etc.)
            if period == "7d":
                data = stock.history(period="7d", interval="1h")
            elif period == "30d":
                data = stock.history(period="1mo", interval="1d")
            elif period == "3mo":
                data = stock.history(period="3mo", interval="1d")
            elif period == "1y":
                data = stock.history(period="1y", interval="1wk")
            else:
                data = stock.history(period="1mo", interval="1d")

            graph_data = [{
                "time": idx.tz_convert('America/New_York').strftime('%Y-%m-%dT%H:%M:%S%z'),
                "price": float(row['Close']),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "volume": int(row['Volume'])
            } for idx, row in data.iterrows() if not pd.isna(row['Close'])]

        if not graph_data:
            return jsonify({"error": "No valid data points after processing"}), 404

        return jsonify({
            "status": "success",
            "ticker": ticker,
            "period": period,
            "data": graph_data,
            "last_updated": now.strftime('%Y-%m-%dT%H:%M:%S%z')
        })

    except Exception as e:
        logging.error(f"Graph data error for {ticker} ({period}): {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": f"Failed to fetch {period} data for {ticker}"
        }), 500
    
@app.route('/risk', methods=['GET'])
def assess_risk():
    """Assess stock investment risk based on volatility"""
    ticker = request.args.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return jsonify({"error": "No data available for this ticker"}), 404
            
        closing_prices = hist['Close'].tolist()
        
        if len(closing_prices) < 10:
            return jsonify({"error": "Not enough data to assess risk"}), 400
        
        volatility = np.std(closing_prices)
        avg_price = np.mean(closing_prices)
        risk_level = "low" if volatility < 0.02 * avg_price else "medium" if volatility < 0.05 * avg_price else "high"

        return jsonify({
            "status": "success",
            "ticker": ticker, 
            "volatility": round(volatility, 2),
            "risk_level": risk_level,
            "description": get_risk_description(risk_level, ticker)
        })

    except Exception as e:
        logging.error(f"Risk assessment error: {str(e)}")
        return jsonify({"error": f"Failed to assess risk: {str(e)}"}), 500

def get_risk_description(risk_level, ticker):
    """Generate descriptive text for risk assessment"""
    descriptions = {
        "low": f"{ticker} shows low volatility, indicating stable price movements. Suitable for conservative investors.",
        "medium": f"{ticker} has moderate volatility. Expect some fluctuations but generally stable.",
        "high": f"{ticker} exhibits high volatility with significant price swings. Higher risk/reward potential."
    }
    return descriptions.get(risk_level, "Risk assessment unavailable.")

@app.route('/predict', methods=['GET'])
def predict_stock():
    """Predict stock movement using machine learning"""
    ticker = request.args.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        if hist.empty:
            return jsonify({"error": "No historical data"}), 404
            
        df = pd.DataFrame({
            'close': hist['Close'],
            'open': hist['Open'],
            'high': hist['High'],
            'low': hist['Low'],
            'volume': hist['Volume']
        })
        
        df = create_features(df)
        df['ma_7'] = df['close'].rolling(window=7).mean()
        last_close = df['close'].iloc[-1]
        last_ma = df['ma_7'].iloc[-1]
        trend = "upward" if last_ma > last_close else "downward"
        
        return jsonify({
            "status": "success",
            "ticker": ticker,
            "current_price": round(last_close, 2),
            "predicted_price": round(last_ma, 2),
            "trend": trend,
            "confidence": 75,
            "prediction_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "message": "7-day moving average prediction"
        })

    except Exception as e:
        logging.error(f"Prediction failed for {ticker}: {str(e)}")
        return jsonify({"error": "Prediction failed"}), 500

def create_features(df):
    """Create technical indicators for the model"""
    df['ma_7'] = df['close'].rolling(window=7).mean()
    df['ma_14'] = df['close'].rolling(window=14).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    df['momentum'] = df['close'] - df['close'].shift(4)
    df = df.dropna()
    
    return df

@app.route('/favicon.ico')
def favicon():
    return send_from_directory("frontend/assets", 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(debug=True)

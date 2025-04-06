# 💹 Finance Chatbot & Stock Analysis Web App

An AI-powered finance chatbot and stock analysis web application built with **Flask**, **Google Gemini**, and **Yahoo Finance**. The app can handle user queries about investing, stock market insights, risk analysis, and provides real-time stock data and visualizations.

---

## 🌟 Features

- 🔎 **Finance Chatbot**  
  Responds to finance, investment, and trading-related questions using Google Gemini (Gemini 2.0 Flash).

- 📈 **Stock Insights**  
  Get concise bullet-point insights for supported tickers like AAPL, MSFT, TSLA, etc.

- ⚠️ **Risk Assessment**  
  Analyze volatility, beta, and overall risk profile of stocks.

- 📊 **Real-Time Stock Data**  
  View current stock price, % change, open/high/low/volume data using `yfinance`.

- 🕰️ **Dynamic Graphs**  
  Visualize price trends across multiple timeframes: intraday, weekly, monthly, etc.

---

## 🧠 Tech Stack

- **Backend:** Python, Flask, Flask-CORS  
- **AI Model:** Google Gemini (via `google.generativeai`)  
- **Finance Data:** Yahoo Finance API (`yfinance`)  
- **Frontend:** Static HTML/CSS/JS (located in `/frontend`)  
- **Timezone Handling:** `pytz`, `datetime`  
- **Data Processing:** `pandas`, `numpy`, `re`

---

## 🚀 Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/your-username/finance-chatbot-app.git
cd finance-chatbot-app
```

## 2. Install Dependencies
Make sure you have Python 3.8+ and pip:

```bash

pip install -r requirements.txt
```
## 3. Set Your Gemini API Key
In app.py, replace:
```python

genai.configure(api_key="YOUR_API_KEY_HERE")
```
Or better, use an environment variable:

```bash

export GEMINI_API_KEY=your-api-key
```
And update app.py like this:

```python

import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
```
## 4. Run the App
```bash

python app.py
```
Then open your browser and go to:
``` bash
📍 http://localhost:5000
```

📂 Project Structure
```bash

finance-chatbot-app/
│
├── frontend/                  # Static frontend assets
│   └── index.html
│
├── app.py                     # Main Flask application
├── requirements.txt           # Python dependencies
└── README.md                  # You're here!
```
## 📌 To-Do / Future Enhancements
 Expand to more stock tickers dynamically

 Add user authentication

 Deploy on Heroku / Render / AWS

 Interactive charts (Plotly.js, Chart.js)

 Real-time news scraping (via NewsAPI)


## 🤝 Contributions
Feel free to open issues or PRs! Let’s build a smarter financial assistant together 💸

---



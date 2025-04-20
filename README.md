# Financial-Analysis-System-with-RAG-and-LLM-Integration
![image](https://github.com/user-attachments/assets/1171b06e-c719-4126-b75b-d78466e9f218)

This system enables the generation of AI-powered financial analysis reports using financial news, economic indicators, stock data, and financial filings. It integrates RAG (Retrieval-Augmented Generation), semantic search (FAISS), and LLM-generated insights into a structured PDF output. Access is controlled via an API key with rate limiting and timeout enforcement.

# Authentication Method: Env-based API key
Valid Keys: Defined in VALID_KEYS list in auth.py

# Rate Limiting
Limit: 1 request per 30 seconds
Mechanism: File-based time tracking (last_run.txt)
Violation Behavior:
  Exits the script if the limit is exceeded
  Logs the event in logs/app.log

# Timeout Mechanism
Timeout Duration: 180 seconds
Applied On: Full PDF generation process

# Automatic Query Parsing Using Gemini
Extracts:
  symbol (e.g., AAPL, MSFT)
  start_date (optional)
  end_date (optional)
If no dates are provided, all historical data is used.

# Data Sources Accessed
  Alpha Vantage API – Stock Prices, Financial Reports, Macroeconomic Indicators
  NewsAPI – Financial news articles
  
# Database
  PostgreSQL – Financial report data

# Vector Database
FAISS Indexes – Semantic search for:
  News
  Stock trends
  Economic indicators
  Financial reports

# AI Insights (RAG + Gemini)
Executive Summary
Market Analysis
Risk Analysis
Data Sources & Methodology

# Setup Instructions
Ensure you have the following installed on your system:
  Docker
  Docker Compose
  


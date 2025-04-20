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
  -Docker, 
  -Docker Compose
- Clone the Repository
- Place .env.example in Project Root with your .env file that includes the required API keys and database URL.
- Build and Start the Docker Environment
- Wait for Initialization The PostgreSQL container will initialize the database using financial_db.sql and the app will run the report generation flow.
- Check Output Once complete, your PDF report will be available in the outputs/ directory of the container.
- View Logs: "docker logs financial_analysis_app"

- Remark 1: A sample query is hardcoded in main.py. You can change it when using or better you can modify it to take inputs from CLI.
- Remark 2: Actually, there is no need to call API's for data and the pushed code doesn't. This is because the .sql file already contains this data.
- Remark 3: Furthermore, the vectors of this database can be found in the folders: faiss_econ_index, faiss_financial_index, faiss_gemini_index, and faiss_price_index which store Stock market, Financial news feeds, Company financial reports, and Economic indicators.
- Remark 4: The main code already reads these vector databases when present. It doesn't make unnecessary API calls.
  
# Testing Strategy
Run functional tests by triggering the system with different queries (You can test different financial queries by editing the hardcoded question inside main.py) and checking:
  Console logs (via Docker)
  Generated PDFs in /outputs
  Logs saved in /logs/app.log

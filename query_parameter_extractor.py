import os
import json
from typing import Optional, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, timedelta

# Load Gemini
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Prompt template
EXTRACTION_PROMPT = (
    "You are an intelligent financial assistant. Given the user's natural language query, extract the following as a JSON object:\n"
    "- 'symbol': The stock ticker of the company mentioned (e.g., 'AAPL' for Apple, 'MSFT' for Microsoft). "
    "If only a company name is provided, infer and return its ticker.\n"
    "- 'start_date': The start date of the time span (in format YYYY-MM-DD)\n"
    "- 'end_date': The end date of the time span (in format YYYY-MM-DD)\n\n"
    "If any value is not found or not clearly stated, return null for that field.\n"
    "Respond ONLY with valid JSON.\n\n"
    "Query: {query}"
)

prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)

def extract_parameters_with_gemini(query: str) -> Dict[str, Optional[str]]:
    try:
        chain = prompt | llm
        response = chain.invoke({"query": query})
        content = response.content.strip()

        # ✅ Clean up LLM markdown-wrapped response
        if content.startswith("```"):
            content = content.strip("`").replace("json", "").strip()

        print("📨 Gemini Response:", content)
        parsed = json.loads(content)

        symbol = parsed.get("symbol")
        start_date = parsed.get("start_date")
        end_date = parsed.get("end_date")

        # ✅ Apply default date range if missing
        if not start_date or not end_date:
            today = datetime.today()
            one_year_ago = today - timedelta(days=365)
            start_date = one_year_ago.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            print(f"⏳ Defaulted to last year: {start_date} to {end_date}")

        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date
        }

    except Exception as e:
        print(f"⚠️ Failed to extract parameters: {e}")
        return {"symbol": None, "start_date": None, "end_date": None}

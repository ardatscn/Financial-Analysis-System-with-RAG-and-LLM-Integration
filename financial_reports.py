# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 23:25:08 2025

@author: PCA
"""

import os
import aiohttp
import asyncio
import pandas as pd
from dotenv import load_dotenv
from models import FinancialReport
from database import postgres_engine
from sqlalchemy import Table, Column, Float, String, Date, Integer, MetaData, text
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

metadata = MetaData()

financial_table = Table("financial_reports", metadata,
    Column("symbol", String),
    Column("fiscal_date", Date),
    Column("total_revenue", Float),
    Column("net_income", Float),
    Column("gross_profit", Float),
    Column("operating_income", Float),
)

metadata.create_all(postgres_engine)

async def fetch_financials(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "INCOME_STATEMENT",
        "symbol": symbol,
        "apikey": API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("quarterlyReports", [])

def parse_financials(raw_reports, symbol):
    cleaned = []
    for report in raw_reports:
        try:
            row = {
                "symbol": symbol,
                "fiscal_date": report["fiscalDateEnding"],
                "total_revenue": float(report.get("totalRevenue") or 0),
                "net_income": float(report.get("netIncome") or 0),
                "gross_profit": float(report.get("grossProfit") or 0),
                "operating_income": float(report.get("operatingIncome") or 0),
            }
            validated = FinancialReport(**row)
            cleaned.append(validated.dict())
        except Exception as e:
            print(f"[{symbol}] Skipped row: {e}")
    return cleaned

def save_financials_to_postgres(data):
    if data:
        with postgres_engine.begin() as conn:
            conn.execute(financial_table.insert(), data)
        print(f"✅ Saved {len(data)} financial rows to PostgreSQL.")

async def main():
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM", "BAC", "WFC", "GS", "MS", "XOM", "CVX", "BP", "COP", "UNH", "JNJ", "PFE", "MRK", "LLY"]
    for symbol in symbols:
        raw = await fetch_financials(symbol)
        parsed = parse_financials(raw, symbol)
        save_financials_to_postgres(parsed)

if __name__ == "__main__":
    asyncio.run(main())
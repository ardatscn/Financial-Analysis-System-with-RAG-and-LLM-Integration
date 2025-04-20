# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 23:32:49 2025

@author: PCA
"""

import os
import aiohttp
import asyncio
import pandas as pd
from dotenv import load_dotenv
from models import EconomicIndicator
from database import postgres_engine
from sqlalchemy import text
from datetime import datetime
from sqlalchemy import Table, Column, String, Float, Date, MetaData
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

metadata = MetaData()

economic_table = Table("economic_indicators", metadata,
    Column("indicator", String),
    Column("date", Date),
    Column("value", Float),
)

metadata.create_all(postgres_engine)

INDICATORS = {
    "CPI": "CPI",
    "Inflation": "INFLATION",
    "FederalFundsRate": "FEDERAL_FUNDS_RATE",
    "Unemployment": "UNEMPLOYMENT"
}

async def fetch_indicator(indicator_name, function_name):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": function_name,
        "apikey": API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            raw = await resp.json()
            return raw

def parse_indicator(indicator_name, raw_data):
    key = "data"
    records = raw_data.get(key, [])
    parsed = []

    for r in records:
        try:
            validated = EconomicIndicator(
                indicator=indicator_name,
                date=r["date"],
                value=float(r["value"]) if r["value"] else None
            )
            parsed.append(validated.dict())
        except Exception as e:
            print(f"[{indicator_name}] Skipped row: {e}")

    return parsed

def save_to_postgres(data):
    if data:
        with postgres_engine.begin() as conn:
            conn.execute(economic_table.insert(), data)
            print(f"✅ Saved {len(data)} rows to PostgreSQL.")

async def main():
    for name, function in INDICATORS.items():
        raw = await fetch_indicator(name, function)
    
        # 🧪 Diagnostic checks:
        print(f"\n🟡 Raw response for {name}:")
        print(raw if raw else "❌ No response received.")
    
        # Check for rate limit or API error
        if "Note" in raw:
            print(f"⚠️ Rate limit notice for {name}: {raw['Note']}")
            continue
        if "Error Message" in raw:
            print(f"❌ API error for {name}: {raw['Error Message']}")
            continue
    
        parsed = parse_indicator(name, raw)
        save_to_postgres(parsed)

if __name__ == "__main__":
    asyncio.run(main())

import os
import aiohttp
import asyncio
import pandas as pd
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from models import StockPrice
from database import postgres_engine
from sqlalchemy import Table, Column, Float, String, Date, Integer, MetaData, text

# Load environment variables
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Define SQLAlchemy table for PostgreSQL
metadata = MetaData()

stock_table = Table("stock_prices", metadata,
    Column("date", Date),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("volume", Integer),
    Column("symbol", String)
)

metadata.create_all(postgres_engine)

@retry(
    retry=retry_if_exception_type(aiohttp.ClientError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30)
)

def clear_stock_prices_table():
    with postgres_engine.begin() as conn:
        conn.execute(text("DELETE FROM stock_prices"))
        print("🧹 Cleared previous stock data from PostgreSQL.")

async def fetch_daily_stock(symbol):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY,
        "outputsize": "full"
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params, headers=headers) as resp:
            if resp.status == 429:
                raise aiohttp.ClientError("Rate limit hit. Retrying...")
            elif resp.status != 200:
                raise aiohttp.ClientError(f"API error: {resp.status}")
            return await resp.json()

def parse_daily_stock(json_data, symbol):
    if "Time Series (Daily)" not in json_data:
        print(f"[{symbol}] ⚠️ No 'Time Series (Daily)' in response.")
        print(json_data)
        return None

    time_series = json_data["Time Series (Daily)"]
    df = pd.DataFrame(time_series).T

    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=False)

    df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    }, inplace=True)

    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=["close"], inplace=True)

    df["symbol"] = symbol
    df.reset_index(inplace=True)
    df.rename(columns={"index": "date"}, inplace=True)
    df["date"] = df["date"].astype(str)  # Ensure date is string for pydantic

    # ✅ Validate using Pydantic
    valid_rows = []
    for row in df.to_dict(orient="records"):
        try:
            validated = StockPrice(**row)
            valid_rows.append(validated.dict())
        except Exception as e:
            print(f"[{symbol}] Skipping invalid row: {e}")

    if not valid_rows:
        print(f"[{symbol}] ❌ No valid data to return after validation.")
        return None

    df_clean = pd.DataFrame(valid_rows)

    # ✅ Fix encoding to prevent UnicodeDecodeError
    for col in df_clean.select_dtypes(include=["object"]).columns:
        df_clean[col] = df_clean[col].astype(str).apply(lambda x: x.encode("utf-8", "replace").decode("utf-8"))

    return df_clean

def save_to_postgres(df):
    if df is not None and not df.empty:
        df = enforce_utf8(df)  # 💡 Apply fix here

        try:
            with postgres_engine.begin() as conn:
                conn.execute(stock_table.insert(), df.to_dict(orient="records"))
                print(f"✅ Saved {len(df)} rows to PostgreSQL.")
        except Exception as e:
            print(f"❌ Database insertion error: {e}")
            
def enforce_utf8(df):
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).apply(
            lambda x: x.encode("utf-8", errors="replace").decode("utf-8", errors="ignore")
        )
    return df

async def fetch_and_parse(symbol):
    try:
        raw = await fetch_daily_stock(symbol)

        if "Note" in raw:
            print(f"[{symbol}] ⚠️ Rate limit notice: {raw['Note']}")
            return None
        if "Error Message" in raw:
            print(f"[{symbol}] ❌ API error: {raw['Error Message']}")
            return None

        df = parse_daily_stock(raw, symbol)

        if df is not None:
            print(df.head())
            save_to_postgres(df)
        else:
            print(f"[{symbol}] No valid data parsed.")

        return df

    except Exception as e:
        print(f"[{symbol}] ❗ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM", "BAC", "WFC", "GS", "MS", "XOM", "CVX", "BP", "COP", "UNH", "JNJ", "PFE", "MRK", "LLY"]

    async def main():
        tasks = [fetch_and_parse(sym) for sym in symbols]
        await asyncio.gather(*tasks)
    
    clear_stock_prices_table()
    asyncio.run(main())

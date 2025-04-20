# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 20:49:42 2025

@author: PCA
"""

import os
import aiohttp
import asyncio
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from database import postgres_engine
from sqlalchemy import Table, Column, String, Text, DateTime, MetaData
from models import NewsArticle  # pydantic model to validate

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"

metadata = MetaData()

news_table = Table("news_articles", metadata,
    Column("title", String),
    Column("description", Text),
    Column("content", Text),
    Column("published_at", DateTime),
    Column("source", String),
    Column("url", String),
    Column("topic", String),
)

metadata.create_all(postgres_engine)

@retry(
    retry=retry_if_exception_type(aiohttp.ClientError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30)
)


def enforce_utf8(df):
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).apply(
            lambda x: x.encode("utf-8", errors="replace").decode("utf-8", errors="ignore")
        )
    return df

def save_news_to_postgres(df):
    if df is not None and not df.empty:
        df = enforce_utf8(df)

        # Ensure datetime format is compatible
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
        df = df.dropna(subset=["published_at"])
        df["published_at"] = df["published_at"].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
        
        valid_docs = []
        for row in df.to_dict(orient="records"):
            try:
                article = NewsArticle(**row)  # use pydantic to validate
                valid_docs.append(article.dict())
            except Exception as e:
                print(f"Skipping row due to validation error: {e}")

        if valid_docs:
            with postgres_engine.begin() as conn:
                conn.execute(news_table.insert(), valid_docs)
                print(f"✅ Saved {len(valid_docs)} news articles to PostgreSQL.")

async def fetch_news(session, query, page=1):
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    hundred_days_ago = today - timedelta(days=30)

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "pageSize": 20,
        "page": page,
        "from": hundred_days_ago.isoformat(),
        "to": today.isoformat()
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    async with session.get(NEWS_API_URL, params=params, headers=headers) as resp:
        if resp.status == 429:
            raise aiohttp.ClientError("Rate limit hit. Retrying...")
        elif resp.status != 200:
            print(await resp.text())  # for debugging
            raise aiohttp.ClientError(f"NewsAPI error: {resp.status}")
        return await resp.json()

def parse_news(json_data, topic):
    if "articles" not in json_data:
        print(f"[{topic}] No articles found.")
        return None

    articles = json_data["articles"]
    data = []

    for item in articles:
        data.append({
            "title": item.get("title"),
            "description": item.get("description"),       # ✅ Add this
            "content": item.get("content"),               # ✅ Add this
            "published_at": item.get("publishedAt"),
            "source": item.get("source", {}).get("name"),
            "url": item.get("url"),
            "topic": topic
        })

    return pd.DataFrame(data)

async def fetch_news_for_topic(topic):
    async with aiohttp.ClientSession() as session:
        try:
            raw = await fetch_news(session, topic)
            df = parse_news(raw, topic)
            print(df)
            if df is not None:
                print(df[["title", "published_at"]].head())
                save_news_to_postgres(df)  # ✅ Store after fetching
            return df
        except Exception as e:
            print(f"[{topic}] Error: {e}")
            return None

if __name__ == "__main__":
    topics = ["stock market", "inflation", "Federal Reserve", "Apple", "Microsoft"]

    async def main():
        tasks = [fetch_news_for_topic(topic) for topic in topics]
        results = await asyncio.gather(*tasks)

        # Combine all news into one DataFrame
        valid_frames = [r for r in results if r is not None and not r.empty]

        if not valid_frames:
            print("⚠️ No news articles were retrieved.")
            return
        
        all_news = pd.concat(valid_frames, ignore_index=True)
        print(all_news.head())
        print("\n✅ Combined News Articles:\n", all_news.head())

    asyncio.run(main())

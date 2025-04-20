import os
import pandas as pd
from database import postgres_engine
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

def load_stock_data():
    query = """
    SELECT symbol, date, close 
    FROM stock_prices
    ORDER BY symbol, date
    """
    df = pd.read_sql(query, postgres_engine)
    df["date"] = pd.to_datetime(df["date"])
    return df

def generate_quarterly_summaries(df):
    summaries = []
    metadata = []

    df['quarter'] = df['date'].dt.to_period('Q')

    for (symbol, quarter), group in df.groupby(['symbol', 'quarter']):
        group = group.sort_values("date")
        start_price = group.iloc[0]["close"]
        end_price = group.iloc[-1]["close"]
        delta = end_price - start_price
        trend = "increased" if delta > 0 else "decreased" if delta < 0 else "remained flat"
        pct = (delta / start_price) * 100 if start_price != 0 else 0

        q_start = group.iloc[0]["date"].date()
        q_end = group.iloc[-1]["date"].date()

        summary = (
            f"{symbol} stock price summary for Q{quarter.quarter} {quarter.year}:\n"
            f"From {q_start} to {q_end}, closing price {trend} from ${start_price:.2f} to ${end_price:.2f} "
            f"({pct:.2f}% change)."
        )

        summaries.append(summary)
        metadata.append({
            "source": "stock_price_summary",
            "symbol": symbol,
            "date_range": f"{q_start} to {q_end}"
        })

    return summaries, metadata

def build_price_faiss_index():
    df = load_stock_data()
    if df.empty:
        print("⚠️ No stock data found.")
        return

    summaries, metadatas = generate_quarterly_summaries(df)

    chunks = []
    chunk_metadata = []

    for text, meta in zip(summaries, metadatas):
        splits = splitter.split_text(text)
        chunks.extend(splits)
        chunk_metadata.extend([meta] * len(splits))

    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=chunk_metadata)
    vector_store.save_local("faiss_price_index")
    print("✅ Quarterly FAISS stock price index saved.")

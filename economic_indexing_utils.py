# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 09:15:42 2025

@author: PCA
"""

import os
import pandas as pd
from database import postgres_engine
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

def load_economic_indicators():
    query = "SELECT * FROM economic_indicators ORDER BY date DESC"
    df = pd.read_sql(query, postgres_engine)
    return df

def convert_to_text_blocks(df):
    text_blocks = []
    for _, row in df.iterrows():
        text = (
            f"Date: {row['date']}\n"
            f"Indicator: {row['indicator']}\n"
            f"Value: {row['value']} {row.get('unit', '')}\n"
        )
        text_blocks.append(text.strip())
    return text_blocks

def build_economic_faiss_index():
    df = load_economic_indicators()
    if df.empty:
        print("⚠️ No economic indicators found.")
        return

    texts = convert_to_text_blocks(df)
    chunks = []
    metadata = []

    for t in texts:
        splits = splitter.split_text(t)
        chunks.extend(splits)
        metadata.extend([{"source": "economic_indicator"}] * len(splits))

    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=metadata)
    vector_store.save_local("faiss_econ_index")
    print("✅ FAISS index with economic indicators saved.")

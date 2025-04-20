# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 08:59:28 2025

@author: PCA
"""

import os
import pandas as pd
from database import postgres_engine
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Set environment
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

# Step 1: Load structured financial report data
def load_structured_reports():
    query = "SELECT * FROM financial_reports"
    df = pd.read_sql(query, postgres_engine)
    return df

# Step 2: Turn rows into paragraphs
def convert_to_text(df):
    text_blocks = []
    for _, row in df.iterrows():
        block = f"Company: {row.get('symbol')}\n"
        for col in df.columns:
            if col != "symbol":
                val = row[col]
                block += f"{col.replace('_', ' ').title()}: {val}\n"
        text_blocks.append(block.strip())
    return text_blocks

# Step 3 & 4: Chunk and embed
def build_financial_faiss_index():
    df = load_structured_reports()
    if df.empty:
        print("⚠️ No financial reports found in the database.")
        return

    paragraphs = convert_to_text(df)
    chunks = []
    metadata = []

    for i, p in enumerate(paragraphs):
        splits = splitter.split_text(p)
        chunks.extend(splits)
        symbol = df.iloc[i].get("symbol", "Unknown")
        metadata.extend([{"source": f"report:{symbol}"}] * len(splits))

    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=metadata)
    vector_store.save_local("faiss_financial_index")
    print("✅ FAISS index with financial reports saved.")

def run_financial_query(question: str):
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.vectorstores import FAISS
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains import create_retrieval_chain
    from langchain_core.prompts import ChatPromptTemplate

    # Load FAISS financial report index
    vector_store = FAISS.load_local("faiss_financial_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

    # Prompt template (reusing the financial analyst tone)
    financial_prompt_template = (
        "You are a financial analyst AI. Based on the context provided from financial reports, "
        "answer the user's question clearly and accurately. Use specific numbers where possible.\n\n"
        "If you cannot find relevant data, say: 'No sufficient financial data found.'\n\n"
        "Context:\n{context}\n\n"
        "Question: {input}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", financial_prompt_template),
        ("human", "{input}")
    ])

    chain = create_retrieval_chain(retriever, create_stuff_documents_chain(llm, prompt))
    response = chain.invoke({"input": question})
    return response.get("answer", "⚠️ No response.")


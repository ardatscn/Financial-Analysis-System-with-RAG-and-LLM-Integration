# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 09:04:38 2025

@author: PCA
"""

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.retrievers import BaseRetriever
from typing import List
from langchain_core.documents import Document
from pydantic import Field

class StaticMultiRetriever(BaseRetriever):
    documents: List[Document] = Field(default_factory=list)

    def get_relevant_documents(self, query: str) -> List[Document]:
        return self.documents

# Set up API key
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Embeddings + LLM
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Prompt Template
combined_prompt_template = (
    "You are a financial analyst AI. Use the provided context — which includes financial news, "
    "company reports, stock price trends, and economic indicators — to answer the user’s question.\n\n"
    "Please summarize your answer using clear, professional bullet points.\n"
    "Each bullet should focus on a distinct insight or trend.\n\n"
    "If there is missing or insufficient data, mention that in one bullet.\n\n"
    "Context:\n{context}\n\n"
    "Question: {input}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", combined_prompt_template),
    ("human", "{input}")
])

# Main function: search both vector stores and combine chunks
def run_combined_rag_query(question: str, k=10):
    try:
        # Load both indexes
        news_index = FAISS.load_local("faiss_gemini_index", embeddings, allow_dangerous_deserialization=True)
        fin_index = FAISS.load_local("faiss_financial_index", embeddings, allow_dangerous_deserialization=True)
        econ_index = FAISS.load_local("faiss_econ_index", embeddings, allow_dangerous_deserialization=True)
        price_index = FAISS.load_local("faiss_price_index", embeddings, allow_dangerous_deserialization=True)

        # Get top-k results from each
        news_docs = news_index.similarity_search(question, k=k)
        fin_docs = fin_index.similarity_search(question, k=k)
        econ_docs = econ_index.similarity_search(question, k=k)
        price_docs = price_index.similarity_search(question, k=k)

        # Combine documents
        all_docs = news_docs + fin_docs + econ_docs + price_docs
        
        # Wrap in a static retriever
        retriever = StaticMultiRetriever(documents=all_docs)

        # Create chain
        qa_chain = create_stuff_documents_chain(llm, prompt)
        chain = create_retrieval_chain(retriever, qa_chain)

        # Run
        result = chain.invoke({"input": question})
        return result.get("answer", "⚠️ No response.")

    except Exception as e:
        return f"❌ Error during combined RAG query: {e}"

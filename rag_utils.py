import os
import pandas as pd
from database import postgres_engine
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# Set environment
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Embedding + LLM setup
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Text splitting config
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

# ✅ Financial analysis prompt template
financial_prompt_template = (
    "You are a highly knowledgeable and confident financial analyst AI. Your role is to provide thorough and insightful answers "
    "based on the context provided, which may include financial reports, stock trends, macroeconomic indicators, and news articles.\n\n"

    "NEVER say that the data is insufficient or missing information or that you cannot answer. If some information is missing or vague, "
    "make intelligent inferences, explain broader implications, or explore related financial and economic trends. "
    "You must ALWAYS provide a meaningful response, even if speculative. Avoid phrases like 'insufficient data', 'not enough info', or 'unable to answer'.\n\n"

    "Respond in 4–6 bullet points that reflect meaningful analysis. Keep the tone confident, objective, and analytical.\n\n"

    "Context:\n{context}\n\n"
    "Question: {input}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", financial_prompt_template),
    ("human", "{input}")
])

# ⬇️ Load news articles and chunk them
def load_and_chunk_news():
    query = "SELECT title, description, content, topic FROM news_articles"
    df = pd.read_sql(query, postgres_engine)

    df["text"] = (
        df["title"].fillna('') + "\n\n" +
        df["description"].fillna('') + "\n\n" +
        df["content"].fillna('')
    ).str.strip()

    texts, sources = [], []
    for _, row in df.iterrows():
        chunks = text_splitter.split_text(row["text"])
        texts.extend(chunks)
        sources.extend([row["topic"]] * len(chunks))

    return texts, sources

# ⬇️ Build and save FAISS index
def build_faiss_index_gemini():
    texts, sources = load_and_chunk_news()
    vector_store = FAISS.from_texts(texts, embeddings, metadatas=[{"source": src} for src in sources])
    vector_store.save_local("faiss_gemini_index")
    print("✅ FAISS index with Gemini saved.")

# ⬇️ Load FAISS index and set up retrieval chain
def load_rag_chain():
    vector_store = FAISS.load_local("faiss_gemini_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    qa_chain = create_stuff_documents_chain(llm, prompt)
    chain = create_retrieval_chain(retriever, qa_chain)
    return chain

# ⬇️ Run query and return structured response
def run_gemini_rag_query(question: str):
    try:
        chain = load_rag_chain()
        response = chain.invoke({"input": question})
        return response.get("answer", "⚠️ No response from model.")
    except Exception as e:
        return f"❌ Error during RAG query: {e}"
    
    
def generate_executive_summary_with_llm(llm, context_text: str, symbol: str, start_date: str, end_date: str) -> str:
    prompt = (
        f"Write an executive summary (3–5 bullet points) for the company {symbol}, "
        f"covering the period from {start_date} to {end_date}, based on the context below:\n\n"
        f"If any details are missing, make reasonable inferences or focus on broader trends. "
        f"**Do not mention insufficient data**. Always generate a confident summary.\n\n{context_text}"
    )
    return llm.invoke(prompt).content.strip()


def generate_risk_analysis_with_llm(llm, context_text: str, symbol: str) -> str:
    prompt = (
        f"List financial and macroeconomic risks affecting {symbol} in bullet points, "
        f"based on the following context:\n\n"
        f"If any details are missing, make reasonable inferences or focus on broader trends. "
        f"**Do not mention insufficient data**. Always generate a confident summary.\n\n{context_text}"
    )
    return llm.invoke(prompt).content.strip()


def generate_methodology_with_llm(llm) -> str:
    prompt = (
        "Summarize the data sources and methods used in this financial analysis. "
        "Include stock APIs like Alpha Vantage, financial news, polynomial regression for predictions, "
        "and semantic vector search with FAISS + RAG architecture."
    )
    return llm.invoke(prompt).content.strip()
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 20:02:10 2025

@author: PCA
"""

import logging
from query_parameter_extractor import extract_parameters_with_gemini
from regression_utils import run_polynomial_regression
from report_utils import generate_pdf_report
from rag_utils import (
    run_combined_rag_query,
    generate_executive_summary_with_llm,
    generate_risk_analysis_with_llm,
    generate_methodology_with_llm
)
from langchain_google_genai import ChatGoogleGenerativeAI


def process_query_to_pdf(question: str):
    logging.info(f"📥 Processing query: {question}")
    rag_summary = run_combined_rag_query(question)
    params = extract_parameters_with_gemini(question)

    symbol = params.get("symbol")
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    executive_summary = generate_executive_summary_with_llm(llm, rag_summary, symbol, start_date, end_date)
    risk_analysis = generate_risk_analysis_with_llm(llm, rag_summary, symbol)
    methodology = generate_methodology_with_llm(llm)

    if symbol:
        df, r2, plot_path, pred_date, pred_price = run_polynomial_regression(symbol)
        if df is not None:
            return generate_pdf_report(
                symbol=symbol,
                start_date=start_date or df["date"].min().strftime("%Y-%m-%d"),
                end_date=end_date or df["date"].max().strftime("%Y-%m-%d"),
                r2_score=r2,
                plot_path=plot_path,
                predicted_date=pred_date,
                predicted_value=pred_price,
                rag_insight=rag_summary,
                executive_summary=executive_summary,
                risk_analysis=risk_analysis,
                methodology=methodology
            )
    else:
        logging.warning("⚠️ No symbol detected in query.")
        logging.info("🧠 RAG-only insight:\n" + rag_summary)
        return None

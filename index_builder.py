# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 19:59:52 2025

@author: PCA
"""

import os
from rag_utils import build_faiss_index_gemini
from financial_indexing_utils import build_financial_faiss_index
from economic_indexing_utils import build_economic_faiss_index
from price_indexing_utils import build_price_faiss_index
from rag_utils import load_and_chunk_news

def initialize_all_indexes():
    load_and_chunk_news()
    if not os.path.exists("faiss_gemini_index/index.faiss"):
        build_faiss_index_gemini()
    if not os.path.exists("faiss_financial_index/index.faiss"):
        build_financial_faiss_index()
    if not os.path.exists("faiss_econ_index/index.faiss"):
        build_economic_faiss_index()
    if not os.path.exists("faiss_price_index/index.faiss"):
        build_price_faiss_index()
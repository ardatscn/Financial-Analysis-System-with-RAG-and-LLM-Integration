# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 22:17:23 2025

@author: PCA
"""

from sqlalchemy import create_engine
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_DB_URL = os.getenv("POSTGRES_DB_URL")
MONGODB_URL = os.getenv("MONGODB_URL")

# PostgreSQL engine (for stock data)
postgres_engine = create_engine(POSTGRES_DB_URL)

# MongoDB client (for news articles)
mongo_client = AsyncIOMotorClient(MONGODB_URL)
mongo_db = mongo_client.financial_db
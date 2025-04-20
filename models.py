# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 22:18:44 2025

@author: PCA
"""

from pydantic import BaseModel, validator
from typing import Optional

class StockPrice(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str

    @validator('symbol')
    def validate_symbol(cls, v):
        assert v.isupper(), "Symbol must be uppercase"
        return v

class NewsArticle(BaseModel):
    title: str
    published_at: str
    source: Optional[str]
    url: str
    topic: str
    description: Optional[str] = ""
    content: Optional[str] = ""

    @validator('url')
    def validate_url(cls, v):
        assert v.startswith("http"), "Invalid URL"
        return v

class FinancialReport(BaseModel):
    symbol: str
    fiscal_date: str
    total_revenue: Optional[float]
    net_income: Optional[float]
    gross_profit: Optional[float]
    operating_income: Optional[float]
    
    
class EconomicIndicator(BaseModel):
    indicator: str
    date: str
    value: Optional[float]
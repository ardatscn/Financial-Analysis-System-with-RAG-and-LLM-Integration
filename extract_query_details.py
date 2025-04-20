# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 09:35:40 2025

@author: PCA
"""

import re
from dateutil import parser as date_parser
from datetime import datetime
from typing import Optional, Tuple

# Define known stock symbols
KNOWN_SYMBOLS = {"AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NFLX", "META", "NVDA", "IBM"}

def extract_query_details(query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extracts symbol, start_date, and end_date from query text."""
    
    symbol = None
    for s in KNOWN_SYMBOLS:
        if s in query.upper():
            symbol = s
            break

    # Look for date patterns
    date_matches = re.findall(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
                              r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
                              r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{4})\b[ \d,]*", query, flags=re.IGNORECASE)

    parsed_dates = []
    for text in date_matches:
        try:
            dt = date_parser.parse(text, fuzzy=True, default=datetime(2023, 1, 1))
            parsed_dates.append(dt.date())
        except Exception:
            pass

    if len(parsed_dates) >= 2:
        start_date, end_date = sorted(parsed_dates[:2])
        return symbol, str(start_date), str(end_date)
    
    return symbol, None, None

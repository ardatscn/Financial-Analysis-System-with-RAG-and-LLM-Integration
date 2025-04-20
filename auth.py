# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 19:58:53 2025

@author: PCA
"""

import os
import time
import logging

VALID_KEYS = ["key123"]
RATE_LIMIT_SECONDS = 30
LAST_RUN_FILE = "last_run.txt"

def validate_api_key():
    key = os.getenv("API_KEY")
    if not key or key not in VALID_KEYS:
        logging.error("❌ Invalid or missing API key.")
        raise PermissionError("Invalid API key.")
    logging.info("✅ API key validated.")

def enforce_rate_limit():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            last_run = float(f.read().strip())
        elapsed = time.time() - last_run
        if elapsed < RATE_LIMIT_SECONDS:
            raise RuntimeError(f"⏳ Rate limit: Please wait {int(RATE_LIMIT_SECONDS - elapsed)}s.")
    with open(LAST_RUN_FILE, "w") as f:
        f.write(str(time.time()))
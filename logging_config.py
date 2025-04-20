# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 19:59:21 2025

@author: PCA
"""

import logging
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
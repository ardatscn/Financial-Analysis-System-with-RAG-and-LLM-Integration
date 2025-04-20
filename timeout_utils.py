# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 19:59:07 2025

@author: PCA
"""

import signal

class TimeoutException(Exception):
    pass

def timeout(seconds=60):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutException(f"⏰ Operation timed out after {seconds} seconds.")
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
        return wrapper
    return decorator
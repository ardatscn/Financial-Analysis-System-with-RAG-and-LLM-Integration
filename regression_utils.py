import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from database import postgres_engine

def run_polynomial_regression(symbol, start_date=None, end_date=None, degree=8, output_dir="plots"):
    """
    Perform polynomial regression on stock data for a given symbol.
    If start_date and end_date are None, use all available data.
    """
    os.makedirs(output_dir, exist_ok=True)

    query = f"SELECT date, close FROM stock_prices WHERE symbol = '{symbol}' ORDER BY date ASC"
    df = pd.read_sql(query, postgres_engine)
    df["date"] = pd.to_datetime(df["date"])

    if df.empty:
        print(f"❌ No data found for {symbol}")
        return None, None, None

    if start_date and end_date:
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        if df.empty:
            print(f"⚠️ No data for {symbol} between {start_date} and {end_date}")
            return None, None, None

    df = df.dropna()
    
    df["days"] = (df["date"] - df["date"].min()).dt.days
    X = df[["days"]]
    y = df["close"]

    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X)

    model = LinearRegression()
    model.fit(X_poly, y)

    y_pred = model.predict(X_poly)
    r2 = r2_score(y, y_pred)

    # ✅ Predict next day
    next_day = df["days"].max() + 1
    X_next = poly.transform([[next_day]])
    y_next = model.predict(X_next)[0]
    next_date = df["date"].max() + pd.Timedelta(days=1)

    # ✅ Plot
    plot_path = os.path.join(output_dir, f"{symbol}_regression.png")
    plt.figure(figsize=(10, 4))
    plt.plot(df["date"], y, label="Actual", linewidth=2)
    plt.plot(df["date"], y_pred, label="Polynomial Fit", linestyle="--")

    # ✅ Mark predicted point
    plt.axvline(next_date, color="gray", linestyle=":")
    plt.scatter(next_date, y_next, color="red", zorder=5, label=f"Predicted: {y_next:.2f}")
    plt.text(next_date, y_next, f"{y_next:.2f}", ha="left", va="bottom", fontsize=9)

    plt.title(f"{symbol} Price Trend (Degree {degree})")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    return df, r2, plot_path, next_date, y_next

def compute_technical_indicators(symbol: str, start_date: str, end_date: str):
    """
    Retrieves stock data from PostgreSQL and computes key technical indicators.
    Returns a dictionary of calculated metrics.
    """
    query = f"""
        SELECT date, close
        FROM stock_prices
        WHERE symbol = '{symbol}'
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date ASC
    """
    df = pd.read_sql(query, postgres_engine)

    if df.empty or "close" not in df.columns:
        print(f"[{symbol}] ⚠️ No data found for computing technical indicators.")
        return {}

    df["date"] = pd.to_datetime(df["date"])
    df["daily_return"] = df["close"].pct_change()

    indicators = {
        "volatility": df["daily_return"].std(),
        "average_return": df["daily_return"].mean(),
        "ma20": df["close"].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None,
        "ma50": df["close"].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else None,
        "max_drawdown": ((df["close"] - df["close"].cummax()) / df["close"].cummax()).min()
    }

    return indicators



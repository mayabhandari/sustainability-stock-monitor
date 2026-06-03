#!/usr/bin/env python3
"""
Sustainability Stock Monitor
Tracks top 30 sustainability/ESG stocks daily, fetches news,
and generates AI-powered investment analysis via Groq (free).
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta

import requests
import yfinance as yf

# ── Configuration ────────────────────────────────────────────────────────────

SUSTAINABILITY_STOCKS = {
    "ENPH": "Enphase Energy",
    "SEDG": "SolarEdge Technologies",
    "FSLR": "First Solar",
    "NEE":  "NextEra Energy",
    "PLUG": "Plug Power",
    "BE":   "Bloom Energy",
    "RUN":  "Sunrun",
    "TSLA": "Tesla",
    "RIVN": "Rivian Automotive",
    "NIO":  "NIO Inc",
    "XYL":  "Xylem (Water Tech)",
    "AWK":  "American Water Works",
    "WM":   "Waste Management",
    "RSG":  "Republic Services",
    "TRMB": "Trimble (Precision Ag)",
    "DANOY":"Danone (Sustainable Food)",
    "VWDRY":"Vestas Wind Systems",
    "ORSTED.CO":"Orsted (Offshore Wind)",
    "IBDRY":"Iberdrola (Renewables)",
    "CWEN": "Clearway Energy",
    "AES":  "AES Corporation",
    "BEP":  "Brookfield Renewable",
    "HASI": "HA Sustainable Infra",
    "BEPC": "Brookfield Renewable Corp",
    "DQ":   "Daqo New Energy",
    "CSIQ": "Canadian Solar",
    "JKS":  "JinkoSolar",
    "GPRE": "Green Plains (Biofuels)",
    "STEM": "Stem Inc (Energy Storage)",
    "CHPT": "ChargePoint Holdings",
}

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ── Groq API Helper ──────────────────────────────────────────────────────────

def call_groq(api_key, prompt, max_tokens=4096):
    """Call Groq API (OpenAI-compatible). Free, fast, reliable."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    for attempt in range(3):
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)

            if resp.status_code == 429:
                wait = (attempt + 1) * 20
                print(f"   ... Rate limited, waiting {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"   ! Groq API error: {e}")
            if attempt < 2:
                time.sleep(10)

    return ""


# ── Data Fetching ────────────────────────────────────────────────────────────

def fetch_stock_data(tickers, period="5d"):
    """Fetch recent price data for a list of tickers using yfinance."""
    results = {}
    print(f"  Fetching stock data for {len(tickers)} tickers...")

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)

            if hist.empty:
                results[ticker] = {"error": "No data available"}
                continue

            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) >= 2 else hist.iloc[0]

            daily_change = latest["Close"] - prev["Close"]
            daily_change_pct = (daily_change / prev["Close"]) * 100

            week_change_pct = (
                (latest["Close"] - hist.iloc[0]["Close"]) / hist.iloc[0]["Close"]
            ) * 100

            results[ticker] = {
                "name": SUSTAINABILITY_STOCKS.get(ticker, ticker),
                "price": round(latest["Close"], 2),
                "daily_change": round(daily_change, 2),
                "daily_change_pct": round(daily_change_pct, 2),
                "week_change_pct": round(week_change_pct, 2),
                "volume": int(latest["Volume"]),
                "high": round(latest["High"], 2),
                "low": round(latest["Low"], 2),
                "open": round(latest["Open"], 2),
            }
        except Exception as e:
            results[ticker] = {"error": str(e)}

    return results


# ── Analysis ─────────────────────────────────────────────────────────────────

def generate_report(api_key, stock_data):
    """Send stock data to Groq for investment analysis."""
    print("  Generating AI analysis...")

    valid = {k: v for k, v in stock_data.items() if "error" not in v}
    sorted_stocks = sorted(
        valid.items(), key=lambda x: x[1]["daily_change_pct"], reverse=True
    )

    stock_summary = "STOCK PERFORMANCE DATA\n" + "=" * 50 + "\n\n"
    stock_summary += f"{'Ticker':<8} {'Name':<30} {'Price':>8} {'Day %':>8} {'Week %':>8} {'Volume':>12}\n"
    stock_summary += "-" * 80 + "\n"

    for ticker, data in sorted_stocks:
        stock_summary += (
            f"{ticker:<8} {data['name']:<30} "
            f"${data['price']:>7.2f} "
            f"{data['daily_change_pct']:>+7.2f}% "
            f"{data['week_change_pct']:>+7.2f}% "
            f"{data['volume']:>12,}\n"
        )

    prompt = f"""You are a senior ESG/sustainability investment analyst.
Analyze the following stock performance data for a portfolio
of 30 sustainability-focused stocks. Today's date is {datetime.now().strftime("%B %d, %Y")}.

{stock_summary}

Please provide a comprehensive daily briefing with these sections:

1. **MARKET OVERVIEW** - How did the sustainability sector perform today overall?
   Summarize the broad trend in 2-3 sentences.

2. **TOP PERFORMERS** - Highlight the top 5 gainers with brief analysis of why
   they may have moved. Include price, daily %, and weekly %.

3. **BOTTOM PERFORMERS** - Highlight the bottom 5 with analysis of potential
   catalysts for the decline.

4. **SECTOR TRENDS** - What broader trends do you see across renewable energy,
   EVs, water tech, and waste management?

5. **INVESTMENT CONSIDERATIONS** - Based on the data:
   - Which stocks show strong momentum worth watching?
   - Which beaten-down stocks might present value opportunities?
   - Any sector-wide trends to be aware of?
   - Key risks to monitor this week.

6. **WATCHLIST** - Pick 3-5 stocks to watch closely tomorrow with brief
   reasoning.

IMPORTANT: Include a disclaimer that this is AI-generated analysis for
informational purposes only, not professional financial advice. Always
recommend consulting a qualified financial advisor before making investment
decisions.

Format the report in clean Markdown."""

    result = call_groq(api_key, prompt)
    if not result:
        return "Error: Could not generate analysis. Check your GROQ_API_KEY."
    return result


# ── Output ───────────────────────────────────────────────────────────────────

def save_report(report, stock_data):
    """Save the report to a dated markdown file."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"reports/sustainability_report_{date_str}.md"

    os.makedirs("reports", exist_ok=True)

    header = f"""# Sustainability Stock Monitor
## Daily Report - {datetime.now().strftime("%B %d, %Y")}
*Generated at {datetime.now().strftime("%I:%M %p")}*

---

"""
    with open(filename, "w") as f:
        f.write(header + report)

    print(f"\n  Report saved to {filename}")
    return filename


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: Set your GROQ_API_KEY environment variable.")
        print("  export GROQ_API_KEY='gsk_...'")
        sys.exit(1)

    tickers = list(SUSTAINABILITY_STOCKS.keys())

    print("Sustainability Stock Monitor")
    print(f"Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
    print(f"Tracking {len(tickers)} stocks\n")

    # 1. Fetch stock data
    stock_data = fetch_stock_data(tickers)

    valid_count = sum(1 for v in stock_data.values() if "error" not in v)
    error_count = len(stock_data) - valid_count
    print(f"  {valid_count} stocks loaded, {error_count} errors\n")

    # 2. Generate analysis
    report = generate_report(api_key, stock_data)
    print(f"  Analysis complete\n")

    # 3. Save report
    filepath = save_report(report, stock_data)

    # 4. Print to console
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    return filepath


if __name__ == "__main__":
    main()

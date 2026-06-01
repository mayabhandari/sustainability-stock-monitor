#!/usr/bin/env python3
"""
Sustainability Stock Monitor
Tracks top 30 sustainability/ESG stocks daily, fetches news,
and generates AI-powered investment analysis via Google Gemini (free).
"""

import json
import os
import sys
from datetime import datetime, timedelta

import requests
import yfinance as yf

# ── Configuration ────────────────────────────────────────────────────────────

# Top 30 sustainability / ESG-focused stocks
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

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"


# ── Gemini API Helper ────────────────────────────────────────────────────────

def call_gemini(api_key: str, prompt: str, use_search: bool = False) -> str:
    """Call Google Gemini API. Optionally enable Google Search grounding."""
    url = f"{GEMINI_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 4096},
    }

    # Enable Google Search grounding for news fetching
    if use_search:
        payload["tools"] = [{"google_search": {}}]

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # Extract text from Gemini response
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            return text

        return "No response generated."

    except Exception as e:
        print(f"   ⚠ Gemini API error: {e}")
        return ""


# ── Data Fetching ────────────────────────────────────────────────────────────

def fetch_stock_data(tickers: list[str], period: str = "5d") -> dict:
    """Fetch recent price data for a list of tickers using yfinance."""
    results = {}
    print(f"📊 Fetching stock data for {len(tickers)} tickers...")

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


def fetch_news(api_key: str, tickers: list[str]) -> str:
    """Use Gemini with Google Search grounding to fetch latest news."""
    print("📰 Fetching news via Gemini + Google Search...")

    top_names = [SUSTAINABILITY_STOCKS[t] for t in tickers[:10]]
    query = (
        f"Find the most important news from the last 48 hours about these "
        f"sustainability and clean energy stocks: {', '.join(top_names)}. "
        f"Also include any major ESG investing news, renewable energy policy "
        f"changes, or clean tech sector developments. "
        f"Summarize each piece of news in 1-2 sentences."
    )

    result = call_gemini(api_key, query, use_search=True)
    return result if result.strip() else "News unavailable — analysis will be based on price data only."


# ── Analysis ─────────────────────────────────────────────────────────────────

def generate_analysis(api_key: str, stock_data: dict, news: str) -> str:
    """Send stock data + news to Gemini for investment analysis."""
    print("🤖 Generating AI analysis...")

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
Analyze the following stock performance data and recent news for a portfolio 
of 30 sustainability-focused stocks.

{stock_summary}

RECENT NEWS
{"=" * 50}
{news}

Please provide a comprehensive daily briefing with these sections:

1. **MARKET OVERVIEW** — How did the sustainability sector perform today overall?
   Summarize the broad trend in 2-3 sentences.

2. **TOP PERFORMERS** — Highlight the top 5 gainers with brief analysis of why 
   they may have moved. Include price, daily %, and weekly %.

3. **BOTTOM PERFORMERS** — Highlight the bottom 5 with analysis of potential 
   catalysts for the decline.

4. **NEWS IMPACT** — Connect any relevant news to stock movements. Which 
   headlines are driving the market?

5. **INVESTMENT CONSIDERATIONS** — Based on the data and news:
   - Which stocks show strong momentum worth watching?
   - Which beaten-down stocks might present value opportunities?
   - Any sector-wide trends to be aware of?
   - Key risks to monitor this week.

6. **WATCHLIST** — Pick 3-5 stocks to watch closely tomorrow with brief 
   reasoning.

IMPORTANT: Include a disclaimer that this is AI-generated analysis for 
informational purposes only, not professional financial advice. Always 
recommend consulting a qualified financial advisor before making investment 
decisions.

Format the report in clean Markdown."""

    result = call_gemini(api_key, prompt)
    if not result:
        return "Error: Could not generate analysis. Check your Gemini API key."
    return result


# ── Output ───────────────────────────────────────────────────────────────────

def save_report(report: str, stock_data: dict):
    """Save the report to a dated markdown file."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"reports/sustainability_report_{date_str}.md"

    os.makedirs("reports", exist_ok=True)

    header = f"""# 🌿 Sustainability Stock Monitor
## Daily Report — {datetime.now().strftime("%B %d, %Y")}
*Generated at {datetime.now().strftime("%I:%M %p")}*

---

"""
    with open(filename, "w") as f:
        f.write(header + report)

    print(f"\n✅ Report saved to {filename}")
    return filename


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: Set your GEMINI_API_KEY environment variable.")
        print("   export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)

    tickers = list(SUSTAINABILITY_STOCKS.keys())

    print("🌿 Sustainability Stock Monitor")
    print(f"📅 {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
    print(f"📈 Tracking {len(tickers)} stocks\n")

    # 1. Fetch stock data
    stock_data = fetch_stock_data(tickers)

    valid_count = sum(1 for v in stock_data.values() if "error" not in v)
    error_count = len(stock_data) - valid_count
    print(f"   ✓ {valid_count} stocks loaded, {error_count} errors\n")

    # 2. Fetch news
    news = fetch_news(api_key, tickers)
    print(f"   ✓ News fetched\n")

    # 3. Generate analysis
    report = generate_analysis(api_key, stock_data, news)
    print(f"   ✓ Analysis complete\n")

    # 4. Save report
    filepath = save_report(report, stock_data)

    # 5. Print to console
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    return filepath


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Sustainability Stock Monitor
Tracks top 30 sustainability/ESG stocks daily, fetches news,
and generates AI-powered investment analysis via Claude.
"""
 
import json
import os
import sys
from datetime import datetime, timedelta
 
import anthropic
import yfinance as yf
 
# ── Configuration ────────────────────────────────────────────────────────────
 
# Top 30 sustainability / ESG-focused stocks
# Mix of renewable energy, EVs, ESG leaders, water, and clean tech
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
 
MODEL = "claude-sonnet-4-6"
 
 
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
 
            # Week performance (first vs last in period)
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
 
 
def fetch_news_via_claude(client: anthropic.Anthropic, tickers: list[str]) -> str:
    """Use Claude with web search to fetch latest sustainability stock news."""
    print("📰 Fetching news via Claude web search...")
 
    # Build a focused news query
    top_names = [SUSTAINABILITY_STOCKS[t] for t in tickers[:10]]
    query = (
        f"Find the most important news from the last 24-48 hours about these "
        f"sustainability and clean energy stocks: {', '.join(top_names)}. "
        f"Also include any major ESG investing news, renewable energy policy "
        f"changes, or clean tech sector developments. "
        f"Summarize each piece of news in 1-2 sentences."
    )
 
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": query}],
    )
 
    # Extract text from response
    news_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            news_text += block.text + "\n"
 
    return news_text if news_text.strip() else "No recent news found."
 
 
# ── Analysis ─────────────────────────────────────────────────────────────────
 
def generate_analysis(
    client: anthropic.Anthropic,
    stock_data: dict,
    news: str,
) -> str:
    """Send stock data + news to Claude for investment analysis."""
    print("🤖 Generating AI analysis...")
 
    # Sort stocks by daily performance
    valid = {k: v for k, v in stock_data.items() if "error" not in v}
    sorted_stocks = sorted(
        valid.items(), key=lambda x: x[1]["daily_change_pct"], reverse=True
    )
 
    # Build a structured data summary for Claude
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
 
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
 
    return response.content[0].text
 
 
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
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Set your ANTHROPIC_API_KEY environment variable.")
        print("   export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)
 
    client = anthropic.Anthropic(api_key=api_key)
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
    news = fetch_news_via_claude(client, tickers)
    print(f"   ✓ News fetched\n")
 
    # 3. Generate analysis
    report = generate_analysis(client, stock_data, news)
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

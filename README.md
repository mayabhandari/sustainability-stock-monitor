# 🌿 Sustainability Stock Monitor

AI-powered daily briefing on 30 top sustainability & ESG stocks. Uses **yfinance** for market data, **Claude** for news retrieval (via web search) and investment analysis.

## What it does

1. **Fetches live stock data** — price, daily/weekly change, volume for 30 sustainability stocks
2. **Gathers news** — uses Claude's web search to find the latest ESG/clean energy headlines
3. **Generates analysis** — Claude acts as an ESG analyst, producing a structured daily report with top/bottom performers, news impact, investment considerations, and a watchlist
4. **Saves a report** — dated Markdown file in `reports/`
5. **Optional email delivery** — send the report to your inbox each morning

## Stocks tracked

Renewable energy (ENPH, SEDG, FSLR, NEE, RUN), hydrogen/fuel cells (PLUG, BE), EVs (TSLA, RIVN, NIO), water tech (XYL, AWK), waste management (WM, RSG), wind (VWDRY, ORSTED), solar manufacturing (DQ, CSIQ, JKS), energy storage (STEM, CHPT), clean infrastructure (CWEN, AES, BEP, HASI, BEPC), and more.

## Quick start

```bash
# 1. Clone or download this folder

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 4. Run
python monitor.py
```

The report prints to the console and saves to `reports/sustainability_report_YYYY-MM-DD.md`.

## Automate it (run daily)

### Option A: cron (Mac/Linux)

```bash
# Open crontab
crontab -e

# Run every weekday at 5:00 PM ET (after market close)
0 17 * * 1-5 cd /path/to/sustainability-stock-monitor && ANTHROPIC_API_KEY="sk-ant-..." /usr/bin/python3 monitor.py
```

### Option B: GitHub Actions

Create `.github/workflows/daily-report.yml`:

```yaml
name: Daily Sustainability Report
on:
  schedule:
    - cron: '0 21 * * 1-5'  # 9 PM UTC = 5 PM ET
  workflow_dispatch:  # manual trigger

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python monitor.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - uses: actions/upload-artifact@v4
        with:
          name: report-${{ github.run_id }}
          path: reports/
```

### Option C: Cloud function

Deploy to AWS Lambda, Google Cloud Functions, or similar. Trigger with CloudWatch Events / Cloud Scheduler on a daily cron.

## Email delivery (optional)

```bash
# Set email credentials (Gmail example — use an App Password)
export SENDER_EMAIL="you@gmail.com"
export SENDER_PASSWORD="your-app-password"
export RECIPIENT_EMAIL="you@gmail.com"

# Run after generating a report
python email_report.py reports/sustainability_report_2026-06-01.md
```

## Customizing the stock list

Edit the `SUSTAINABILITY_STOCKS` dictionary in `monitor.py`. Use any valid Yahoo Finance ticker.

## API costs

- **yfinance**: Free (unofficial Yahoo Finance API)
- **Claude API**: Each run uses roughly 5,000–8,000 tokens. At Sonnet pricing, this is a few cents per run. The web search call for news adds a small additional cost. See [Anthropic pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) for current rates.

## Disclaimer

This tool generates AI-powered analysis for **informational purposes only**. It is not professional financial advice. Always consult a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

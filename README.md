# create-graph-action-video

Tool for generating TikTok videos (1080×1920 vertical format) showing the evolution of a long-term stock investment. Everything is driven by a `scenario.json` file.

---

## Concept

The graph displays up to three curves over the same period:

| # | Curve | Always shown | Description |
|---|-------|:------------:|-------------|
| 1 | **Amount invested** | Yes | Cumulative amount actually contributed (regular or one-time investment) |
| 2 | **Value without dividends** | Yes | Portfolio value based solely on price appreciation (Adjusted Close, excluding dividends) |
| 3 | **Value with reinvested dividends** | Only if the stock pays dividends | Portfolio value assuming each dividend received is immediately reinvested into additional shares |

Curve 3 only appears if the stock has actually paid dividends during the period. The gap between curves 2 and 3 visually shows the concrete long-term impact of reinvested dividends.

### Axes

| Axis | Content | Style |
|------|---------|-------|
| Vertical (left) | Price / Value in currency | **Bold, black** |
| Horizontal | Years | **Bold, black** |

The video background is **white**.

---

### Curve legend

| Curve | Suggested color |
|-------|----------------|
| Amount invested | Grey `#888888` |
| Value without dividends | Blue `#2979FF` |
| Value with reinvested dividends | Green `#00C853` |

---

## Video layout

```
┌─────────────────────────────────┐
│                                 │
│   If you had invested $10       │
│   per week in McDonald's        │
│   instead of eating McDonald's  │  ← Hook text (top)
│   every week...                 │
│                                 │
│                                 │
│                                 │
│         [empty space]           │
│                                 │
│                                 │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │        GRAPH              │  │  ← Graph (center-bottom)
│  │     (three curves)        │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

- **Top of screen**: hook text, defined in `scenario.json`, centered, bold
- **Center-bottom**: animated graph with the curves
- **Background**: white `#FFFFFF` across the entire video

---

## scenario.json

Single configuration file that drives the entire video.

```json
{
  "text": {
    "headline": "If you had invested $10 per week in McDonald's\ninstead of buying McDonald's every week",
    "font_size": 52,
    "color": "#111111"
  },
  "data": {
    "ticker": "MCD",
    "start_date": "2015-01-01",
    "end_date": "2025-01-01",
    "weekly_investment": 10,
    "currency": "USD",
    "reinvest_dividends": true
  },
  "video": {
    "output": "video_MCD.mp4",
    "duration_seconds": 10,
    "fps": 30
  }
}
```

### Field details

#### `text`
| Field | Description |
|-------|-------------|
| `headline` | Text displayed at the top of the screen. Use `\n` for line breaks. |
| `font_size` | Font size (default: 52) |
| `color` | Text color in hex (default: `#111111`) |

#### `data`
| Field | Description |
|-------|-------------|
| `ticker` | Stock symbol (e.g. `MCD`, `AAPL`, `MC.PA`) |
| `start_date` | Investment start date (`YYYY-MM-DD`) |
| `end_date` | End date (`YYYY-MM-DD`), default: today |
| `weekly_investment` | Weekly contribution in currency (or `monthly_investment` for monthly) |
| `currency` | Display currency |
| `reinvest_dividends` | `true`: shows the 3rd curve with reinvested dividends. `false`: only the first two curves. Default: `true` |

#### `video`
| Field | Description |
|-------|-------------|
| `output` | Output MP4 filename |
| `duration_seconds` | Total video duration |
| `fps` | Frames per second (default: 30) |

---

## Tech stack

### Rendering pipeline — same approach as `create-sms-story-video`

```
yfinance → scenario.json → index.html (D3.js) → Playwright → FFmpeg → MP4
```

1. `render.py` fetches historical data via **yfinance**
2. Injects the computed data into `scenario.json`
3. Serves `index.html` via a local HTTP server
4. **Playwright** records the browser animation in real time
5. **FFmpeg** encodes the WebM capture → MP4 H.264

---

### Why JS/HTML instead of Matplotlib?

| Criterion | JS/HTML + Playwright | Matplotlib + Pillow |
|-----------|:--------------------:|:-------------------:|
| Render quality | Antialiased SVG, crisp at 1080×1920 | Bitmap rendering, less sharp |
| Curve animation | `requestAnimationFrame` — natively smooth | Manual frame-by-frame |
| Typography | CSS + web fonts, automatic wrapping | Limited API, manual handling |
| Curves | Smooth Bézier | Straight segments between points |
| Project consistency | Same pipeline as `create-sms-story-video` | Separate stack |

---

### Tech breakdown

| Component | Role |
|-----------|------|
| **Python** | Orchestration, data fetching, injection into `scenario.json` |
| **yfinance** | Adjusted close history + dividends — free, no API key required |
| **pandas** | Time series manipulation on data returned by yfinance |
| **D3.js** | SVG graph rendering, left-to-right curve drawing animation, custom axes |
| **Playwright** | Real-time HTML animation capture (headless Chromium) |
| **FFmpeg** | WebM → final MP4 H.264 encoding |

### Why D3.js and not Chart.js?

D3.js provides full control over the progressive drawing animation (the curve is drawn point by point from left to right using `stroke-dashoffset`), bold/black custom axes, and pixel-perfect element positioning. Chart.js animates everything at once and offers less freedom over sequential curve drawing.

---

One-shot tool: each run calls the API, fetches the full history, and generates the video. No cache, no database.

---

## Data sources

### yfinance (primary source)
- Unofficial Python wrapper for Yahoo Finance
- Free, no API key required
- Provides `Adjusted Close` natively via `Ticker.history()`
- Provides dividend history via `Ticker.dividends`
- Limitation: can be unstable over very long periods or for some non-US markets

### Financial Modeling Prep — FMP (secondary source)
- Official REST API, key required (free plan available with limits)
- Reliable historical data with adjusted prices
- Dedicated endpoint for dividend history (`/historical/stock_dividend/{ticker}`)
- Used as fallback if yfinance fails or returns incomplete data

### Dividend reinvestment calculation

At each dividend payment date:
1. Retrieve the gross dividend amount per share
2. Compute total dividend received = `shares_held × dividend_per_share`
3. Buy new shares at the day's price = `total_dividend / adjusted_close_of_day`
4. Add the new shares to the portfolio for subsequent calculations

This calculation produces the **"Value with reinvested dividends"** curve.

---

## Critical points

### Adjusted Close price

Always use the **split- and dividend-adjusted close price**, never the raw price.

> Example: if a stock does a 1:10 split, its raw price drops 90% overnight. Without adjustment, the "current value" curve would artificially collapse — the graph would be misleading.

Both sources (yfinance and FMP) provide this field; make sure to use it explicitly.

---

## Output format

- **Resolution**: 1080 × 1920 px (TikTok portrait)
- **FPS**: 30 (configurable)
- **Format**: MP4 (H.264)
- **Background**: white `#FFFFFF`
- **Animation**: curves are drawn from left to right as the video progresses

---

## Project structure (target)

```
create-graph-action-video/
├── README.md
├── render.py          # Entry point — reads scenario.json and orchestrates everything
├── fetcher.py         # Historical data fetching (yfinance / FMP)
├── graph.py           # Frame-by-frame graph rendering (D3.js via index.html)
├── encoder.py         # PNG frames → MP4 assembly via FFmpeg
└── scenario.json      # Full configuration for the video to generate
```

## Usage

```bash
python3 render.py --scenario scenario.json
```

# PortfolioLens — Milestone 5

PortfolioLens turns Indian equity holdings into understandable performance, allocation, concentration, and risk insights.

Milestone 5 adds a readable portfolio report and PDF export to the existing AI-assisted extraction and local analytics engine. The default report is generated from verified metrics without an API call. An optional AI interpretation is available only after separate consent and is cached in the browser to avoid paying for the same report twice.

## What works

- Upload JPG, JPEG, PNG, or PDF portfolio files
- Upload up to 6 screenshots, including overlapping screenshots
- Detect Zerodha, Upstox, or another broker layout
- Extract only visibly shown holdings and remove duplicate symbols
- Prefill symbol, company, quantity, average price, LTP/current price, sector, and market cap
- Highlight lower-confidence readings and missing fields
- Require the user to verify every holding before analysis
- Keep manual holding entry as an alternative
- Recalculate the complete dashboard through the Flask API
- Portfolio health score and effective-holdings measure
- Gross gains, gross losses, profit factor, winners, and losers
- Best and weakest holding identification
- Single-stock, top-three, and sector concentration analysis
- Return contribution in portfolio percentage points
- Sector-level invested value, current value, P&L, and return
- Four preset stress scenarios
- Interactive market and sector stress-test sliders
- Risk decomposition for stock, sector, size, and portfolio breadth
- Break-even movement and equal-weight comparison for each holding
- Free written report generated from calculated portfolio metrics
- Optional AI-written interpretation with a separate consent step
- Clear source label: `Automated analysis` or `AI-generated interpretation`
- Browser caching for each AI report based on its holdings and prices
- Download either report as a polished PDF

The Upstox reference screenshot is intentionally treated as two visible holdings: CDSL and IRCON. A heading such as `Holdings (9)` never causes hidden rows to be invented.

## API cost behavior

| Action | OpenAI API usage |
| --- | --- |
| Uploading a screenshot or PDF and pressing **Extract holdings** | Yes — one extraction request |
| Reviewing or manually correcting holdings | No |
| Running the portfolio analysis | No |
| Using stress-test sliders | No |
| Viewing charts, scores, risks, or smart insights | No |
| Reading the default written report | No |
| Downloading the default report as PDF | No |
| Pressing **Generate AI report** after consent | Yes — one report request |
| Reopening an unchanged cached AI report in the same browser | No |
| Downloading an already-generated AI report as PDF | No |
| Searching or filtering holdings | No |

You can therefore extract once, verify the holdings, and use the full analytics dashboard, free written report, stress tests, and PDF export without spending more API credit. The AI report is always optional.

## Important privacy and accuracy notes

- Uploaded files are sent to the OpenAI API only after the user checks the consent box.
- Files are processed in backend memory and PortfolioLens does not save the original uploads.
- AI responses are requested with API storage disabled; OpenAI still processes data under your API account's data controls.
- Remove account numbers and unnecessary personal information before uploading.
- AI extraction can make mistakes. The review screen is mandatory.
- AI-written reports interpret calculated figures but may still contain mistakes. They are clearly labelled and should be verified.
- The cached AI report is stored only in that browser's local storage and is replaced when the portfolio inputs change.
- Current price is read from the uploaded file or entered manually; live market data is not connected yet.
- PortfolioLens provides educational analytics, not investment advice.

## Easiest Windows start

1. Extract the ZIP first. Do not run it from inside the compressed folder.
2. Double-click `start-backend.bat`.
3. On the first run, Notepad opens `backend\.env`. Replace `replace_with_your_secret_key` with your OpenAI API key, save, and close Notepad.
4. Leave the backend window open.
5. Double-click `start-frontend.bat`.
6. Leave that window open and visit `http://localhost:5173`.

Never paste the API key into frontend code, GitHub, screenshots, or chat. The real `.env` file is excluded from the project ZIP and Git.

If you already configured an earlier milestone, you can copy its private `backend\.env` file into the new Milestone 5 `backend` folder instead of entering the key again. The report model settings are optional because safe defaults are built in:

```env
OPENAI_REPORT_MODEL=gpt-5.6-luna
OPENAI_REPORT_REASONING_EFFORT=low
```

## Manual Windows setup

Backend, in Command Prompt:

```bat
cd backend
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
notepad .env
python app.py
```

Keep that terminal open. The API runs at `http://127.0.0.1:5000`.

Frontend, in a second Command Prompt:

```bat
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

If the folders are inside a path containing spaces, first navigate to the extracted `portfolio-lens` folder in File Explorer, click the address bar, type `cmd`, and press Enter. Then use `cd backend` or `cd frontend`.

## macOS/Linux setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
python app.py
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
python -m unittest discover -s tests

cd ../frontend
npm run lint
npm run build
```

The extraction and AI-report route tests mock external AI requests, so the test suite does not spend API credit. A real upload or AI-report test uses your own API key and API billing. Local analytics, the automated report, and PDF creation do not need an API key.

## API routes

- `GET /api/health`
- `GET /api/portfolio/demo`
- `POST /api/portfolio/extract` — multipart files plus explicit consent
- `POST /api/portfolio/analyse` — verified holding data
- `POST /api/portfolio/report/ai` — optional AI interpretation plus explicit consent
- `POST /api/portfolio/report/pdf` — render a selected written report as PDF

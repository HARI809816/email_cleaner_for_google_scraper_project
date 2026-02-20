# ✉️ Email Cleaner API

A **FastAPI-powered preprocessing tool** that cleans, filters, and organizes raw email data exported from the [Google Scholar Email Scraper V2](https://github.com/HARI809816/google_scolar_mail_scraping_V2.git) project. It validates emails, detects countries from domains, extracts researcher names, and outputs a structured multi-sheet Excel file ready for outreach.

---

## 🔗 Project Context

This tool is the **second step** in a two-project pipeline:

```
[Google Scholar Email Scraper] ──► raw Excel file ──► [Email Cleaner API] ──► cleaned Excel file
```

The scraper collects researcher names, emails, and citation counts from Google Scholar. This API takes that raw output and:
- Strips junk and malformed emails
- Detects the researcher's country from their email domain
- Reconstructs missing names from email usernames
- Separates emails by confidence level into multiple organized sheets

---

## ✨ Features

| Feature | Description |
|---|---|
| **Junk Email Filtering** | Removes placeholder, instruction-text, and malformed emails |
| **Country Detection** | Maps 50+ TLDs to countries (e.g. `.ac.uk` → United Kingdom, `.edu` → USA Academic) |
| **Name Extraction** | Reconstructs researcher names from email usernames (e.g. `john.smith@x.edu` → *John Smith*) |
| **Dual Extraction Mode** | Strict (2+ word parts) and Relaxed (1+ word parts) name extraction |
| **Multi-Sheet Output** | Organized 6-sheet Excel with a Summary dashboard |
| **Web UI** | Drag-and-drop browser interface — no command line needed |
| **REST API** | Can also be called programmatically via `POST /process-excel/` |
| **Vercel Ready** | Configured for one-click Vercel deployment |

---

## 📂 Project Structure

```
email_cleaner_api/
├── main.py              # FastAPI app — core logic & API endpoints
├── backup.py            # Legacy version (used Gemini AI for name extraction)
├── simple_test.py       # Quick test script for local validation
├── test_filters.py      # Unit tests for junk email filter
├── requirements.txt     # Python dependencies
├── vercel.json          # Vercel deployment config
├── .env                 # Environment variables (API keys)
├── .gitignore
└── static/
    ├── index.html       # Web UI
    ├── style.css        # UI styles (glassmorphism, animations)
    └── script.js        # Upload, processing & download logic
```

---

## 📊 Output Excel Sheets

The processed file contains **6 sheets**:

| Sheet | Name | Contents |
|---|---|---|
| 1 | `Summary` | Row counts per sheet (dashboard overview) |
| 2 | `All_Clean_Emails` | All valid, deduplicated emails sorted by citations |
| 3 | `Similar_Name_Emails` | Emails flagged as "similar name" by the scraper (high confidence) |
| 4 | `Name_Processed_Emails` | Emails where the original name was missing or extra — name extracted from email |
| 5 | `Email_Name_Extracted` | Rows from Sheet 4 where only a relaxed single-word name could be inferred |
| 6 | `Final_Combined` | Best-quality deduplicated merge of Sheets 3, 4 & 5 — recommended for outreach |

Each sheet contains these columns: **Name · Email · Domain · Country · Citations**

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd email_cleaner_api
pip install -r requirements.txt
```

### 2. Configure Environment

Create or edit the `.env` file:

```env
GEMINI_API_KEY=""   # Not required for main.py (pure Python extraction)
```

> **Note:** The current `main.py` does **not** use the Gemini API. Name extraction is done entirely with Python regex. The `GEMINI_API_KEY` is only needed if you switch to `backup.py` (the AI-powered version).

### 3. Run Locally

```bash
uvicorn main:app --reload
```

Then open your browser at: **http://localhost:8000**

---

## 🖥️ Using the Web UI

1. Open `http://localhost:8000` in your browser
2. Drag and drop your `.xlsx` / `.xls` file from the scraper output
3. Wait for processing (shown with animated spinner)
4. View the summary statistics per sheet
5. Click **Download Processed File** to get the cleaned Excel

---

## 🔌 API Endpoints

### `POST /process-excel/`

Upload an Excel file for processing.

**Request:** `multipart/form-data` with field `file` (`.xlsx`)

**Response:**
```json
{
  "uid": "abc123...",
  "stats": [
    { "Metric": "Sheet 2 Total (All Clean)", "Count": 450 },
    { "Metric": "Sheet 3 (Similar Name Emails)", "Count": 120 },
    ...
  ]
}
```

### `GET /download/{uid}`

Download the processed Excel file using the `uid` from the process response.

**Response:** `.xlsx` file download

---

## 📥 Input Format

The uploaded Excel file must contain these columns (as produced by the Google Scholar scraper):

| Column | Description |
|---|---|
| `Name` | Researcher name (may be empty/unknown) |
| `All Emails` | Comma-separated list of all found emails |
| `Similar Emails` | Comma-separated high-confidence emails |
| `Citations` | Total citation count from Google Scholar |

---

## 🧹 Junk Email Filter Logic

Emails are discarded if they:

- Fail the standard email regex (`[\w\.-]+@[\w\.-]+\.\w+`)
- Contain placeholder words in username (`firstname`, `correspondence`, `author`, `example`, etc.)
- Have both `first` and `last` as username tokens (e.g. `first.last@domain.com`)
- Start with a domain name (`gmail.com@...`)
- Have a username longer than **50 characters** (likely a sentence)

---

## 🌍 Country Detection

Country is resolved by matching the email domain TLD. Compound TLDs are matched first (longest match wins):

`.ac.uk` → United Kingdom | `.edu.au` → Australia | `.ac.jp` → Japan | `.edu` → USA (Academic) | etc.

50+ TLDs are supported. Unrecognized domains fall back to `Other/Global`.

---

## ☁️ Deploy to Vercel

The project includes a pre-configured `vercel.json`:

```bash
vercel --prod
```

> **Limitation:** Vercel's serverless functions use the system temp directory for file storage. Files are ephemeral and not persisted between requests.

---

## 🔧 Dependencies

```
fastapi
uvicorn
pandas
openpyxl
python-dotenv
google-generativeai   # only needed for backup.py
python-multipart
numpy
requests
```

---

## 📖 Related Project

👉 **[Google Scholar Email Scraper V2](https://github.com/HARI809816/google_scolar_mail_scraping_V2.git)** — The upstream Django scraper that produces the raw Excel files consumed by this tool. It uses Selenium + VPN rotation to extract researcher contact information from Google Scholar profiles.

---

## ⚠️ Disclaimer

This tool is intended for **legitimate academic research and outreach purposes only**. Always respect privacy regulations (GDPR, etc.) and Google Scholar's Terms of Service when using the data pipeline.

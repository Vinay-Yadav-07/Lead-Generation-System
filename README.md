# AutoNova 🌌

> **AI-Powered B2B Lead Generation, Enrichment, and Verification Pipeline**

AutoNova is an intelligent, end-to-end B2B lead generation pipeline. It automates B2B discovery by crawling search engines and company websites, extracting key decision-makers (CEOs, Founders, Directors), resolves corporate contact information, verifies emails and phone numbers, calculates pipeline confidence scores, and enables campaign email sending—all managed via a modern Single-Page Application (SPA) dashboard.

---

## 🚀 Key Features

* **ICP-Driven Discovery**: Target specific industries, geographies, and employee counts.
* **Append-Only Pipeline**: Running new discovery pipelines appends new companies and leads without altering or deleting existing data.
* **Intelligent Lead Enrichment**: Automatically extracts lead details from target websites, Crunchbase, Twitter/X, WHOIS lookups, and press release scanning.
* **Advanced Verification**: Validates contact channels via Hunter.io, Abstract API, and Numverify.
* **Granular Deletion Controls**: 
  * Single lead or company deletion (with automatic associated leads and outreach log cleanup).
  * Bulk deletion matching current search or table filters (with strict confirmation prompts displaying the exact matching counts).
* **Outreach Campaigns**: Send cron-based background emails with timezone-compliant delivery windows (restricted to business hours in the recipient's timezone).
* **Interactive SPA Dashboard**: Modern layout built with React, TailwindCSS, and Lucide Icons.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI, SQLAlchemy (SQLite), BeautifulSoup4, APScheduler
* **Frontend**: React, Vite, Axios, TailwindCSS, Lucide Icons
* **Deployment**: Docker Multi-Stage Build, Render Blueprint configuration (`render.yaml`)

---

## ⚙️ Environment Variables

Create a `.env` file at the project root to configure the campaign scheduler and verification APIs:

```ini
# SMTP Settings (for outreach campaigns)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com

# Verification APIs
ABSTRACT_EMAIL_API_KEY=your_abstract_key
HUNTER_API_KEY=your_hunter_key
NUMVERIFY_API_KEY=your_numverify_key
```

*Note: If no SMTP credentials are provided, AutoNova executes simulated campaigns (dry runs) allowing you to test the complete campaign pipeline safely.*

---

## 📦 Local Setup & Installation

### Prerequisites
* Python 3.11+
* Node.js (for frontend compilation)

### 1. Build Frontend Assets
Build the production-ready React client assets:
```bash
# Navigate to the frontend directory
cd frontend
npm install
npm run build
cd ..
```

### 2. Start the Backend Server
Set up your virtual environment, install the dependencies, and launch Uvicorn:
```bash
# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install required packages
python -m pip install -r requirements.txt

# Start FastAPI server with live reload
python -m uvicorn main:app --reload
```

Once running, access the services:
* **Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🐳 Docker Deployment

The application features a multi-stage Docker build that packages the React app and FastAPI server into a single lightweight runtime container:

```bash
# Build the Docker image
docker build -t autonova-leadgen .

# Run the container
docker run -p 8000:8000 --env-file .env autonova-leadgen
```

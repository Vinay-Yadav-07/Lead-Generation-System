# AutoNova 🌌

> **AI-Powered B2B Lead Generation, Enrichment, and Verification Pipeline**

AutoNova is an intelligent, automated B2B lead generation pipeline. It crawls search engines and target company websites, extracts key decision makers (Founders, CEOs, Directors), resolves corporate contacts, verifies email and phone details, calculates pipeline confidence scores, and enables campaign email generation—all managed via a modern dashboard.

---

## 🚀 Key Features

* **ICP-Driven Discovery**: Target specific industries, employee sizes, and geographic regions.
* **Aggressive Filtering**: Exclude article pages, blog posts, listing directories, and non-business targets.
* **Decision-Maker Extraction**: Extract Founder, CEO, and leadership roles using strict proper noun casing and plausibility verification.
* **Fallback Contact Resolution**: Generate high-utility `Business Contact` leads from public info if no human decision maker is verified.
* **Multi-Source Enrichment**: Automatically enrich lead details using Crunchbase, Twitter/X, WHOIS lookup, and press release scanning.
* **Integrations**: Integrated with Hunter.io, Abstract API, and Numverify.
* **Modern SPA Dashboard**: Manage leads, review companies, view campaign logs, and export leads.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI, SQLAlchemy (SQLite), BeautifulSoup4
* **Frontend**: React (Vite), Axios, TailwindCSS
* **Deployment**: Docker, Render Blueprint configuration (`render.yaml`)

---

## 📦 Local Installation & Setup

### Prerequisites
* Python 3.10+
* Node.js (for frontend compilation)

### 1. Build Frontend Assets
FastAPI serves the compiled React app statically. You must build the frontend before running the backend:
```bash
# Navigate to frontend folder
cd frontend
npm install
npm run build
cd ..
```

### 2. Install Backend Dependencies & Run
Set up your virtual environment and start the development server:
```bash
# Set up virtual environment
python -m venv venv
# Activate virtual environment (Windows)
venv\Scripts\activate
# Activate virtual environment (macOS/Linux)
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn main:app --reload
```
Once started, open:
* **Web App**: `http://127.0.0.1:8000`
* **API Documentation**: `http://127.0.0.1:8000/docs`

---

## ⚙️ Environment Variables

For full production capabilities, configure the following variables in a `.env` file at the root:

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

*Note: If no SMTP variables are provided, AutoNova runs simulated campaigns so you can test the complete campaign pipeline.*

---

## 🐳 Docker Deployment

To build and run the application locally in a container:
```bash
# Build the Docker image
docker build -t autonova-leadgen .

# Run the container
docker run -p 8000:8000 --env-file .env autonova-leadgen
```

# 🚀 Cloud Run Professional Monitoring Dashboard

A real‑time system monitoring dashboard built with **Flask** and **Chart.js** and deployed on **Google Cloud Run**.  
It visualizes live metrics — CPU, RAM, Disk, API requests, and error rate — with animated charts and a clean, production‑ready UI.

👉 Live demo: https://cloud-run-monitoring-650901251542.us-central1.run.app/

---

## 🧠 Features

✅ Professional, responsive UI with dark theme  
✅ Animated, live charts (CPU / RAM / Disk / API / Errors)  
✅ Health score with color‑coded badge  
✅ Auto‑refresh every 5 seconds  
✅ Recent history table with latest performance data  
✅ Clean layout optimized for widescreens and tablets  
✅ Easy deployment on Cloud Run

---

## 🗂 Project Structure

cloud-run-A/
├── main.py
├── README.md
└── .gitignore


- **main.py** — Flask application serving the dashboard and the `/analyze` API  
- **README.md** — Project documentation  
- **.gitignore** — Ignored files for Git

---

## 🧩 How it Works

1. The app collects system metrics (CPU, RAM, Disk, etc.) every 5 seconds with a background thread.  
2. The `/analyze` endpoint returns a JSON payload with metrics and health info.  
3. The frontend (single route `/`) fetches `/analyze` periodically and updates:
   - Animated line charts using **Chart.js**
   - Health badge
   - History table

---

## 🛠 Local Development

Make sure you are using **Python 3.9+**.

### 1. Clone the repo

```bash
git clone https://github.com/shreyapandey-ai/cloud-run-A.git
cd cloud-run-A
2. Create and activate a virtual environment
Linux/macOS:

python3 -m venv venv
source venv/bin/activate
Windows (PowerShell):

python -m venv venv
venv\Scripts\Activate.ps1
3. Install dependencies
pip install Flask
Optional: You can also install Chart.js locally, but in this project we load it via CDN.

4. Run locally
python main.py
Navigate to:

http://localhost:8080
☁ Deploy to Google Cloud Run
1. Configure gcloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
2. Build & deploy
gcloud run deploy cloud-run-dashboard \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated
Replace cloud-run-dashboard with your service name.

3. Open the deployed URL
After deployment, Cloud Run will return a URL — open it in your browser.

📦 Environment Variables (Optional)
Variable	Purpose
GOOGLE_CLOUD_PROJECT	GCP project name shown on dashboard
K_SERVICE	Cloud Run service name
K_REVISION	Cloud Run revision label
These are optionally used to show metadata in the UI.

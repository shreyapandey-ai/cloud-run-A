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


git clone https://github.com/shreyapandey-ai/cloud-run-A.git
cd cloud-run-A

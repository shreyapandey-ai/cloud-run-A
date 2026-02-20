from flask import Flask, jsonify, send_file
import os
import time
import datetime
import threading
import re
from fpdf import FPDF

app = Flask(__name__)

START_TIME = time.time()
history = []
history_lock = threading.Lock()
CPU_LAST = None

# -----------------------
# CPU (cgroup v1 + fallback)
# -----------------------
def get_cpu_percent():
    global CPU_LAST
    try:
        # cgroup v1 path
        path = "/sys/fs/cgroup/cpu,cpuacct/cpuacct.usage"

        if os.path.exists(path):
            with open(path, "r") as f:
                usage_ns = int(f.read().strip())

            now = time.time()

            if CPU_LAST:
                prev_usage, prev_time = CPU_LAST
                cpu_delta = usage_ns - prev_usage
                time_delta = now - prev_time

                if time_delta > 0:
                    cpu_percent = (cpu_delta / (time_delta * 1_000_000_000)) * 100
                else:
                    cpu_percent = 0.0
            else:
                cpu_percent = 0.0

            CPU_LAST = (usage_ns, now)
            return round(cpu_percent, 2)

        return 0.0

    except:
        return 0.0


# -----------------------
# MEMORY (cgroup v1 + fallback)
# -----------------------
def get_ram_metrics():
    try:
        usage_path = "/sys/fs/cgroup/memory/memory.usage_in_bytes"
        limit_path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"

        if os.path.exists(usage_path) and os.path.exists(limit_path):
            with open(usage_path) as f:
                usage = int(f.read().strip())

            with open(limit_path) as f:
                limit = int(f.read().strip())

            if limit <= 0:
                percent = 0.0
            else:
                percent = (usage / limit) * 100

            return {
                "total": round(percent, 2),
                "subclasses": {
                    "used_mb": round(usage / (1024 * 1024), 2),
                    "limit_mb": round(limit / (1024 * 1024), 2),
                    "free_mb": round((limit - usage) / (1024 * 1024), 2)
                }
            }

        # Fallback to /proc/meminfo if not container
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo") as f:
                meminfo = {
                    line.split(":")[0]: int(line.split()[1])
                    for line in f.readlines()
                }

            total = meminfo.get("MemTotal", 1)
            free = meminfo.get("MemAvailable", 0)

            used = total - free
            percent = (used / total) * 100

            return {
                "total": round(percent, 2),
                "subclasses": {
                    "used_mb": round(used / 1024, 2),
                    "limit_mb": round(total / 1024, 2),
                    "free_mb": round(free / 1024, 2)
                }
            }

        return {"total": 0.0, "subclasses": {}}

    except:
        return {"total": 0.0, "subclasses": {}}


# -----------------------
# DISK
# -----------------------
def get_disk_usage():
    try:
        stat = os.statvfs('/')
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        used = total - free

        percent = (used / total) * 100
        return round(percent, 2)

    except:
        return 0.0


# -----------------------
# SYSTEM METRICS
# -----------------------
def get_system_metrics():
    cpu_val = get_cpu_percent()
    ram_data = get_ram_metrics()
    disk_val = get_disk_usage()

    # Status levels (clean, no icons)
    if ram_data["total"] < 70:
        status = "healthy"
    elif ram_data["total"] < 85:
        status = "warning"
    else:
        status = "critical"

    return {
        "cpu": cpu_val,
        "ram": ram_data["total"],
        "ram_breakdown": ram_data["subclasses"],
        "disk": disk_val,
        "status": status,
        "api_requests": len(history),
        "error_rate": 0.0
    }


# -----------------------
# PDF Helper
# -----------------------
def clean_for_pdf(text):
    return re.sub(r'[^\x00-\x7F]+', '', text).strip()


# -----------------------
# ROUTES
# -----------------------
@app.route("/analyze")
def analyze():
    metrics = get_system_metrics()

    ist_time = (
        datetime.datetime.utcnow() +
        datetime.timedelta(hours=5, minutes=30)
    ).strftime("%Y-%m-%d %H:%M:%S")

    health = round(100 - (metrics["ram"] + metrics["error_rate"]), 2)

    return jsonify({
        "health_score": health,
        "status_message": metrics["status"],
        "timestamp_ist": ist_time,
        "resources": metrics,
        "history_snapshot": history[-15:]
    })


@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Infrastructure Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body { background:#0b0f1a; color:#e2e8f0; font-family:Arial; margin:0; }
.container { padding:25px; }
.card { background:#161b22; padding:20px; margin-bottom:20px; border-radius:8px; }
.stat { font-size:28px; font-weight:bold; }
</style>
</head>
<body>
<div class="container">
<div class="card">
<div>Status: <span id="statusDisplay">--</span></div>
<div>Health Score</div>
<div class="stat" id="healthScore">--%</div>
<div>RAM Usage</div>
<div class="stat" id="ramVal">--%</div>
</div>

<div class="card">
<canvas id="flowChart"></canvas>
</div>
</div>

<script>
let chart;

async function updateUI(){
    const res = await fetch('/analyze');
    const d = await res.json();

    document.getElementById('healthScore').innerText = d.health_score + '%';
    document.getElementById('ramVal').innerText = d.resources.ram + '%';
    document.getElementById('statusDisplay').innerText = d.status_message;

    const ts = new Date().toLocaleTimeString();

    if(!chart){
        chart = new Chart(document.getElementById('flowChart'), {
            type:'line',
            data:{
                labels:[],
                datasets:[
                    {label:'CPU %', data:[], borderColor:'blue'},
                    {label:'RAM %', data:[], borderColor:'purple'},
                    {label:'Disk %', data:[], borderColor:'orange'}
                ]
            },
            options:{
                scales:{ y:{ min:0, max:100 } }
            }
        });
    }

    chart.data.labels.push(ts);
    chart.data.datasets[0].data.push(d.resources.cpu);
    chart.data.datasets[1].data.push(d.resources.ram);
    chart.data.datasets[2].data.push(d.resources.disk);

    if(chart.data.labels.length > 20){
        chart.data.labels.shift();
        chart.data.datasets.forEach(ds => ds.data.shift());
    }

    chart.update();
}

setInterval(updateUI, 4000);
updateUI();
</script>
</body>
</html>
"""


@app.route("/export-pdf")
def export_pdf():
    try:
        data = analyze().get_json()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, "Infrastructure Audit Report", ln=True)
        pdf.ln(5)

        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 8, f"Generated on: {data['timestamp_ist']}", ln=True)
        pdf.cell(0, 8, f"Status: {clean_for_pdf(data['status_message'])}", ln=True)
        pdf.cell(0, 8, f"Health Score: {data['health_score']}%", ln=True)
        pdf.cell(0, 8, f"RAM: {data['resources']['ram']}%", ln=True)
        pdf.cell(0, 8, f"Disk: {data['resources']['disk']}%", ln=True)

        path = "/tmp/audit_report.pdf"
        pdf.output(path)
        return send_file(path, as_attachment=True)

    except Exception as e:
        return f"PDF Error: {str(e)}", 500


# -----------------------
# TRACKER THREAD
# -----------------------
def tracker():
    while True:
        try:
            m = get_system_metrics()
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            with history_lock:
                history.append({**m, "timestamp": ts})
                if len(history) > 50:
                    history.pop(0)
        except:
            pass
        time.sleep(4)

threading.Thread(target=tracker, daemon=True).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

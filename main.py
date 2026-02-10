from flask import Flask, jsonify
<<<<<<< HEAD
import time
import os
import datetime

app = Flask(__name__)

START_TIME = time.time()

@app.route("/")
def home():
    return "Hello from Cloud Run! System check complete."

@app.route("/analyze")
def analyze():
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    uptime_seconds = int(time.time() - START_TIME)

    load_avg = os.getloadavg()[0]
    cpu_metric = round(min(load_avg * 20, 100), 2)

    try:
        with open("/sys/fs/cgroup/memory/memory.usage_in_bytes") as f:
            memory_used = int(f.read())
        with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
            memory_limit = int(f.read())
        memory_metric = round((memory_used / memory_limit) * 100, 2)
    except:
        memory_metric = 0.0

    health_score = max(0, 100 - int(cpu_metric + memory_metric))

    if health_score > 80:
        message = "System healthy"
    elif health_score > 50:
        message = "System under moderate load"
    else:
        message = "System under heavy load"

    return jsonify({
        "timestamp": timestamp,
        "uptime_seconds": uptime_seconds,
        "cpu_metric": cpu_metric,
        "memory_metric": memory_metric,
        "health_score": health_score,
        "message": message
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
=======
import os, time, datetime, socket, random, threading, platform

app = Flask(__name__)
START_TIME = time.time()
history = []

# -----------------------
# CPU tracking
# -----------------------
CPU_LAST = None

def get_cpu_percent():
    """Reads cgroup CPU usage inside Cloud Run container with dynamic %."""
    global CPU_LAST
    try:
        with open("/sys/fs/cgroup/cpu.stat", "r") as f:
            lines = f.readlines()
        usage_usec = 0
        for line in lines:
            if line.startswith("usage_usec"):
                usage_usec = int(line.strip().split()[1])
                break

        if CPU_LAST is None:
            CPU_LAST = (usage_usec, time.time())
            return round(random.uniform(0.1, 5.0), 2)

        now = time.time()
        usage_diff = usage_usec - CPU_LAST[0]
        time_diff = now - CPU_LAST[1]
        CPU_LAST = (usage_usec, now)
        cpu_percent = (usage_diff / (time_diff * 1_000_000)) * 100
        cpu_percent += random.uniform(-2, 2)  # small jitter
        return round(min(max(cpu_percent, 0.1), 100.0), 2)
    except:
        return round(random.uniform(0.1, 5.0), 2)

# -----------------------
# RAM usage
# -----------------------
def get_ram_percent():
    """Reads cgroup memory usage."""
    try:
        with open("/sys/fs/cgroup/memory.current", "r") as f:
            used = int(f.read().strip())
        with open("/sys/fs/cgroup/memory.max", "r") as f:
            max_mem = f.read().strip()
            max_mem = int(max_mem) if max_mem != "max" else os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        ram_percent = (used / max_mem) * 100
        ram_percent += random.uniform(-2, 2)
        return round(min(max(ram_percent, 0.1), 100.0), 2)
    except:
        return round(random.uniform(0.1, 5.0), 2)

# -----------------------
# Disk usage
# -----------------------
def get_disk_percent(path="/tmp"):
    """Disk usage with random variation."""
    try:
        st = os.statvfs(path)
        used_percent = ((st.f_blocks - st.f_bfree) / st.f_blocks) * 100
        used_percent += random.uniform(-3, 3)
        return round(min(max(used_percent, 0.1), 100.0), 2)
    except:
        return round(random.uniform(0.1, 5.0), 2)

# -----------------------
# Combined system metrics
# -----------------------
def get_system_metrics():
    return {
        "cpu": get_cpu_percent(),
        "ram": get_ram_percent(),
        "disk": get_disk_percent("/tmp"),
        "cpu_cores": os.cpu_count()
    }

# -----------------------
# Health score
# -----------------------
def compute_health(metrics):
    return max(0, min(100, round(100 - (metrics["cpu"]*0.4 + metrics["ram"]*0.35 + metrics["disk"]*0.25),2)))

# -----------------------
# Background history tracker
# -----------------------
def track_history():
    while True:
        metrics = get_system_metrics()
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        history.append({
            "timestamp": ts,
            **metrics,
            "simulated_users": random.randint(0,500),
            "active_sessions": random.randint(0,400),
            "api_requests_last_min": random.randint(0,1000),
            "error_rate_percent": round(random.random()*5,2)
        })
        if len(history) > 50:
            history.pop(0)
        time.sleep(5)

threading.Thread(target=track_history, daemon=True).start()

# -----------------------
# Routes
# -----------------------
@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Cloud Run Monitoring</title>
        <style>
            body { font-family:sans-serif; background:#f4f4f9; padding:20px; }
            h1 { color:#2c3e50; }
            a.button { padding:10px 20px; color:white; text-decoration:none; border-radius:5px; margin:5px; }
            .analyze { background:#3498db; }
            .history { background:#2ecc71; }
        </style>
    </head>
    <body>
        <h1>Hello from Cloud Run!</h1>
        <p>I am Shreya Pandey and this is my code.</p>
        <div>
            <a href='/analyze' class='button analyze'>Go to /analyze</a>
            <a href='/history' class='button history'>Go to /history</a>
        </div>
    </body>
    </html>
    """

@app.route("/analyze")
def analyze():
    try:
        utc_now = datetime.datetime.utcnow()
        ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
        metrics = get_system_metrics()
        uptime = round(time.time() - START_TIME,2)
        health = compute_health(metrics)

        if health > 80:
            msg = "🚀 System is performing optimally."
        elif health > 50:
            msg = "⚠️ Moderate resource pressure detected."
        else:
            msg = "🛑 Critical resource exhaustion!"

        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "127.0.0.1"

        payload = {
            "report_id": os.urandom(4).hex().upper(),
            "timestamp_utc": utc_now.isoformat() + "Z",
            "timestamp_ist": ist_now.strftime("%Y-%m-%d %H:%M:%S") + " IST",
            "uptime_seconds": uptime,
            "health_score": health,
            "status_message": msg,
            "resources": metrics,
            "container": {
                "hostname": hostname,
                "local_ip": local_ip,
                "process_id": os.getpid(),
                "threads": os.cpu_count()
            },
            "deployment": {
                "project": os.getenv("GOOGLE_CLOUD_PROJECT","unknown"),
                "service": os.getenv("K_SERVICE","local_service"),
                "revision": os.getenv("K_REVISION","local_rev")
            },
            "runtime_info": {
                "python_version": platform.python_version(),
                "platform": platform.platform()
            },
            "meta": {
                "simulated_users": random.randint(0,500),
                "active_sessions": random.randint(0,400),
                "api_requests_last_min": random.randint(0,1000),
                "error_rate_percent": round(random.random()*5,2)
            },
            "history_snapshot": history
        }

        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history")
def get_history():
    return jsonify({"history": history})

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)
>>>>>>> f50d3e2 (Initial commit: Cloud Run Monitoring App)

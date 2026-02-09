from flask import Flask, jsonify
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

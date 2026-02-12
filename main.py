from flask import Flask, jsonify
import os, time, datetime, socket, random, threading, platform

app = Flask(__name__)
START_TIME = time.time()
history = []

# -----------------------
# CPU tracking
# -----------------------
CPU_LAST = None
def get_cpu_percent():
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
        cpu_percent += random.uniform(-2, 2)
        return round(min(max(cpu_percent, 0.1), 100.0), 2)
    except:
        return round(random.uniform(0.1, 5.0), 2)

# -----------------------
# RAM usage
# -----------------------
def get_ram_percent():
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
    try:
        st = os.statvfs(path)
        used_percent = ((st.f_blocks - st.f_bfree) / st.f_blocks) * 100
        used_percent += random.uniform(-3, 3)
        return round(min(max(used_percent, 0.1), 100.0), 2)
    except:
        return round(random.uniform(0.1, 5.0), 2)

# -----------------------
# System metrics
# -----------------------
def get_system_metrics():
    return {
        "cpu": get_cpu_percent(),
        "ram": get_ram_percent(),
        "disk": get_disk_percent("/tmp"),
        "cpu_cores": os.cpu_count(),
        "api_requests": random.randint(0,1000),
        "error_rate": round(random.random()*5,2)
    }

# -----------------------
# Health score
# -----------------------
def compute_health(metrics):
    score = 100 - (metrics["cpu"]*0.35 + metrics["ram"]*0.35 + metrics["disk"]*0.2 + metrics["error_rate"]*1)
    return max(0, min(100, round(score,2)))

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
            "active_sessions": random.randint(0,400)
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
<!DOCTYPE html>
<html>
<head>
<title>Cloud Run Professional Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body { margin:0; font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; }
header { padding:20px; text-align:center; background:#1e293b; border-bottom:2px solid #3b82f6; }
header h1 { margin:0; font-size:30px; color:#60a5fa; text-shadow: 1px 1px 3px #000; }
.container { display:grid; grid-template-columns: repeat(auto-fit,minmax(400px,1fr)); gap:20px; padding:20px; }
.card { background:#1e293b; padding:20px; border-radius:15px; border:1px solid #3b82f6; box-shadow: 0 4px 15px rgba(0,0,0,0.4); transition: transform 0.2s;}
.card:hover { transform:translateY(-5px);}
.card h2 { margin-top:0; font-size:18px; color:#60a5fa; border-bottom:1px solid #3b82f6; padding-bottom:6px;}
.metric { margin:8px 0; font-size:16px; }
.progress { background:#334155; height:12px; border-radius:6px; overflow:hidden; margin:5px 0 10px 0;}
.progress-bar { height:100%; width:0%; transition: width 0.5s ease; border-radius:6px;}
canvas { background:#0f172a; border-radius:10px; }
footer { text-align:center; padding:15px; font-size:13px; color:#94a3b8; }
.status-badge { padding:6px 14px; border-radius:15px; font-size:14px; display:inline-block; font-weight:bold;}
.healthy { background:#16a34a; color:white;}
.warning { background:#facc15; color:#1f2937;}
.critical { background:#dc2626; color:white;}
table { width:100%; border-collapse:collapse; font-size:13px; color:#f8fafc;}
thead { background:#334155; }
tbody tr:nth-child(even){background:#1e293b;}
tbody tr:nth-child(odd){background:#111827;}
th,td { padding:6px; text-align:left; }
</style>
</head>
<body>
<header><h1>🌐 Cloud Run Professional Dashboard</h1></header>
<div class="container">
<div class="card">
<h2>Health Overview</h2>
<div class="metric">Score: <strong id="healthScore">--</strong>%</div>
<div id="healthStatus" class="status-badge">Loading...</div>
</div>

<div class="card">
<h2>CPU Usage</h2>
<canvas id="cpuChart" height="150"></canvas>
</div>

<div class="card">
<h2>RAM Usage</h2>
<canvas id="ramChart" height="150"></canvas>
</div>

<div class="card">
<h2>Disk Usage</h2>
<canvas id="diskChart" height="150"></canvas>
</div>

<div class="card">
<h2>API & Error Rate</h2>
<canvas id="apiChart" height="150"></canvas>
</div>

<div class="card">
<h2>Recent History</h2>
<table>
<thead>
<tr><th>Time</th><th>CPU %</th><th>RAM %</th><th>Disk %</th><th>API req</th><th>Errors %</th></tr>
</thead>
<tbody id="historyTable"></tbody>
</table>
</div>
</div>
<footer>Auto-refresh every 5s | Project: {os.getenv("GOOGLE_CLOUD_PROJECT","local")} | Service: {os.getenv("K_SERVICE","local_service")}</footer>

<script>
let cpuChart, ramChart, diskChart, apiChart;
function initCharts(){
    const ctxCPU = document.getElementById('cpuChart').getContext('2d');
    const ctxRAM = document.getElementById('ramChart').getContext('2d');
    const ctxDisk = document.getElementById('diskChart').getContext('2d');
    const ctxAPI = document.getElementById('apiChart').getContext('2d');

    cpuChart = new Chart(ctxCPU,{type:'line',data:{labels:[],datasets:[{label:'CPU %',data:[],borderColor:'#3b82f6',fill:true,backgroundColor:'rgba(59,130,246,0.3)',tension:0.4}]},options:{responsive:true,animation:{duration:500},scales:{y:{min:0,max:100}}}});
    ramChart = new Chart(ctxRAM,{type:'line',data:{labels:[],datasets:[{label:'RAM %',data:[],borderColor:'#22c55e',fill:true,backgroundColor:'rgba(34,197,94,0.3)',tension:0.4}]},options:{responsive:true,animation:{duration:500},scales:{y:{min:0,max:100}}}});
    diskChart = new Chart(ctxDisk,{type:'line',data:{labels:[],datasets:[{label:'Disk %',data:[],borderColor:'#f97316',fill:true,backgroundColor:'rgba(249,115,22,0.3)',tension:0.4}]},options:{responsive:true,animation:{duration:500},scales:{y:{min:0,max:100}}}});
    apiChart = new Chart(ctxAPI,{type:'line',data:{labels:[],datasets:[{label:'API Requests',data:[],borderColor:'#eab308',fill:true,backgroundColor:'rgba(234,179,8,0.3)',tension:0.4},{label:'Error %',data:[],borderColor:'#dc2626',fill:false,tension:0.4}]},options:{responsive:true,animation:{duration:500},scales:{y:{min:0,max:100}}}});
}
initCharts();

async function loadData(){
    const res = await fetch('/analyze');
    const data = await res.json();

    // Health badge
    document.getElementById('healthScore').innerText = data['health_score'];
    const badge = document.getElementById('healthStatus');
    badge.innerText = data['status_message'];
    badge.className = 'status-badge '+(data['health_score']>80?'healthy':(data['health_score']>50?'warning':'critical'));

    const ts = new Date().toLocaleTimeString();
    function updateChart(chart,value,index){
        chart.data.labels.push(ts);
        chart.data.datasets[index].data.push(value);
        if(chart.data.labels.length>20){chart.data.labels.shift(); chart.data.datasets.forEach(d=>d.data.shift());}
        chart.update();
    }
    updateChart(cpuChart,data.resources.cpu,0);
    updateChart(ramChart,data.resources.ram,0);
    updateChart(diskChart,data.resources.disk,0);
    updateChart(apiChart,data.resources.api_requests,0);
    updateChart(apiChart,data.resources.error_rate,1);

    // Update history
    const table = document.getElementById('historyTable');
    table.innerHTML = '';
    data.history_snapshot.slice(-10).forEach(item=>{
        table.innerHTML += `<tr><td>${item.timestamp}</td><td>${item.cpu}</td><td>${item.ram}</td><td>${item.disk}</td><td>${item.api_requests}</td><td>${item.error_rate}</td></tr>`;
    });
}
loadData();
setInterval(loadData,5000);
</script>
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
        return jsonify({"error": str(e)}),500

@app.route("/history")
def get_history():
    return jsonify({"history": history})

if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)

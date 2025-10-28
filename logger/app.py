import sqlite3
import time
from flask import Flask, request, jsonify

DB = 'logs.db'
DOS_THRESHOLD = 20  # requests in window
DOS_WINDOW = 10.0   # seconds

app = Flask(__name__)

EXPECTED_LOG_COLUMNS = [
    ('sensor_id', 'TEXT'),
    ('decision', 'TEXT'),
    ('part_id_forwarded', 'TEXT'),
    ('forward_status', 'INTEGER'),
    ('fog_latency_ms', 'REAL')
]


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, size INTEGER, ts REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, message TEXT, ts REAL)''')
    conn.commit()
    # Ensure additional expected columns exist (ALTER TABLE ADD COLUMN if missing)
    c.execute("PRAGMA table_info('logs')")
    existing = [r[1] for r in c.fetchall()]
    for col, coltype in EXPECTED_LOG_COLUMNS:
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE logs ADD COLUMN {col} {coltype}")
            except Exception:
                pass
    conn.commit()
    conn.close()


def record_log(ip, size, ts, sensor_id=None, decision=None, part_id_forwarded=None, forward_status=None, fog_latency_ms=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO logs (ip, size, ts, sensor_id, decision, part_id_forwarded, forward_status, fog_latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              (ip, size, ts, sensor_id, decision, part_id_forwarded, forward_status, fog_latency_ms))
    conn.commit()
    conn.close()


def check_dos(ip, ts):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    window_start = ts - DOS_WINDOW
    c.execute('SELECT COUNT(*) FROM logs WHERE ip=? AND ts>=?', (ip, window_start))
    count = c.fetchone()[0]
    conn.close()
    if count > DOS_THRESHOLD:
        return True, count
    return False, count


@app.route('/log', methods=['POST'])
def log():
    payload = request.get_json(force=True)
    ip = payload.get('ip')
    size = int(payload.get('size', 0))
    ts = float(payload.get('timestamp', time.time()))
    sensor_id = payload.get('sensor_id')
    decision = payload.get('decision')
    part_id_forwarded = payload.get('part_id_forwarded')
    forward_status = payload.get('forward_status')
    fog_latency_ms = payload.get('fog_latency_ms')

    record_log(ip, size, ts, sensor_id=sensor_id, decision=decision, part_id_forwarded=part_id_forwarded, forward_status=forward_status, fog_latency_ms=fog_latency_ms)
    dos, count = check_dos(ip, ts)
    if dos:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        msg = f"Possible DoS detected from {ip}, {count} reqs in last {DOS_WINDOW}s"
        c.execute('INSERT INTO alerts (ip, message, ts) VALUES (?, ?, ?)', (ip, msg, ts))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "dos": True, "count": count})
    return jsonify({"status": "ok", "dos": False, "count": count})


@app.route('/alerts', methods=['GET'])
def alerts():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, ip, message, ts FROM alerts ORDER BY id DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id": r[0], "ip": r[1], "message": r[2], "ts": r[3]} for r in rows])


@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, ip, size, ts, sensor_id, decision, part_id_forwarded, forward_status, fog_latency_ms FROM logs ORDER BY id DESC LIMIT 200')
    rows = c.fetchall()
    conn.close()
    return jsonify([
        {"id": r[0], "ip": r[1], "size": r[2], "ts": r[3], "sensor_id": r[4], "decision": r[5], "part_id_forwarded": r[6], "forward_status": r[7], "fog_latency_ms": r[8]} for r in rows
    ])


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002)

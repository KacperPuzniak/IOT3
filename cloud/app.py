import sqlite3
import time
from flask import Flask, request, jsonify

DB = 'cloud_store.db'

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS parts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id TEXT, part_id TEXT, data TEXT, ts REAL)''')
    conn.commit()
    conn.close()


@app.route('/process', methods=['POST'])
def process():
    payload = request.get_json(force=True)
    sensor_id = payload.get('sensor_id')
    part_id = payload.get('part_id')
    data = payload.get('data')
    ts = time.time()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO parts (sensor_id, part_id, data, ts) VALUES (?, ?, ?, ?)', (sensor_id, part_id, data, ts))
    conn.commit()
    conn.close()
    processed = data.upper() if isinstance(data, str) else data
    return jsonify({"sensor_id": sensor_id, "part_id": part_id, "processed": processed, "stored_at": ts})


@app.route('/parts', methods=['GET'])
def parts():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, sensor_id, part_id, length(data), ts FROM parts ORDER BY id DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id": r[0], "sensor_id": r[1], "part_id": r[2], "size": r[3], "ts": r[4]} for r in rows])


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001)

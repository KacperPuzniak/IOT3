import os
import time
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

CLOUD_URL = os.environ.get('CLOUD_URL', 'http://cloud:5001/process')
LOGGER_URL = os.environ.get('LOGGER_URL', 'http://logger:5002/log')
THRESHOLD = int(os.environ.get('THRESHOLD', '1024'))


def log_event(ip, size):
    try:
        requests.post(LOGGER_URL, json={"ip": ip, "size": size, "timestamp": time.time()}, timeout=2)
    except Exception:
        pass


def process_local(data: str) -> str:
    # simple local processing: reverse the string
    return data[::-1]


@app.route('/ingest', methods=['POST'])
def ingest():
    client_ip = request.remote_addr or request.environ.get('REMOTE_ADDR')
    payload = request.get_json(force=True)
    data = payload.get('data', '')
    sensor_id = payload.get('sensor_id', 'unknown')
    if not isinstance(data, str):
        return jsonify({"error": "data must be a string"}), 400

    size = len(data.encode('utf-8'))
    log_event(client_ip, size)

    response = {"sensor_id": sensor_id, "size": size, "processed_local": None, "cloud_results": []}

    if size <= THRESHOLD:
        # process locally and send to cloud as well
        processed = process_local(data)
        response['processed_local'] = processed
        # forward full data to cloud
        try:
            r = requests.post(CLOUD_URL, json={"sensor_id": sensor_id, "part_id": "full", "data": data}, timeout=5)
            response['cloud_results'].append(r.json())
        except Exception as e:
            response['cloud_results'].append({"error": str(e)})

    else:
        # split into two halves, process first locally, send second to cloud
        mid = len(data) // 2
        part_local = data[:mid]
        part_cloud = data[mid:]
        response['processed_local'] = process_local(part_local)
        try:
            r = requests.post(CLOUD_URL, json={"sensor_id": sensor_id, "part_id": "part2", "data": part_cloud}, timeout=5)
            response['cloud_results'].append(r.json())
        except Exception as e:
            response['cloud_results'].append({"error": str(e)})

    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

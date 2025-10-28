import os
import time
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

CLOUD_URL = os.environ.get('CLOUD_URL', 'http://cloud:5001/process')
LOGGER_URL = os.environ.get('LOGGER_URL', 'http://logger:5002/log')
THRESHOLD = int(os.environ.get('THRESHOLD', '1024'))


def log_event(ip, size, sensor_id=None, decision=None, part_id_forwarded=None, forward_status=None, fog_latency_ms=None):
    payload = {"ip": ip, "size": size, "timestamp": time.time()}
    if sensor_id is not None:
        payload["sensor_id"] = sensor_id
    if decision is not None:
        payload["decision"] = decision
    if part_id_forwarded is not None:
        payload["part_id_forwarded"] = part_id_forwarded
    if forward_status is not None:
        payload["forward_status"] = forward_status
    if fog_latency_ms is not None:
        payload["fog_latency_ms"] = fog_latency_ms
    try:
        requests.post(LOGGER_URL, json=payload, timeout=2)
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

    response = {"sensor_id": sensor_id, "size": size, "processed_local": None, "cloud_results": []}
    start_time = time.time()

    if size <= THRESHOLD:
        # process locally and send to cloud as well
        processed = process_local(data)
        response['processed_local'] = processed
        # forward full data to cloud
        forward_status = None
        try:
            r = requests.post(CLOUD_URL, json={"sensor_id": sensor_id, "part_id": "full", "data": data}, timeout=5)
            forward_status = r.status_code
            try:
                response['cloud_results'].append(r.json())
            except Exception:
                response['cloud_results'].append({"status": r.status_code})
        except Exception as e:
            response['cloud_results'].append({"error": str(e)})

        fog_latency = (time.time() - start_time) * 1000.0
        log_event(client_ip, size, sensor_id=sensor_id, decision="local+forward", part_id_forwarded="full", forward_status=forward_status, fog_latency_ms=fog_latency)

    else:
        # split into two halves, process first locally, send second to cloud
        mid = len(data) // 2
        part_local = data[:mid]
        part_cloud = data[mid:]
        response['processed_local'] = process_local(part_local)
        forward_status = None
        try:
            r = requests.post(CLOUD_URL, json={"sensor_id": sensor_id, "part_id": "part2", "data": part_cloud}, timeout=5)
            forward_status = r.status_code
            try:
                response['cloud_results'].append(r.json())
            except Exception:
                response['cloud_results'].append({"status": r.status_code})
        except Exception as e:
            response['cloud_results'].append({"error": str(e)})

        fog_latency = (time.time() - start_time) * 1000.0
        log_event(client_ip, size, sensor_id=sensor_id, decision="split+forward", part_id_forwarded="part2", forward_status=forward_status, fog_latency_ms=fog_latency)

    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

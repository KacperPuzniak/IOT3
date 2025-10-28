import os
import time
import requests

FOG = os.environ.get('FOG_URL', 'http://fog:5000/ingest')
CLIENT_ID = os.environ.get('CLIENT_ID', 'client1')
PAYLOAD_SIZE = int(os.environ.get('PAYLOAD_SIZE', '512'))


def make_payload(size):
    return 'A' * size


def send_once():
    data = make_payload(PAYLOAD_SIZE)
    payload = {"sensor_id": CLIENT_ID, "data": data}
    try:
        r = requests.post(FOG, json=payload, timeout=5)
        print('response', r.status_code, r.text[:200])
    except Exception as e:
        print('error', e)


if __name__ == '__main__':
    # send a few sample requests then exit
    for _ in range(3):
        send_once()
        time.sleep(1)

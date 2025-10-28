import os
import time
import requests

FOG = os.environ.get('FOG_URL', 'http://fog:5000/ingest')
CLIENT_ID = os.environ.get('CLIENT_ID', 'client2')
PAYLOAD_SIZE = int(os.environ.get('PAYLOAD_SIZE', '2048'))
DOS_MODE = os.environ.get('DOS_MODE', 'false').lower() in ('1','true','yes')


def make_payload(size):
    return 'B' * size


def send_once(i=0):
    data = make_payload(PAYLOAD_SIZE)
    payload = {"sensor_id": CLIENT_ID, "data": data}
    try:
        r = requests.post(FOG, json=payload, timeout=5)
        print('response', i, r.status_code)
    except Exception as e:
        print('error', e)


if __name__ == '__main__':
    if DOS_MODE:
        print('Starting DoS mode: sending many requests quickly')
        i = 0
        while i < 1000:
            send_once(i)
            i += 1
            # very small sleep to simulate heavy flood
            time.sleep(0.0005)
    else:
        for i in range(5):
            send_once(i)
            time.sleep(1)

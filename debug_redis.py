"""Listen on sensor_data for 1 message and print it, then call ML predict directly."""
import redis, json, requests

r = redis.from_url('redis://redis:6379', decode_responses=True)

# Check what's on the channel
p = r.pubsub()
p.subscribe('sensor_data')
print('Subscribed to sensor_data. Waiting 8s for a message...')

import threading, time

received = []

def listen():
    for msg in p.listen():
        if msg['type'] == 'message':
            received.append(json.loads(msg['data']))
            print('Got message:', json.dumps({k: (f"list[{len(v)}]" if isinstance(v, list) else (f"dict_keys={list(v.keys())}" if isinstance(v, dict) else v)) for k, v in received[-1].items()}))
            break

t = threading.Thread(target=listen, daemon=True)
t.start()
t.join(timeout=8)

if not received:
    print('NO MESSAGE received on sensor_data in 8s')
else:
    # Try a direct ML prediction with the same payload
    msg = received[0]
    sensors = msg.get('sensors', {})
    machine = msg.get('machine')
    print(f'\nTesting ML predict for {machine} with sensors keys: {list(sensors.keys())}')
    # call ML directly
    resp = requests.post('http://ml:5002/api/ml/predict',
        json={'machine': machine, 'sensors': sensors},
        headers={'Authorization': 'Bearer test'}, timeout=8)
    print(f'ML response: {resp.status_code} {resp.text[:300]}')

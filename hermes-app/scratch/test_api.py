import requests

session = requests.Session()
# Need to login first to get the cookie
res = session.post('http://127.0.0.1:5000/login', data={'email': 'test@example.com', 'password': 'password'})

res2 = session.get('http://127.0.0.1:5000/api/trackers')
print("Status Code:", res2.status_code)
try:
    print(res2.json())
except Exception as e:
    print("Error parsing JSON:", e)
    print(res2.text[:200])

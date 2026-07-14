import base64

with open('app.py', 'rb') as f:
    content = f.read()

encoded = base64.b64encode(content).decode('utf-8')

with open('app_base64.txt', 'w') as f:
    f.write(encoded)

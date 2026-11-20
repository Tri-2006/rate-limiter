import requests

for i in range(1, 9):
    res = requests.get("http://127.0.0.1:8000/api/data")
    print(i, res.status_code, res.json())
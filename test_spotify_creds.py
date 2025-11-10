# test_spotify_creds.py
import base64, requests, json

CLIENT_ID = "1ec4f4ffbe2141239bdc26724246459d"
CLIENT_SECRET = "a76bd1cc87bd431e9d4da934747ba248"

auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
headers = {"Authorization": f"Basic {auth}"}
r = requests.post("https://accounts.spotify.com/api/token",
                  data={"grant_type": "client_credentials"}, headers=headers, timeout=10)
print("Status:", r.status_code)
try:
    print(json.dumps(r.json(), indent=2))
except Exception:
    print(r.text)

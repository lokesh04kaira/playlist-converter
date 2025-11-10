import requests

KEY = "AIzaSyBu3gFIH9aSFZKKiWCou-1Shsfk-QR_zFM"  # 👈 yahan apna actual key daalna

url = "https://www.googleapis.com/youtube/v3/videos"
params = {
    "part": "snippet",
    "id": "Ks-_Mh1QhMc",
    "key": KEY
}

resp = requests.get(url, params=params, timeout=10)
print("Status Code:", resp.status_code)
print("Response:", resp.text[:500])

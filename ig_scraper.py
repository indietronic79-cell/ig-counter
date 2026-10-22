import requests
import json

USERNAME = "prophetpublichouse.lecce"
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

def get_followers():
    # Metodo 1: API pubblica tramite proxy di servizio social
    try:
        url = f"https://api.baskadia.com/instagram/{USERNAME}" # o servizio analogo
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if "followers" in data:
            return data["followers"]
    except Exception as e:
        print(f"Metodo 1 fallito: {e}")

    # Metodo 2: Fetch tramite un micro-service API libero (Fallback)
    try:
        url = f"https://instagram-follower-count.vercel.app/api/followers?username={USERNAME}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "followers" in data:
            return data["followers"]
    except Exception as e:
        print(f"Metodo 2 fallito: {e}")

    return None

followers = get_followers()

if followers:
    print(f"Follower trovati: {followers}")
    payload = {"username": USERNAME, "followers": int(followers)}
    
    # Aggiorna npoint.io
    res = requests.put(NPOINT_URL, json=payload)
    print(f"Stato aggiornamento npoint: {res.status_code}")
else:
    print("Impossibile recuperare i follower al momento.")
